#!/usr/bin/env python3
"""
Lightweight Notes Processor
Provides direct full-text search for clinical notes using SQLite FTS5
"""

import sqlite3
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import os
import httpx
import asyncio

logger = logging.getLogger(__name__)

class NotesProcessor:
    def __init__(self, db_path: str = "notes_index.db", fhir_base_url: str = None):
        self.db_path = db_path
        self.fhir_base_url = fhir_base_url or "https://fdfbc9a33dc5.ngrok-free.app/fhir"
        self._init_db()
    
    def _init_db(self):
        """Create SQLite database with FTS5 for full-text search"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # Main notes table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS notes (
                id INTEGER PRIMARY KEY,
                patient_id TEXT NOT NULL,
                note_id TEXT UNIQUE NOT NULL,
                content TEXT NOT NULL,
                note_type TEXT,
                timestamp TEXT,
                store_time TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Migration: add store_time column if missing
        try:
            cur.execute("PRAGMA table_info(notes)")
            cols = [r[1] for r in cur.fetchall()]
            if 'store_time' not in cols:
                cur.execute("ALTER TABLE notes ADD COLUMN store_time TEXT")
        except Exception:
            pass
        
        # Create index for faster lookups
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_patient_id 
            ON notes(patient_id)
        """)
        
        cur.execute("""
            CREATE INDEX IF NOT EXISTS idx_notes_timestamp 
            ON notes(timestamp)
        """)
        
        # Full-text search index
        cur.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
                content,
                patient_id,
                note_type,
                content='notes',
                content_rowid='id'
            )
        """)
        
        conn.commit()
        conn.close()
        logger.info(f"Notes database initialized: {self.db_path}")
    
    async def fetch_notes_from_fhir(self, patient_id: str = None, limit: int = 100) -> List[Dict]:
        """Fetch clinical notes from FHIR DocumentReference resources"""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Build FHIR query
                if patient_id:
                    url = f"{self.fhir_base_url}/DocumentReference"
                    params = {
                        "patient": patient_id,
                        "type": "clinical-note",
                        "_count": limit
                    }
                else:
                    url = f"{self.fhir_base_url}/DocumentReference"
                    params = {
                        "type": "clinical-note",
                        "_count": limit
                    }
                
                logger.info(f"Fetching notes from FHIR: {url}")
                response = await client.get(url, params=params)
                response.raise_for_status()
                
                data = response.json()
                notes = []
                
                if data.get("resourceType") == "Bundle" and data.get("entry"):
                    for entry in data["entry"]:
                        resource = entry.get("resource", {})
                        if resource.get("resourceType") == "DocumentReference":
                            note = self._parse_document_reference(resource)
                            if note:
                                notes.append(note)
                
                logger.info(f"Fetched {len(notes)} notes from FHIR")
                return notes
                
        except Exception as e:
            logger.error(f"Error fetching notes from FHIR: {e}")
            return []
    
    def _parse_document_reference(self, doc_ref: Dict) -> Optional[Dict]:
        """Parse FHIR DocumentReference into note format"""
        try:
            # Extract basic information
            note_id = doc_ref.get("id", "")
            patient_ref = doc_ref.get("subject", {}).get("reference", "")
            patient_id = patient_ref.replace("Patient/", "") if patient_ref.startswith("Patient/") else patient_ref
            
            # Extract content
            content = ""
            if doc_ref.get("content"):
                for content_item in doc_ref["content"]:
                    attachment = content_item.get("attachment", {})
                    if attachment.get("data"):
                        # Handle base64 encoded content
                        import base64
                        try:
                            content = base64.b64decode(attachment["data"]).decode('utf-8')
                            break
                        except:
                            pass
                    elif attachment.get("url"):
                        # Handle URL-based content (would need additional fetch)
                        content = f"[Content available at: {attachment['url']}]"
                        break
            
            # Extract note type
            note_type = "clinical-note"
            if doc_ref.get("type", {}).get("coding"):
                for coding in doc_ref["type"]["coding"]:
                    if coding.get("code"):
                        note_type = coding["code"]
                        break
            
            # Extract timestamp
            timestamp = doc_ref.get("date", "")
            
            if not content or not patient_id:
                logger.warning(f"Skipping DocumentReference {note_id}: missing content or patient_id")
                return None
            
            return {
                "patient_id": patient_id,
                "note_id": note_id,
                "content": content,
                "note_type": note_type,
                "timestamp": timestamp
            }
            
        except Exception as e:
            logger.error(f"Error parsing DocumentReference: {e}")
            return None
    
    async def index_notes_from_fhir(self, patient_id: str = None, limit: int = 100) -> Dict[str, Any]:
        """Index notes from FHIR DocumentReference resources"""
        try:
            logger.info(f"Starting FHIR notes indexing for {'all patients' if patient_id is None else f'patient {patient_id}'}")
            
            # Fetch notes from FHIR
            notes = await self.fetch_notes_from_fhir(patient_id, limit)
            
            if not notes:
                return {
                    "message": "No notes found in FHIR",
                    "indexed": 0,
                    "errors": 0
                }
            
            # Index the notes
            result = self.index_notes_batch(notes)
            
            logger.info(f"FHIR notes indexing completed: {result['success']} indexed, {result['errors']} errors")
            
            return {
                "message": "FHIR notes indexing completed",
                "fetched": len(notes),
                "indexed": result["success"],
                "errors": result["errors"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error indexing notes from FHIR: {e}")
            return {
                "message": f"Error indexing notes from FHIR: {str(e)}",
                "fetched": 0,
                "indexed": 0,
                "errors": 1
            }
    
    def index_note(self, patient_id: str, note_id: str, content: str, 
                   note_type: str = None, timestamp: str = None, store_time: str = None) -> bool:
        """Index a single note"""
        if not content or not content.strip():
            logger.warning(f"Skipping empty note: {note_id}")
            return False
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            # Insert into main table
            cur.execute("""
                INSERT OR REPLACE INTO notes 
                (patient_id, note_id, content, note_type, timestamp, store_time)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (patient_id, note_id, content, note_type, timestamp, store_time))
            
            # FTS5 automatically updates the virtual table
            conn.commit()
            logger.debug(f"Indexed note: {note_id} for patient: {patient_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error indexing note {note_id}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def index_notes_batch(self, notes: List[Dict]) -> Dict[str, int]:
        """Index multiple notes in a batch"""
        success_count = 0
        error_count = 0
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            for note in notes:
                try:
                    patient_id = note.get('patient_id')
                    note_id = note.get('note_id')
                    content = note.get('content', '')
                    note_type = note.get('note_type')
                    timestamp = note.get('timestamp')
                    
                    if not all([patient_id, note_id, content]):
                        logger.warning(f"Skipping incomplete note: {note_id}")
                        error_count += 1
                        continue
                    
                    store_time = note.get('store_time')
                    cur.execute("""
                        INSERT OR REPLACE INTO notes 
                        (patient_id, note_id, content, note_type, timestamp, store_time)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (patient_id, note_id, content, note_type, timestamp, store_time))
                    
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Error indexing note {note.get('note_id', 'unknown')}: {e}")
                    error_count += 1
            
            conn.commit()
            logger.info(f"Batch indexing completed: {success_count} success, {error_count} errors")
            
        except Exception as e:
            logger.error(f"Batch indexing failed: {e}")
            conn.rollback()
        finally:
            conn.close()
        
        return {"success": success_count, "errors": error_count}
    
    def search_notes(self, query: str, patient_id: str = None, 
                    note_type: str = None, limit: int = 50, 
                    offset: int = 0) -> List[Dict]:
        """Search notes using SQLite FTS5"""
        if not query or not query.strip():
            # If no query, just return all notes with filters
            return self.get_patient_notes(patient_id, limit, offset) if patient_id else []
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            # Try FTS5 search first
            if patient_id:
                # Search with patient filter
                sql = """
                    SELECT n.*, rank 
                    FROM notes n
                    JOIN notes_fts fts ON n.id = fts.rowid
                    WHERE notes_fts MATCH ? AND n.patient_id = ?
                    ORDER BY rank, n.timestamp DESC
                    LIMIT ? OFFSET ?
                """
                cur.execute(sql, [query, patient_id, limit, offset])
            elif note_type:
                # Search with note type filter
                sql = """
                    SELECT n.*, rank 
                    FROM notes n
                    JOIN notes_fts fts ON n.id = fts.rowid
                    WHERE notes_fts MATCH ? AND n.note_type = ?
                    ORDER BY rank, n.timestamp DESC
                    LIMIT ? OFFSET ?
                """
                cur.execute(sql, [query, note_type, limit, offset])
            else:
                # Simple search
                sql = """
                    SELECT n.*, rank 
                    FROM notes n
                    JOIN notes_fts fts ON n.id = fts.rowid
                    WHERE notes_fts MATCH ?
                    ORDER BY rank, n.timestamp DESC
                    LIMIT ? OFFSET ?
                """
                cur.execute(sql, [query, limit, offset])
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'patient_id': row[1],
                    'note_id': row[2],
                    'content': row[3],
                    'note_type': row[4],
                    'timestamp': row[5],
                    'created_at': row[6],
                    'relevance_score': row[7] if len(row) > 7 else 0
                })
            
            # If FTS5 search returns no results, try fallback
            if not results:
                logger.debug(f"FTS5 search returned no results for '{query}', trying fallback")
                return self._fallback_text_search(query, patient_id, note_type, limit, offset)
            
            return results
            
        except Exception as e:
            logger.error(f"FTS5 search error: {e}")
            # Fallback to simple text search
            return self._fallback_text_search(query, patient_id, note_type, limit, offset)
        finally:
            conn.close()
    
    def _fallback_text_search(self, query: str, patient_id: str = None, 
                             note_type: str = None, limit: int = 50, 
                             offset: int = 0) -> List[Dict]:
        """Fallback text search using LIKE operator"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            conditions = ["content LIKE ?"]
            params = [f"%{query}%"]
            
            if patient_id:
                conditions.append("patient_id = ?")
                params.append(patient_id)
            
            if note_type:
                conditions.append("note_type = ?")
                params.append(note_type)
            
            where_clause = " AND ".join(conditions)
            
            sql = f"""
                SELECT * FROM notes 
                WHERE {where_clause}
                ORDER BY timestamp DESC, created_at DESC
                LIMIT ? OFFSET ?
            """
            
            params.extend([limit, offset])
            cur.execute(sql, params)
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'patient_id': row[1],
                    'note_id': row[2],
                    'content': row[3],
                    'note_type': row[4],
                    'timestamp': row[5],
                    'created_at': row[6],
                    'relevance_score': 1.0  # Default relevance for fallback
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback search error: {e}")
            return []
        finally:
            conn.close()
    
    def get_patient_notes(self, patient_id: str, limit: int = 100, 
                         offset: int = 0) -> List[Dict]:
        """Get all notes for a specific patient"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            cur.execute("""
                SELECT * FROM notes 
                WHERE patient_id = ?
                ORDER BY timestamp DESC, created_at DESC
                LIMIT ? OFFSET ?
            """, (patient_id, limit, offset))
            
            results = []
            for row in cur.fetchall():
                results.append({
                    'id': row[0],
                    'patient_id': row[1],
                    'note_id': row[2],
                    'content': row[3],
                    'note_type': row[4],
                    'timestamp': row[5],
                    'created_at': row[6]
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting patient notes: {e}")
            return []
        finally:
            conn.close()
    
    def get_notes_summary(self) -> Dict[str, Any]:
        """Get summary statistics about indexed notes"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            # Total notes count
            cur.execute("SELECT COUNT(*) FROM notes")
            total_notes = cur.fetchone()[0]
            
            # Unique patients count
            cur.execute("SELECT COUNT(DISTINCT patient_id) FROM notes")
            unique_patients = cur.fetchone()[0]
            
            # Notes by type
            cur.execute("""
                SELECT note_type, COUNT(*) 
                FROM notes 
                WHERE note_type IS NOT NULL 
                GROUP BY note_type
            """)
            notes_by_type = dict(cur.fetchall())
            
            # Recent notes (last 30 days)
            cur.execute("""
                SELECT COUNT(*) FROM notes 
                WHERE timestamp >= datetime('now', '-30 days')
            """)
            recent_notes = cur.fetchone()[0]
            
            return {
                'total_notes': total_notes,
                'unique_patients': unique_patients,
                'notes_by_type': notes_by_type,
                'recent_notes': recent_notes,
                'last_updated': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error getting notes summary: {e}")
            return {
                'total_notes': 0,
                'unique_patients': 0,
                'notes_by_type': {},
                'recent_notes': 0,
                'last_updated': datetime.now().isoformat()
            }
        finally:
            conn.close()
    
    def clear_notes(self, patient_id: str = None):
        """Clear notes from the index"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        try:
            if patient_id:
                cur.execute("DELETE FROM notes WHERE patient_id = ?", (patient_id,))
                logger.info(f"Cleared notes for patient: {patient_id}")
            else:
                cur.execute("DELETE FROM notes")
                logger.info("Cleared all notes")
            
            conn.commit()
            
        except Exception as e:
            logger.error(f"Error clearing notes: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database file information"""
        try:
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path)
                return {
                    'db_path': self.db_path,
                    'size_bytes': size,
                    'size_mb': round(size / (1024 * 1024), 2),
                    'exists': True
                }
            else:
                return {
                    'db_path': self.db_path,
                    'size_bytes': 0,
                    'size_mb': 0,
                    'exists': False
                }
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {
                'db_path': self.db_path,
                'error': str(e)
            }

# Global instance consolidated into the primary local DB
import os
_HERE = os.path.abspath(os.path.dirname(__file__))
_LOCAL_DB_PATH = os.path.join(_HERE, "local_ehr.db")
notes_processor = NotesProcessor(db_path=_LOCAL_DB_PATH)
