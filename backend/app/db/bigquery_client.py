import os
from typing import List, Dict, Any, Optional
from google.cloud import bigquery
from google.oauth2 import service_account

# Determine key path relative to this file
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DEFAULT_KEY_PATH = os.path.join(BASE_DIR, "floodguard-sa-key.json")

class BigQueryClientWrapper:
    def __init__(self, key_path: str = DEFAULT_KEY_PATH):
        self.project_id = "floodguardai-501409"
        self.dataset_id = "floodguard_db"
        self.dataset_ref = f"{self.project_id}.{self.dataset_id}"
        
        # Load credentials
        if os.path.exists(key_path):
            self.credentials = service_account.Credentials.from_service_account_file(key_path)
            self.client = bigquery.Client(credentials=self.credentials, project=self.project_id)
            print(f"BigQuery client initialized successfully from service account: {key_path}")
        else:
            # Fallback to default application credentials
            self.client = bigquery.Client(project=self.project_id)
            print("BigQuery client initialized using default application credentials.")

    def execute_query(self, query: str, job_config: Optional[bigquery.QueryJobConfig] = None) -> List[Dict[str, Any]]:
        """Executes a SQL query and returns list of dictionaries (one per row)."""
        query_job = self.client.query(query, job_config=job_config)
        results = query_job.result()
        return [dict(row) for row in results]

    def insert_rows(self, table_name: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Inserts multiple rows into a BigQuery table using streaming API."""
        table_ref = f"{self.dataset_ref}.{table_name}"
        errors = self.client.insert_rows_json(table_ref, rows)
        if errors:
            raise Exception(f"Failed to insert rows into {table_name}: {errors}")
        return errors

    def init_tables(self):
        """Creates the database tables if they do not already exist."""
        # 1. vulnerability_grids
        grids_schema = [
            bigquery.SchemaField("lat", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("lng", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("altitude", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("slope", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("drainage_capacity", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("fvi", "FLOAT", mode="NULLABLE"),
        ]
        self._create_table_if_not_exists("vulnerability_grids", grids_schema)

        # 2. drainage_network
        drainage_schema = [
            bigquery.SchemaField("drain_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("lat", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("lng", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # 'blocked', 'cleared'
        ]
        self._create_table_if_not_exists("drainage_network", drainage_schema)

        # 3. active_sos
        sos_schema = [
            bigquery.SchemaField("session_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("lat", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("lng", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("detected_depth", "FLOAT", mode="NULLABLE"),
            bigquery.SchemaField("photo_url", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("status", "STRING", mode="REQUIRED"),  # 'pending', 'rescued'
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
        ]
        self._create_table_if_not_exists("active_sos", sos_schema)

        # 4. guidelines_vector
        vector_schema = [
            bigquery.SchemaField("chunk_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("doc_name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("page_num", "INTEGER", mode="REQUIRED"),
            bigquery.SchemaField("section_title", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("category", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("content", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("embedding", "FLOAT", mode="REPEATED"),  # Array of floats
        ]
        self._create_table_if_not_exists("guidelines_vector", vector_schema)

        # 5. low_lying_hotspots
        hotspots_schema = [
            bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("lat", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("lng", "FLOAT", mode="REQUIRED"),
            bigquery.SchemaField("object_id", "INTEGER", mode="REQUIRED"),
        ]
        self._create_table_if_not_exists("low_lying_hotspots", hotspots_schema)

    def _create_table_if_not_exists(self, table_name: str, schema: List[bigquery.SchemaField]):
        table_ref = f"{self.dataset_ref}.{table_name}"
        try:
            self.client.get_table(table_ref)
            print(f"Table {table_name} already exists.")
        except Exception:
            # Table does not exist, create it
            table = bigquery.Table(table_ref, schema=schema)
            self.client.create_table(table)
            print(f"Table {table_name} created successfully.")
            
            # If creating guidelines_vector, create a vector index (optional, brute force is fine for hackathon, but index is standard)
            if table_name == "guidelines_vector":
                try:
                    self._create_vector_index()
                except Exception as e:
                    print(f"Vector index creation warning (can run brute force instead): {e}")

    def _create_vector_index(self):
        """Creates a vector index on the embedding column of guidelines_vector."""
        query = f"""
        CREATE OR REPLACE VECTOR INDEX guidelines_embedding_index
        ON `{self.dataset_ref}.guidelines_vector`(embedding)
        OPTIONS(distance_type='COSINE', index_type='IVF')
        """
        self.client.query(query).result()
        print("Vector index guidelines_embedding_index created successfully.")

    def vector_search(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """Queries guidelines_vector using BigQuery Vector Search."""
        embedding_str = ",".join(map(str, query_embedding))
        query = f"""
        SELECT base.chunk_id AS chunk_id, base.doc_name AS doc_name, base.page_num AS page_num, base.content AS content
        FROM VECTOR_SEARCH(
          TABLE `{self.dataset_ref}.guidelines_vector`,
          'embedding',
          (SELECT [{embedding_str}] AS embedding),
          top_k => {top_k}
        )
        """
        return self.execute_query(query)
