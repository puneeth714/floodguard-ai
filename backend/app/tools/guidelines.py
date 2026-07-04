from typing import List, Dict, Any, Optional
import os
from google.adk.tools.tool_context import ToolContext
from google import genai
from app.db.bigquery_client import BigQueryClientWrapper
from app.core.config import settings

def search_disaster_guidelines(query_text: str, tool_context: Optional[ToolContext] = None) -> List[Dict[str, Any]]:
    """
    Performs vector search in BigQuery guidelines_vector table for disaster response guidelines
    based on the user's query embedding generated via Vertex AI.
    
    Args:
        query_text: User's textual search query.
        tool_context: Optional ADK ToolContext to store retrieved records in state.
        
    Returns:
        List of matching guideline document snippets.
    """
    project_id = settings.PROJECT_ID
    
    # 1. Initialize Google GenAI client to generate query embedding using Vertex AI
    client = genai.Client(vertexai=True, project=project_id, location="us-central1")
    emb_response = client.models.embed_content(
        model=settings.EMBEDDING_MODEL,
        contents=query_text
    )
    query_embedding = emb_response.embeddings[0].values
    
    # 2. Query BigQuery guidelines_vector table using VECTOR_SEARCH
    bq_wrapper = BigQueryClientWrapper()
    results = bq_wrapper.vector_search(query_embedding, top_k=3)
    
    # 3. Save to ADK tool context if present
    if tool_context is not None:
        tool_context.state["policy_documents"] = results
        
    return results
