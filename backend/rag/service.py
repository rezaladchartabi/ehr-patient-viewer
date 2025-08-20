import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

try:
    import chromadb  # type: ignore
    logger.info(f"RAG: ChromaDB imported successfully, version: {chromadb.__version__}")
except Exception as e:  # pragma: no cover
    logger.error(f"RAG: Failed to import ChromaDB: {e}")
    chromadb = None

_DEFAULT_STORE = os.getenv("RAG_STORE_PATH", "backend/.chroma-rag")
_DEFAULT_TOPK = int(os.getenv("RAG_TOP_K", "8"))

class RagService:
    def __init__(self, store_path: str = _DEFAULT_STORE):
        self.enabled = os.getenv("RAG_ENABLED", "false").lower() == "true"
        self.store_path = store_path
        self._client = None
        self._collections: Dict[str, Any] = {}
        self._model = None

        if self.enabled and chromadb is not None:
            logger.info(f"RAG: Initializing with store_path={self.store_path}")
            # Ensure store directory exists
            try:
                os.makedirs(self.store_path, exist_ok=True)
                logger.info(f"RAG: Created/verified store directory: {self.store_path}")
            except Exception as e:
                logger.error(f"RAG: Failed to create store directory: {e}")
                pass
            
            # Set environment variables to disable telemetry and configure ChromaDB
            os.environ["ANONYMIZED_TELEMETRY"] = "false"
            os.environ["CHROMA_SERVER_HOST"] = "0.0.0.0"
            os.environ["CHROMA_SERVER_HTTP_PORT"] = "8000"
            os.environ["CHROMA_SERVER_CORS_ALLOW_ORIGINS"] = '["*"]'  # JSON array format
            
            # Reduce memory/threads to fit small instances
            os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
            os.environ.setdefault("OMP_NUM_THREADS", "1")
            os.environ.setdefault("MKL_NUM_THREADS", "1")
            
            logger.info(f"RAG: About to initialize ChromaDB client with path: {self.store_path}")
            logger.info(f"RAG: Current working directory: {os.getcwd()}")
            logger.info(f"RAG: Directory exists: {os.path.exists(self.store_path)}")
            
            try:
                # Initialize ChromaDB client
                self._client = chromadb.Client()
                logger.info(f"RAG: ChromaDB client initialized successfully")
                
                # Initialize sentence-transformers (configurable; allow disabling to avoid OOM)
                model_name = os.getenv("RAG_EMBED_MODEL", "disabled")
                if model_name.lower() in ("disabled", "none", "off", "false"):
                    logger.info("RAG: Embedding model disabled via RAG_EMBED_MODEL")
                    self._model = None
                else:
                    from sentence_transformers import SentenceTransformer  # type: ignore
                    self._model = SentenceTransformer(model_name)
                    logger.info(f"RAG: SentenceTransformer model loaded: {model_name}")
            except Exception as e:
                logger.error(f"RAG: Failed to initialize RAG service: {e}")
                logger.error(f"RAG: Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"RAG: Full traceback: {traceback.format_exc()}")
                self._client = None
                self._model = None

    def _get_collection(self, name: str):
        if not self._client:
            return None
        if name not in self._collections:
            self._collections[name] = self._client.get_or_create_collection(
                name=name, metadata={"hnsw:space": "cosine"}
            )
        return self._collections[name]

    def health(self) -> Dict[str, Any]:
        # Try to initialize client if not already done
        if self.enabled and self._client is None and chromadb is not None:
            try:
                logger.info("RAG: Attempting to initialize client in health check")
                self._client = chromadb.Client()
                logger.info("RAG: Client initialized successfully in health check")
            except Exception as e:
                logger.error(f"RAG: Failed to initialize client in health check: {e}")
        
        return {
            "enabled": self.enabled,
            "store_path": self.store_path,
            "collections": list(self._collections.keys()),
            "client": bool(self._client) if self.enabled else False,
            "chromadb_available": chromadb is not None,
        }

    def index_documents(self, documents: List[Dict[str, Any]], collection: str = "patient") -> Dict[str, Any]:
        if not self.enabled:
            return {"status": "disabled"}
        col = self._get_collection(collection)
        if col is None:
            return {"status": "error", "message": "Chroma not available"}

        def _primitive(v):
            return isinstance(v, (str, int, float, bool)) or v is None

        def _sanitize(meta: Dict[str, Any]) -> Dict[str, Any]:
            out = {}
            for k, v in (meta or {}).items():
                # Drop nested/large objects like note_metadata
                if k == "note_metadata":
                    continue
                if _primitive(v):
                    out[k] = v
                else:
                    try:
                        out[k] = str(v)
                    except Exception:
                        pass
            return out

        ids = [d["id"] for d in documents]
        texts = [d["text"] for d in documents]
        metadatas = [_sanitize(d.get("metadata", {})) for d in documents]
        embeddings = None
        if self._model is not None:
            passages = [f"passage: {t}" for t in texts]
            vecs = self._model.encode(passages, normalize_embeddings=True)
            embeddings = [v.tolist() for v in vecs]
        if embeddings is not None:
            col.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)
        else:
            col.add(ids=ids, documents=texts, metadatas=metadatas)
        return {"status": "ok", "count": len(ids)}

    def search(self, query: str, top_k: Optional[int] = None, collection: str = "patient", filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not self.enabled:
            return {"hits": []}
        col = self._get_collection(collection)
        if col is None:
            return {"hits": []}
        k = top_k or _DEFAULT_TOPK
        if self._model is not None:
            qv = self._model.encode([f"query: {query}"], normalize_embeddings=True)
            if filters:
                res = col.query(query_embeddings=qv.tolist(), n_results=k, where=filters)
            else:
                res = col.query(query_embeddings=qv.tolist(), n_results=k)
        else:
            if filters:
                res = col.query(query_texts=[query], n_results=k, where=filters)
            else:
                res = col.query(query_texts=[query], n_results=k)
        # Normalize output
        hits = []
        for i in range(len(res.get("ids", [[]])[0])):
            hits.append({
                "id": res["ids"][0][i],
                "text": res["documents"][0][i],
                "metadata": res.get("metadatas", [[{}]])[0][i],
                "score": res.get("distances", [[None]])[0][i],
            })
        return {"hits": hits}

    def get_all_notes(self, collection: str = "patient", limit: Optional[int] = None) -> Dict[str, Any]:
        """Get all notes from the collection, ordered by recency"""
        if not self.enabled:
            return {"notes": []}
        col = self._get_collection(collection)
        if col is None:
            return {"notes": []}
        
        try:
            # Get all documents from the collection
            # Note: ChromaDB doesn't have built-in ordering, so we'll get all and sort in Python
            all_results = col.get()
            
            if not all_results.get("ids"):
                return {"notes": []}
            
            # Combine all data
            notes = []
            for i in range(len(all_results["ids"])):
                note = {
                    "id": all_results["ids"][i],
                    "text": all_results["documents"][i],
                    "metadata": all_results.get("metadatas", [{}])[i] if all_results.get("metadatas") else {},
                }
                notes.append(note)
            
            # Sort by chart_time (most recent first)
            def sort_key(note):
                metadata = note.get("metadata", {})
                chart_time = metadata.get("chart_time", "")
                # Convert chart_time to sortable format (assuming format like "101429")
                try:
                    return int(chart_time) if chart_time.isdigit() else 0
                except (ValueError, TypeError):
                    return 0
            
            notes.sort(key=sort_key, reverse=True)
            
            # Apply limit if specified
            if limit:
                notes = notes[:limit]
            
            return {"notes": notes, "total_count": len(notes)}
            
        except Exception as e:
            logger.error(f"RAG: Failed to get all notes: {e}")
            return {"notes": [], "error": str(e)}

    def get_notes_by_patient(self, collection: str = "patient", patient_id: str = None, limit: Optional[int] = None) -> Dict[str, Any]:
        """Get notes for a specific patient, ordered by recency"""
        if not self.enabled:
            return {"notes": []}
        col = self._get_collection(collection)
        if col is None:
            return {"notes": []}
        
        try:
            # Use ChromaDB's built-in filtering for better performance
            where_filter = {"patient_identifier": patient_id}
            all_results = col.get(where=where_filter)
            
            if not all_results.get("ids"):
                return {"notes": [], "total_count": 0, "patient_id": patient_id}
            
            # Combine all data
            patient_notes = []
            for i in range(len(all_results["ids"])):
                note = {
                    "id": all_results["ids"][i],
                    "text": all_results["documents"][i],
                    "metadata": all_results.get("metadatas", [{}])[i] if all_results.get("metadatas") else {},
                }
                patient_notes.append(note)
            
            # Sort by chart_time (most recent first)
            def sort_key(note):
                metadata = note.get("metadata", {})
                chart_time = metadata.get("chart_time", "")
                try:
                    return int(chart_time) if chart_time.isdigit() else 0
                except (ValueError, TypeError):
                    return 0
            
            patient_notes.sort(key=sort_key, reverse=True)
            
            # Apply limit if specified
            if limit:
                patient_notes = patient_notes[:limit]
            
            return {"notes": patient_notes, "total_count": len(patient_notes), "patient_id": patient_id}
            
        except Exception as e:
            logger.error(f"RAG: Failed to get notes for patient {patient_id}: {e}")
            return {"notes": [], "error": str(e)}


