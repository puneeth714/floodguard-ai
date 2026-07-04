"""python
vision.py

FloodGuard AI - Vision Tool Module
===================================

This module implements the `VisionTool` class, responsible for analyzing
flood-related images using Google's Gemini multimodal vision model
(via the `google-genai` SDK) and converting the model's structured JSON
output into a validated `VisionResult` object.

Responsibilities of this module (and ONLY this module):
    - Validate uploaded flood images (format, size).
    - Load images safely into memory.
    - Send images + system prompt to Gemini for multimodal analysis.
    - Extract and clean JSON from the Gemini response.
    - Validate the JSON against the `VisionResult` Pydantic schema.
    - Return a fully validated `VisionResult` instance.

This module explicitly does NOT handle:
    - FastAPI routes / HTTP concerns
    - Database persistence
    - RAG / retrieval logic
    - Agent orchestration
    - Frontend concerns

Design note:
    This module is intentionally decoupled from any specific Gemini SDK
    call pattern inside a single private method (`_analyze_with_gemini`)
    so that swapping the backend (e.g., to Vertex AI's `google-cloud-aiplatform`
    SDK) in the future requires changes to only that method.
"""

from __future__ import annotations

import io
import json
import logging
import os
from pathlib import Path
from typing import Final

from google import genai
from google.genai import types as genai_types
from PIL import Image, UnidentifiedImageError
from pydantic import ValidationError

from .vision_models import VisionResult
from .vision_prompt import VISION_SYSTEM_PROMPT

from dotenv import load_dotenv
load_dotenv()  # Loads GEMINI_API_KEY (and other vars) from .env into os.environ

from pathlib import Path

# --------------------------------------------------------------------------- #
# Logging configuration
# --------------------------------------------------------------------------- #

logger = logging.getLogger("floodguard.vision")
if not logger.handlers:
    _handler = logging.StreamHandler()
    _formatter = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    _handler.setFormatter(_formatter)
    logger.addHandler(_handler)
    logger.setLevel(logging.INFO)


# --------------------------------------------------------------------------- #
# Custom Exceptions
# --------------------------------------------------------------------------- #

class VisionToolError(Exception):
    """Base exception for all VisionTool-related errors."""


class ImageValidationError(VisionToolError):
    """Raised when an image fails format, size, or integrity validation."""


class GeminiAPIError(VisionToolError):
    """Raised when the Gemini API call fails or returns an unusable response."""


class JSONExtractionError(VisionToolError):
    """Raised when JSON cannot be extracted or parsed from the model response."""


class ResultValidationError(VisionToolError):
    """Raised when extracted JSON fails validation against `VisionResult`."""


# --------------------------------------------------------------------------- #
# VisionTool
# --------------------------------------------------------------------------- #

