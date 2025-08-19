from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional

from .service import RagService

router = APIRouter(prefix="/rag", tags=["rag"])
service = RagService()

class Doc(BaseModel):
    id: str
    text: str
    metadata: Dict[str, Any] = {}

class IndexRequest(BaseModel):
    documents: List[Doc]
    collection: Optional[str] = "patient"

class SearchRequest(BaseModel):
    query: str
    topK: Optional[int] = None
    collection: Optional[str] = "patient"
    filters: Optional[Dict[str, Any]] = None

class PatientSearchRequest(BaseModel):
    query: str
    patientIdentifier: str
    topK: Optional[int] = None
    filters: Optional[Dict[str, Any]] = None

@router.get("/health")
def rag_health():
    return service.health()

@router.get("/test")
def rag_test():
    """Test endpoint to debug ChromaDB initialization"""
    try:
        import chromadb
        result = {
            "chromadb_imported": True,
            "chromadb_version": chromadb.__version__,
            "service_enabled": service.enabled,
            "client_exists": service._client is not None,
            "store_path": service.store_path,
            "collections": list(service._collections.keys())
        }
        
        # Try to create a test collection
        if service._client:
            try:
                test_collection = service._client.create_collection(name="test_collection")
                result["test_collection_created"] = True
                # Clean up
                service._client.delete_collection(name="test_collection")
                result["test_collection_cleaned"] = True
            except Exception as e:
                result["test_collection_error"] = str(e)
        else:
            result["test_collection_created"] = False
            result["test_collection_error"] = "No client available"
            
    except Exception as e:
        result = {
            "chromadb_imported": False,
            "error": str(e),
            "error_type": type(e).__name__
        }
    
    return result

@router.post("/index")
def rag_index(req: IndexRequest):
    return service.index_documents([d.dict() for d in req.documents], collection=req.collection or "patient")

@router.post("/search")
def rag_search(req: SearchRequest):
    return service.search(req.query, top_k=req.topK, collection=req.collection or "patient", filters=req.filters)

@router.post("/patient/search")
def rag_patient_search(req: PatientSearchRequest):
    filters = req.filters.copy() if req.filters else {}
    filters["patient_identifier"] = req.patientIdentifier
    return service.search(req.query, top_k=req.topK, collection="patient", filters=filters)


