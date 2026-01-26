"""
Variables Service

Handles all variable-related database operations.
"""

import re
import logging
import sys
import os
from typing import List, Dict, Any, Set
from pymongo.errors import PyMongoError

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from core import get_collection
from models import Variable

logger = logging.getLogger(__name__)


class VariablesServiceError(Exception):
    """Exception for variable service errors."""
    pass


class VariablesService:
    """Service for managing device variables."""
    
    def get_all(self) -> List[Dict[str, Any]]:
        """
        Get all variables from the database.
        
        Returns:
            List of variable dictionaries
        
        Raises:
            VariablesServiceError: If database operation fails
        """
        collection = get_collection()
        if collection is None:
            raise VariablesServiceError("Database connection not available")
        
        try:
            variables = list(collection.find({}, {"_id": 0}))
            logger.info(f"Retrieved {len(variables)} variables")
            return variables
        except PyMongoError as e:
            logger.error(f"Database error retrieving variables: {e}")
            raise VariablesServiceError("Database error while retrieving variables")
    
    def save_all(self, variables: List[Variable]) -> Dict[str, Any]:
        """
        Save/sync variables to the database.
        
        This performs a full sync: deletes removed items, updates existing, adds new.
        
        Args:
            variables: List of variables to save
        
        Returns:
            Result dictionary with status and message
        
        Raises:
            VariablesServiceError: If database operation fails
        """
        collection = get_collection()
        if collection is None:
            raise VariablesServiceError("Database connection not available")
        
        try:
            # Get current variables from database
            db_variables = list(collection.find({}, {"deviceName": 1}))
            db_device_names: Set[str] = {doc["deviceName"] for doc in db_variables}
            
            # Get device names from input
            frontend_device_names: Set[str] = {var.deviceName for var in variables}
            
            # Delete removed variables
            deleted_names = db_device_names - frontend_device_names
            if deleted_names:
                result = collection.delete_many({"deviceName": {"$in": list(deleted_names)}})
                logger.info(f"Deleted {result.deleted_count} variables")
            
            # Upsert all variables
            updated_count = 0
            for var in variables:
                query = {"deviceName": {"$regex": f"^{re.escape(var.deviceName)}$", "$options": "i"}}
                var_dict = var.dict(exclude={'id'})
                result = collection.update_one(query, {"$set": var_dict}, upsert=True)
                if result.modified_count > 0 or result.upserted_id:
                    updated_count += 1
            
            logger.info(f"Synchronized {len(variables)} variables ({updated_count} updated)")
            return {
                "status": "ok",
                "message": f"Successfully synchronized {len(variables)} variables."
            }
            
        except PyMongoError as e:
            logger.error(f"Database error saving variables: {e}")
            raise VariablesServiceError("Database error while saving variables")
    
    def remove_duplicates(self) -> Dict[str, Any]:
        """
        Remove duplicate variables (case-insensitive by deviceName).
        
        Returns:
            Result dictionary with status and message
        
        Raises:
            VariablesServiceError: If database operation fails
        """
        collection = get_collection()
        if collection is None:
            raise VariablesServiceError("Database connection not available")
        
        try:
            # Get all documents
            all_docs = list(collection.find({}, {"_id": 1, "deviceName": 1}))
            
            # Track seen names and duplicates
            seen_names: Dict[str, bool] = {}
            ids_to_delete = []
            
            for doc in all_docs:
                lower_name = doc["deviceName"].lower()
                if lower_name in seen_names:
                    ids_to_delete.append(doc["_id"])
                else:
                    seen_names[lower_name] = True
            
            # Delete duplicates
            deleted_count = 0
            if ids_to_delete:
                result = collection.delete_many({"_id": {"$in": ids_to_delete}})
                deleted_count = result.deleted_count
            
            logger.info(f"Removed {deleted_count} duplicate variables")
            return {
                "status": "ok",
                "message": f"Removed {deleted_count} duplicate(s)."
            }
            
        except PyMongoError as e:
            logger.error(f"Database error removing duplicates: {e}")
            raise VariablesServiceError("Database error while removing duplicates")
    
    def upload_from_list(self, variables_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Upload variables from a list (e.g., from JSON file).
        
        Args:
            variables_list: List of variable dictionaries
        
        Returns:
            Result dictionary with status and message
        
        Raises:
            VariablesServiceError: If database operation fails
        """
        collection = get_collection()
        if collection is None:
            raise VariablesServiceError("Database connection not available")
        
        try:
            saved_count = 0
            for var in variables_list:
                collection.update_one(
                    {"deviceName": var.get("deviceName")},
                    {"$set": var},
                    upsert=True
                )
                saved_count += 1
            
            logger.info(f"Uploaded {saved_count} variables")
            return {
                "status": "ok",
                "message": f"Successfully uploaded {saved_count} variables."
            }
            
        except PyMongoError as e:
            logger.error(f"Database error uploading variables: {e}")
            raise VariablesServiceError("Database error while uploading variables")


# Service instance
variables_service = VariablesService()