class VisionTool:
    """
    VisionTool performs AI-powered flood image analysis using Gemini's
    multimodal vision capabilities.

    Typical usage:
        >>> tool = VisionTool()
        >>> result = tool.analyze_flood_image(str(sample_image_path))
        >>> print(result.model_dump_json(indent=2))

    Attributes:
        SUPPORTED_FORMATS: Allowed image MIME/format identifiers.
        MAX_IMAGE_SIZE_BYTES: Maximum allowed image size in bytes (10 MB).
        model_name: Gemini model identifier used for vision analysis.
    """

    SUPPORTED_FORMATS: Final[frozenset[str]] = frozenset({"PNG", "JPEG", "JPG"})
    MAX_IMAGE_SIZE_BYTES: Final[int] = 10 * 1024 * 1024  # 10 MB

    # Default Gemini model used for multimodal flood image analysis.
    DEFAULT_MODEL_NAME: Final[str] = "gemini-3.5-flash"

    # Default request timeout (seconds) for the Gemini API call.
    DEFAULT_TIMEOUT_SECONDS: Final[int] = 60

    def __init__(
        self,
        model_name: str | None = None,
        timeout_seconds: int | None = None,
    ) -> None:
        """
        Initialize the VisionTool.

        Args:
            model_name: Optional override for the Gemini model name.
                Defaults to `VisionTool.DEFAULT_MODEL_NAME`.
            timeout_seconds: Optional override for the request timeout,
                in seconds. Defaults to `VisionTool.DEFAULT_TIMEOUT_SECONDS`.

        Raises:
            GeminiAPIError: If the Gemini client cannot be initialized
                (e.g., missing API key).
        """
        self.model_name: str = model_name or self.DEFAULT_MODEL_NAME
        self.timeout_seconds: int = timeout_seconds or self.DEFAULT_TIMEOUT_SECONDS
        self._client: genai.Client = self._initialize_client()

    # ------------------------------------------------------------------- #
    # Initialization
    # ------------------------------------------------------------------- #

    def _initialize_client(self) -> genai.Client:
        """
        Initialize and return a Gemini API client using the API key
        stored in the `GEMINI_API_KEY` environment variable.

        Returns:
            genai.Client: An authenticated Gemini client instance.

        Raises:
            GeminiAPIError: If `GEMINI_API_KEY` is not set, or if the
                client fails to initialize for any reason.
        """
        api_key = os.environ.get("GEMINI_API_KEY")

        if not api_key:
            logger.error("GEMINI_API_KEY environment variable is not set.")
            raise GeminiAPIError(
                "Missing GEMINI_API_KEY environment variable. "
                "Set it before initializing VisionTool."
            )

        try:
            client = genai.Client(api_key=api_key)
        except Exception as exc:  # noqa: BLE001 - surface as domain-specific error
            logger.error("Failed to initialize Gemini client: %s", type(exc).__name__)
            raise GeminiAPIError(
                "Failed to initialize the Gemini API client."
            ) from exc

        logger.info("Gemini client initialized successfully (model=%s).", self.model_name)
        return client

    # ------------------------------------------------------------------- #
    # Image Validation
    # ------------------------------------------------------------------- #

    def _validate_image(self, image_path: Path) -> None:
        """
        Validate that the image file exists, is of a supported format,
        and does not exceed the maximum allowed size.

        Args:
            image_path: Path to the image file on disk.

        Raises:
            FileNotFoundError: If the file does not exist.
            ImageValidationError: If the file exceeds the maximum size,
                is not a supported format, or is not a valid/readable image.
        """
        if not image_path.exists():
            logger.error("Image file not found: %s", image_path)
            raise FileNotFoundError(f"Image file not found: {image_path}")

        if not image_path.is_file():
            logger.error("Provided path is not a file: %s", image_path)
            raise ImageValidationError(f"Provided path is not a file: {image_path}")

        file_size = image_path.stat().st_size
        if file_size > self.MAX_IMAGE_SIZE_BYTES:
            logger.error(
                "Image exceeds max allowed size: %s bytes (limit=%s bytes)",
                file_size,
                self.MAX_IMAGE_SIZE_BYTES,
            )
            raise ImageValidationError(
                f"Image size ({file_size} bytes) exceeds the maximum allowed "
                f"size of {self.MAX_IMAGE_SIZE_BYTES} bytes (10 MB)."
            )

        try:
            with Image.open(image_path) as img:
                img.verify()  # Verifies integrity without fully decoding.
                image_format = (img.format or "").upper()
        except (UnidentifiedImageError, OSError) as exc:
            logger.error("Image could not be identified/opened: %s", image_path)
            raise ImageValidationError(
                f"File is not a valid or readable image: {image_path}"
            ) from exc

        if image_format not in self.SUPPORTED_FORMATS:
            logger.error("Unsupported image format: %s", image_format)
            raise ImageValidationError(
                f"Unsupported image format '{image_format}'. "
                f"Supported formats: {sorted(self.SUPPORTED_FORMATS)}."
            )

        logger.info(
            "Image validated successfully: %s (format=%s, size=%s bytes)",
            image_path.name,
            image_format,
            file_size,
        )

    # ------------------------------------------------------------------- #
    # Image Loading
    # ------------------------------------------------------------------- #

    def _load_image(self, image_path: Path) -> bytes:
        """
        Load the image file from disk into memory as raw bytes.

        Args:
            image_path: Path to the previously validated image file.

        Returns:
            bytes: Raw image bytes suitable for transmission to Gemini.

        Raises:
            ImageValidationError: If the image cannot be read or
                re-encoded from disk.
        """
        try:
            with Image.open(image_path) as img:
                img.load()
                image_format = img.format or "JPEG"

                buffer = io.BytesIO()
                img.save(buffer, format=image_format)
                image_bytes = buffer.getvalue()
        except (OSError, ValueError) as exc:
            logger.error("Failed to load image into memory: %s", image_path)
            raise ImageValidationError(
                f"Failed to load image into memory: {image_path}"
            ) from exc

        logger.info("Image loaded into memory: %s (%d bytes).", image_path.name, len(image_bytes))
        return image_bytes

    @staticmethod
    def _get_mime_type(image_path: Path) -> str:
        """
        Determine the MIME type of an image based on its file extension.

        Args:
            image_path: Path to the image file.

        Returns:
            str: The corresponding MIME type (e.g., "image/jpeg").

        Raises:
            ImageValidationError: If the file extension is unsupported.
        """
        suffix = image_path.suffix.lower().lstrip(".")
        mime_map = {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
        }
        mime_type = mime_map.get(suffix)
        if mime_type is None:
            raise ImageValidationError(
                f"Cannot determine MIME type for file extension: '.{suffix}'"
            )
        return mime_type

    # ------------------------------------------------------------------- #
    # Gemini Analysis
    # ------------------------------------------------------------------- #

    def _analyze_with_gemini(self, image_bytes: bytes, mime_type: str) -> str:
        """
        Send the image and system prompt to Gemini for multimodal flood
        analysis and return the raw text response.

        This is the ONLY method that directly couples to the Gemini SDK.
        Swapping to Vertex AI in the future requires changes only here.

        Args:
            image_bytes: Raw image bytes to analyze.
            mime_type: MIME type of the image (e.g., "image/jpeg").

        Returns:
            str: Raw text response from Gemini (expected to be JSON,
                possibly wrapped in markdown code fences).

        Raises:
            GeminiAPIError: If the Gemini API call fails, times out,
                or returns an empty/unusable response.
        """
        logger.info("Gemini request started (model=%s).", self.model_name)

        try:
            response = self._client.models.generate_content(
                model=self.model_name,
                contents=[
                    VISION_SYSTEM_PROMPT,
                    genai_types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                ],
                config=genai_types.GenerateContentConfig(
                    response_mime_type="application/json",
                    http_options=genai_types.HttpOptions(
                        timeout=self.timeout_seconds * 1000  # SDK expects milliseconds
                    ),
                ),
            )
        except genai.errors.APIError as exc:
            logger.error("Gemini API error: %s", type(exc).__name__)
            raise GeminiAPIError(f"Gemini API request failed: {exc}") from exc
        except TimeoutError as exc:
            logger.error("Gemini API request timed out after %s seconds.", self.timeout_seconds)
            raise GeminiAPIError(
                f"Gemini API request timed out after {self.timeout_seconds} seconds."
            ) from exc
        except Exception as exc:  # noqa: BLE001 - convert to domain-specific error
            logger.error("Unexpected error during Gemini request: %s", type(exc).__name__)
            raise GeminiAPIError(
                "Unexpected error occurred while calling the Gemini API."
            ) from exc

        response_text = getattr(response, "text", None)
        if not response_text or not response_text.strip():
            logger.error("Gemini returned an empty response.")
            raise GeminiAPIError("Gemini API returned an empty or unusable response.")

        logger.info("Gemini response received (%d characters).", len(response_text))
        return response_text

    # ------------------------------------------------------------------- #
    # JSON Extraction
    # ------------------------------------------------------------------- #

    def _extract_json(self, raw_text: str) -> dict:
        """
        Extract and parse JSON content from Gemini's raw text response.

        Handles cases where Gemini wraps JSON in markdown code fences
        (e.g., ```json ... ``` or ``` ... ```).

        Args:
            raw_text: The raw text response returned by Gemini.

        Returns:
            dict: The parsed JSON object.

        Raises:
            JSONExtractionError: If no valid JSON object can be parsed
                from the response.
        """
        cleaned_text = raw_text.strip()

        if cleaned_text.startswith("```"):
            lines = cleaned_text.splitlines()
            # Drop the opening fence line (``` or ```json)
            if lines and lines[0].startswith("```"):
                lines = lines[1:]
            # Drop the closing fence line, if present
            if lines and lines[-1].strip().startswith("```"):
                lines = lines[:-1]
            cleaned_text = "\n".join(lines).strip()

        try:
            parsed_json = json.loads(cleaned_text)
        except json.JSONDecodeError as exc:
            logger.error("Failed to parse JSON from Gemini response.")
            raise JSONExtractionError(
                "Failed to parse JSON from Gemini response. "
                f"Reason: {exc.msg} (line {exc.lineno}, column {exc.colno})."
            ) from exc

        if not isinstance(parsed_json, dict):
            logger.error("Parsed JSON is not an object: %s", type(parsed_json).__name__)
            raise JSONExtractionError(
                "Parsed JSON response is not a JSON object as expected."
            )

        return parsed_json

    # ------------------------------------------------------------------- #
    # Result Validation
    # ------------------------------------------------------------------- #

    def _validate_result(self, parsed_json: dict) -> VisionResult:
        """
        Validate the parsed JSON dictionary against the `VisionResult`
        Pydantic schema.

        Args:
            parsed_json: Dictionary parsed from Gemini's JSON response.

        Returns:
            VisionResult: A fully validated result object.

        Raises:
            ResultValidationError: If the JSON fails schema validation.
        """
        try:
            result = VisionResult.model_validate(parsed_json)
        except ValidationError as exc:
            logger.error("VisionResult validation failed: %s", exc.error_count())
            raise ResultValidationError(
                f"Gemini response failed VisionResult validation: {exc}"
            ) from exc

        logger.info("VisionResult validation successful.")
        return result

    # ------------------------------------------------------------------- #
    # Public API
    # ------------------------------------------------------------------- #

    def analyze_flood_image(self, image_path: str) -> VisionResult:
        """
        Analyze a flood image end-to-end and return a validated
        `VisionResult`.

        Pipeline:
            1. Validate the image (format, size, integrity).
            2. Load the image into memory.
            3. Send the image to Gemini for multimodal analysis.
            4. Extract JSON from Gemini's response.
            5. Validate the JSON against the `VisionResult` schema.

        Args:
            image_path: Path (as a string) to the flood image file.

        Returns:
            VisionResult: A validated flood assessment result.

        Raises:
            FileNotFoundError: If the image file does not exist.
            ImageValidationError: If the image fails validation.
            GeminiAPIError: If the Gemini API call fails.
            JSONExtractionError: If JSON cannot be extracted from the response.
            ResultValidationError: If the extracted JSON fails schema validation.
        """
        path = Path(image_path)

        self._validate_image(path)
        mime_type = self._get_mime_type(path)
        image_bytes = self._load_image(path)

        raw_response = self._analyze_with_gemini(image_bytes, mime_type)
        parsed_json = self._extract_json(raw_response)
        result = self._validate_result(parsed_json)

        logger.info("Flood image analysis completed successfully: %s", path.name)
        return result


# --------------------------------------------------------------------------- #
# Local Test Entry Point
# --------------------------------------------------------------------------- #

if __name__ == "__main__":
    BASE_DIR = Path(__file__).parent
    sample_image_path = BASE_DIR / "sample_image.png"

    try:
        vision_tool = VisionTool()
        flood_result = vision_tool.analyze_flood_image(sample_image_path)
        print(flood_result.model_dump_json(indent=2))
    except VisionToolError as tool_error:
        logger.error("VisionTool failed: %s", tool_error)
    except FileNotFoundError as file_error:
        logger.error("File error: %s", file_error)
