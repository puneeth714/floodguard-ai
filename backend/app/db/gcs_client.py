import os
from typing import Optional
from google.cloud import storage
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), ".env"))

class GCSClientWrapper:
    """
    Wrapper for Google Cloud Storage interactions. Handles uploading user-uploaded flood images
    and cached Places API photos, and generating retrieval URLs.
    """
    def __init__(self):
        self.project_id = os.getenv("PROJECT_ID", "floodguardai-501409")
        # Initialize storage client (automatically loads credentials from GOOGLE_APPLICATION_CREDENTIALS absolute path)
        try:
            self.client = storage.Client(project=self.project_id)
            # Standard naming mapping
            self.bucket_name = f"floodguard-assets-{self.project_id.split('-')[-1]}"
            print(f"GCS Client initialized. Default Bucket target: {self.bucket_name}")
        except Exception as e:
            print(f"Warning: Failed to initialize Google Cloud Storage Client: {e}")
            self.client = None
            self.bucket_name = "floodguard-assets-501409"

    def upload_file_bytes(
        self, 
        file_bytes: bytes, 
        destination_blob_name: str, 
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        Uploads raw file bytes directly to a GCS blob and returns its public URL.
        Falls back to local file storage simulation if client is not configured or in sandbox.
        
        Args:
            file_bytes: Raw binary bytes of the file.
            destination_blob_name: Target path in bucket (e.g. 'user-sos-uploads/session_123.jpg').
            content_type: MIME type of the uploaded file.
            
        Returns:
            The public URL of the uploaded asset, or None if upload fails.
        """
        if not self.client:
            print("GCS Client not active. Simulating local fallback file upload.")
            # Simulating local filesystem fallback
            fallback_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "tmp", "gcs_sim")
            os.makedirs(fallback_dir, exist_ok=True)
            local_path = os.path.join(fallback_dir, destination_blob_name.replace("/", "_"))
            with open(local_path, "wb") as f:
                f.write(file_bytes)
            return f"file://{local_path}"

        try:
            # Get or create bucket
            try:
                bucket = self.client.get_bucket(self.bucket_name)
            except Exception:
                # If bucket doesn't exist, create it in asia-south1
                print(f"Bucket {self.bucket_name} not found. Creating bucket in asia-south1...")
                bucket = self.client.create_bucket(self.bucket_name, location="asia-south1")

            blob = bucket.blob(destination_blob_name)
            blob.upload_from_string(file_bytes, content_type=content_type)
            
            # Generate the standard public URL
            # Note: Requires the bucket to have public reading permission (Storage Object Viewer for allUsers)
            public_url = f"https://storage.googleapis.com/{self.bucket_name}/{destination_blob_name}"
            print(f"Successfully uploaded blob to GCS: {public_url}")
            return public_url
            
        except Exception as e:
            print(f"Failed to upload asset to GCS: {e}")
            return None
