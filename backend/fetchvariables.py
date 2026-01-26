"""
Variable Fetcher for IEC 61131-3 Code Generator

Fetches variables from MongoDB and writes them to a local JSON file
for use by the validator and AI integration modules.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, PyMongoError

# Load .env from parent directory (project root)
root_env = Path(__file__).parent.parent / ".env"
load_dotenv(root_env)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("DB_NAME", "iec_code_generator")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "variables")

# Output path for variables JSON
SCRIPT_DIR = Path(__file__).parent
OUTPUT_PATH = SCRIPT_DIR.parent / "AI_Integration" / "kb" / "templates" / "variables.json"


class DatabaseConnection:
    """Context manager for MongoDB connection."""
    
    def __init__(self, mongo_uri: str, db_name: str, collection_name: str):
        self.mongo_uri = mongo_uri
        self.db_name = db_name
        self.collection_name = collection_name
        self.client: Optional[MongoClient] = None
        self.collection = None
    
    def __enter__(self):
        if not self.mongo_uri:
            raise ValueError("MONGO_URI environment variable not set")
        
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            # Test connection
            self.client.admin.command('ping')
            db = self.client[self.db_name]
            self.collection = db[self.collection_name]
            logger.info("Successfully connected to MongoDB!")
            return self.collection
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def fetch_variables() -> List[Dict[str, Any]]:
    """
    Fetch all variables from MongoDB.
    
    Returns:
        List of variable dictionaries (without MongoDB internal fields)
    
    Raises:
        Exception: If database connection or query fails
    """
    if not MONGO_URI:
        logger.error("MONGO_URI environment variable not set")
        return []
    
    try:
        with DatabaseConnection(MONGO_URI, DB_NAME, COLLECTION_NAME) as collection:
            # Fetch all variables, excluding internal MongoDB fields
            variables = list(collection.find({}, {"_id": 0, "id": 0}))
            
            # Clean up any remaining internal fields
            cleaned_variables = []
            for var in variables:
                cleaned_var = {k: v for k, v in var.items() if not k.startswith('_')}
                cleaned_variables.append(cleaned_var)
            
            logger.info(f"Fetched {len(cleaned_variables)} variables from database")
            return cleaned_variables
            
    except Exception as e:
        logger.error(f"Error fetching variables from MongoDB: {e}")
        return []


def write_variables_to_file(variables: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Write variables to a JSON file.
    
    Args:
        variables: List of variable dictionaries
        output_path: Path to output JSON file
    
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write with pretty formatting
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(variables, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Successfully wrote {len(variables)} variables to {output_path}")
        return True
        
    except OSError as e:
        logger.error(f"Error writing to file {output_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error writing variables: {e}")
        return False


def sync_variables() -> bool:
    """
    Main synchronization function.
    Fetches variables from database and writes to local file.
    
    Returns:
        True if sync was successful, False otherwise
    """
    logger.info(f"Starting variable sync from database to {OUTPUT_PATH}")
    
    # Fetch from database
    variables = fetch_variables()
    
    if not variables:
        logger.warning("No variables fetched from database")
        # Still write empty array to ensure file exists
        return write_variables_to_file([], OUTPUT_PATH)
    
    # Write to file
    return write_variables_to_file(variables, OUTPUT_PATH)


def main():
    """Entry point for script execution."""
    import sys
    
    success = sync_variables()
    
    if success:
        logger.info("Variable synchronization completed successfully")
        sys.exit(0)
    else:
        logger.error("Variable synchronization failed")
        sys.exit(1)


# Only run when executed directly, not when imported
if __name__ == "__main__":
    main()
