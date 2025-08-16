"""
Knowledge Base

Local storage and management of external medical knowledge data.
Provides caching, indexing, and retrieval of evidence and medical information.
"""

import sqlite3
import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from contextlib import contextmanager
import hashlib

logger = logging.getLogger(__name__)

class KnowledgeBase:
    """Local knowledge base for storing external medical data"""
    
    def __init__(self, db_path: str = "knowledge_base.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize the knowledge base database"""
        with self._get_connection() as conn:
            # External knowledge table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS external_knowledge (
                    id TEXT PRIMARY KEY,
                    source_name TEXT NOT NULL,
                    source_id TEXT,
                    knowledge_type TEXT NOT NULL,
                    title TEXT,
                    content TEXT,
                    metadata TEXT,  -- JSON string
                    confidence_score REAL DEFAULT 0.0,
                    relevance_score REAL DEFAULT 0.0,
                    last_updated TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    expires_at TEXT
                )
            """)
            
            # Knowledge relationships table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS knowledge_relationships (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    target_id TEXT NOT NULL,
                    relationship_type TEXT NOT NULL,
                    strength REAL DEFAULT 0.0,
                    evidence_count INTEGER DEFAULT 0,
                    metadata TEXT,  -- JSON string
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (source_id) REFERENCES external_knowledge (id),
                    FOREIGN KEY (target_id) REFERENCES external_knowledge (id)
                )
            """)
            
            # Search index table
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_search USING fts5(
                    id UNINDEXED,
                    title,
                    content,
                    knowledge_type,
                    source_name,
                    tokenize='unicode61 remove_diacritics 2'
                )
            """)
            
            # Create indexes for better performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_source ON external_knowledge(source_name)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_type ON external_knowledge(knowledge_type)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_updated ON external_knowledge(last_updated)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_knowledge_expires ON external_knowledge(expires_at)")
            
            conn.commit()
    
    @contextmanager
    def _get_connection(self):
        """Get database connection with proper configuration"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _generate_id(self, source_name: str, source_id: str, knowledge_type: str) -> str:
        """Generate unique ID for knowledge entry"""
        content = f"{source_name}:{source_id}:{knowledge_type}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _serialize_metadata(self, metadata: Dict) -> str:
        """Serialize metadata to JSON string"""
        return json.dumps(metadata, default=str)
    
    def _deserialize_metadata(self, metadata_str: str) -> Dict:
        """Deserialize metadata from JSON string"""
        if not metadata_str:
            return {}
        try:
            return json.loads(metadata_str)
        except json.JSONDecodeError:
            logger.warning(f"Failed to deserialize metadata: {metadata_str}")
            return {}
    
    async def store_knowledge(self, source_name: str, source_id: str, knowledge_type: str,
                            title: str, content: str, metadata: Dict = None,
                            confidence_score: float = 0.0, relevance_score: float = 0.0,
                            ttl_hours: int = 24) -> str:
        """Store knowledge entry in the database"""
        knowledge_id = self._generate_id(source_name, source_id, knowledge_type)
        metadata_str = self._serialize_metadata(metadata or {})
        expires_at = (datetime.now() + timedelta(hours=ttl_hours)).isoformat()
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO external_knowledge 
                (id, source_name, source_id, knowledge_type, title, content, metadata,
                 confidence_score, relevance_score, last_updated, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                knowledge_id, source_name, source_id, knowledge_type, title, content,
                metadata_str, confidence_score, relevance_score, 
                datetime.now().isoformat(), expires_at
            ))
            
            # Update search index
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_search 
                (id, title, content, knowledge_type, source_name)
                VALUES (?, ?, ?, ?, ?)
            """, (knowledge_id, title, content, knowledge_type, source_name))
            
            conn.commit()
        
        logger.info(f"Stored knowledge entry: {knowledge_id}")
        return knowledge_id
    
    async def get_knowledge(self, knowledge_id: str) -> Optional[Dict]:
        """Get knowledge entry by ID"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM external_knowledge WHERE id = ?
            """, (knowledge_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "id": row['id'],
                    "source_name": row['source_name'],
                    "source_id": row['source_id'],
                    "knowledge_type": row['knowledge_type'],
                    "title": row['title'],
                    "content": row['content'],
                    "metadata": self._deserialize_metadata(row['metadata']),
                    "confidence_score": row['confidence_score'],
                    "relevance_score": row['relevance_score'],
                    "last_updated": row['last_updated'],
                    "created_at": row['created_at'],
                    "expires_at": row['expires_at']
                }
        return None
    
    async def search_knowledge(self, query: str, knowledge_type: str = None, 
                             source_name: str = None, limit: int = 20) -> List[Dict]:
        """Search knowledge base using FTS5"""
        with self._get_connection() as conn:
            # Build search query
            search_conditions = [f"knowledge_search MATCH ?"]
            params = [query]
            
            if knowledge_type:
                search_conditions.append("knowledge_type = ?")
                params.append(knowledge_type)
            
            if source_name:
                search_conditions.append("source_name = ?")
                params.append(source_name)
            
            where_clause = " AND ".join(search_conditions)
            
            cursor = conn.execute(f"""
                SELECT k.*, rank FROM external_knowledge k
                JOIN knowledge_search s ON k.id = s.id
                WHERE {where_clause}
                ORDER BY rank DESC, relevance_score DESC, confidence_score DESC
                LIMIT ?
            """, params + [limit])
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "id": row['id'],
                    "source_name": row['source_name'],
                    "source_id": row['source_id'],
                    "knowledge_type": row['knowledge_type'],
                    "title": row['title'],
                    "content": row['content'],
                    "metadata": self._deserialize_metadata(row['metadata']),
                    "confidence_score": row['confidence_score'],
                    "relevance_score": row['relevance_score'],
                    "rank": row['rank'],
                    "last_updated": row['last_updated']
                }
                results.append(result)
            
            return results
    
    async def get_knowledge_by_type(self, knowledge_type: str, limit: int = 50) -> List[Dict]:
        """Get knowledge entries by type"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT * FROM external_knowledge 
                WHERE knowledge_type = ? AND (expires_at IS NULL OR expires_at > ?)
                ORDER BY relevance_score DESC, confidence_score DESC
                LIMIT ?
            """, (knowledge_type, datetime.now().isoformat(), limit))
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "id": row['id'],
                    "source_name": row['source_name'],
                    "source_id": row['source_id'],
                    "knowledge_type": row['knowledge_type'],
                    "title": row['title'],
                    "content": row['content'],
                    "metadata": self._deserialize_metadata(row['metadata']),
                    "confidence_score": row['confidence_score'],
                    "relevance_score": row['relevance_score'],
                    "last_updated": row['last_updated']
                }
                results.append(result)
            
            return results
    
    async def store_relationship(self, source_id: str, target_id: str, 
                               relationship_type: str, strength: float = 0.0,
                               evidence_count: int = 0, metadata: Dict = None) -> str:
        """Store relationship between knowledge entries"""
        relationship_id = hashlib.sha256(
            f"{source_id}:{target_id}:{relationship_type}".encode()
        ).hexdigest()[:16]
        
        metadata_str = self._serialize_metadata(metadata or {})
        
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO knowledge_relationships
                (id, source_id, target_id, relationship_type, strength, evidence_count, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (relationship_id, source_id, target_id, relationship_type, 
                  strength, evidence_count, metadata_str))
            conn.commit()
        
        return relationship_id
    
    async def get_relationships(self, knowledge_id: str, relationship_type: str = None) -> List[Dict]:
        """Get relationships for a knowledge entry"""
        with self._get_connection() as conn:
            query = """
                SELECT r.*, k.title as target_title, k.knowledge_type as target_type
                FROM knowledge_relationships r
                JOIN external_knowledge k ON r.target_id = k.id
                WHERE r.source_id = ?
            """
            params = [knowledge_id]
            
            if relationship_type:
                query += " AND r.relationship_type = ?"
                params.append(relationship_type)
            
            query += " ORDER BY r.strength DESC, r.evidence_count DESC"
            
            cursor = conn.execute(query, params)
            
            results = []
            for row in cursor.fetchall():
                result = {
                    "id": row['id'],
                    "source_id": row['source_id'],
                    "target_id": row['target_id'],
                    "target_title": row['target_title'],
                    "target_type": row['target_type'],
                    "relationship_type": row['relationship_type'],
                    "strength": row['strength'],
                    "evidence_count": row['evidence_count'],
                    "metadata": self._deserialize_metadata(row['metadata'])
                }
                results.append(result)
            
            return results
    
    async def cleanup_expired(self) -> int:
        """Remove expired knowledge entries"""
        with self._get_connection() as conn:
            cursor = conn.execute("""
                DELETE FROM external_knowledge 
                WHERE expires_at IS NOT NULL AND expires_at < ?
            """, (datetime.now().isoformat(),))
            
            deleted_count = cursor.rowcount
            
            # Also clean up search index for deleted entries
            conn.execute("""
                DELETE FROM knowledge_search 
                WHERE id NOT IN (SELECT id FROM external_knowledge)
            """)
            
            conn.commit()
        
        logger.info(f"Cleaned up {deleted_count} expired knowledge entries")
        return deleted_count
    
    async def get_statistics(self) -> Dict:
        """Get knowledge base statistics"""
        with self._get_connection() as conn:
            # Total entries
            cursor = conn.execute("SELECT COUNT(*) as total FROM external_knowledge")
            total_entries = cursor.fetchone()['total']
            
            # Entries by type
            cursor = conn.execute("""
                SELECT knowledge_type, COUNT(*) as count 
                FROM external_knowledge 
                GROUP BY knowledge_type
            """)
            by_type = {row['knowledge_type']: row['count'] for row in cursor.fetchall()}
            
            # Entries by source
            cursor = conn.execute("""
                SELECT source_name, COUNT(*) as count 
                FROM external_knowledge 
                GROUP BY source_name
            """)
            by_source = {row['source_name']: row['count'] for row in cursor.fetchall()}
            
            # Total relationships
            cursor = conn.execute("SELECT COUNT(*) as total FROM knowledge_relationships")
            total_relationships = cursor.fetchone()['total']
            
            return {
                "total_entries": total_entries,
                "total_relationships": total_relationships,
                "by_type": by_type,
                "by_source": by_source,
                "timestamp": datetime.now().isoformat()
            }
