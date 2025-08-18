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


