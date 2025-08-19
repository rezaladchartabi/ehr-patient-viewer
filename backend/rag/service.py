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
            
            try:
                # Set environment variables to disable telemetry
                os.environ["ANONYMIZED_TELEMETRY"] = "false"
                # Don't set ChromaDB server env vars as they're causing parsing errors
                # These were removed to fix "error parsing env var" issues
                # os.environ["CHROMA_SERVER_HOST"] = "0.0.0.0"
                # os.environ["CHROMA_SERVER_HTTP_PORT"] = "8000"
                # os.environ["CHROMA_SERVER_CORS_ALLOW_ORIGINS"] = "*"
                
                logger.info(f"RAG: About to initialize ChromaDB client with path: {self.store_path}")
                logger.info(f"RAG: Current working directory: {os.getcwd()}")
                logger.info(f"RAG: Directory exists: {os.path.exists(self.store_path)}")
                
                # Try in-memory client first for Render free tier
                try:
                    self._client = chromadb.Client()
                    logger.info(f"RAG: ChromaDB in-memory client initialized successfully")
                except Exception as mem_error:
                    logger.warning(f"RAG: In-memory client failed, trying persistent: {mem_error}")
                    self._client = chromadb.PersistentClient(path=self.store_path)
                    logger.info(f"RAG: ChromaDB persistent client initialized successfully")
            except Exception as e:
                logger.error(f"RAG: Failed to initialize ChromaDB client: {e}")
                logger.error(f"RAG: Exception type: {type(e).__name__}")
                import traceback
                logger.error(f"RAG: Full traceback: {traceback.format_exc()}")
                self._client = None
            
            # Initialize sentence-transformers (BGE-M3 by default)
            model_name = os.getenv("RAG_EMBED_MODEL", "BAAI/bge-m3")
            try:
                from sentence_transformers import SentenceTransformer  # type: ignore
                self._model = SentenceTransformer(model_name)
                logger.info(f"RAG: SentenceTransformer model loaded: {model_name}")
            except Exception as e:
                logger.error(f"RAG: Failed to load SentenceTransformer model: {e}")
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


