"""
Database Connection Management

Handles MongoDB connection lifecycle.
"""

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pymongo.collection import Collection

from .config import settings

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Manages MongoDB connection lifecycle."""
    
    def __init__(self):
        self._client: Optional[MongoClient] = None
        self._collection: Optional[Collection] = None
    
    @property
    def client(self) -> Optional[MongoClient]:
        return self._client
    
    @property
    def collection(self) -> Optional[Collection]:
        return self._collection
    
    @property
    def is_connected(self) -> bool:
        return self._client is not None and self._collection is not None
    
    def connect(self) -> bool:
        """
        Establish database connection.
        
        Returns:
            True if connection successful, False otherwise
        """
        if not settings.has_database:
            logger.warning("Database connection skipped - no MONGO_URI configured")
            return False
        
        try:
            self._client = MongoClient(
                settings.mongo_uri,
                serverSelectionTimeoutMS=5000
            )
            
            # Test connection
            self._client.admin.command('ping')
            
            # Get collection
            db = self._client[settings.db_name]
            self._collection = db[settings.collection_name]
            
            logger.info("Successfully connected to MongoDB!")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            self._client = None
            self._collection = None
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            self._client = None
            self._collection = None
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self._client:
            self._client.close()
            self._client = None
            self._collection = None
            logger.info("Closed MongoDB connection")
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Global database manager instance
db_manager = DatabaseManager()


def get_collection() -> Optional[Collection]:
    """Get the database collection, connecting if necessary."""
    if not db_manager.is_connected:
        db_manager.connect()
    return db_manager.collection


def init_database():
    """Initialize database connection on startup."""
    return db_manager.connect()


def close_database():
    """Close database connection on shutdown."""
    db_manager.disconnect()
