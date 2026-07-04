import os
from dotenv import load_dotenv

# Ensure environment variables are loaded from the base .env file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
load_dotenv(os.path.join(BASE_DIR, ".env"))

class Settings:
    # Mode Settings
    ENVIRONMENT_MODE: str = os.getenv("ENVIRONMENT_MODE", "test")
    DEFAULT_DEMO_PROFILE: str = os.getenv("DEFAULT_DEMO_PROFILE", "rajesh")

    # LLM configurations
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
    EMBEDDING_MODEL: str = os.getenv("EMBEDDING_MODEL", "text-embedding-004")
    
    # GCP & BigQuery strategy
    PROJECT_ID: str = os.getenv("PROJECT_ID", "floodguardai-501409")
    BQ_DATASET: str = os.getenv("BQ_DATASET", "floodguard")
    BQ_GUIDELINES_TABLE: str = os.getenv("BQ_GUIDELINES_TABLE", "guidelines_vector")
    BQ_GRID_VULNERABILITY_TABLE: str = os.getenv("BQ_GRID_VULNERABILITY_TABLE", "grid_vulnerability")


    # Mocks & Telemetry
    USE_MOCK_TELEMETRY: bool = os.getenv("USE_MOCK_TELEMETRY", "False").lower() in ("true", "1", "yes")
    MOCK_WEATHER_PRECIPITATION: float = float(os.getenv("MOCK_WEATHER_PRECIPITATION", "45.0"))
    MOCK_ELEVATION_ALTITUDE: float = float(os.getenv("MOCK_ELEVATION_ALTITUDE", "858.0"))

settings = Settings()
