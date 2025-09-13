import os
import json
from pymongo import MongoClient
from AI_Integration.main import Rag

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://natrajrakul_db_user:kvxWYOeQXDOc0j7n@converter.wtd1klj.mongodb.net/?retryWrites=true&w=majority&appName=Converter")
DB_NAME = "iec_code_generator" 
COLLECTION_NAME = "Users Credentials"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    variables_collection = db[COLLECTION_NAME]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    client = None
    variables_collection=None

def fetch_variables(user_id):
     
    if variables_collection is None:
        print("MongoDB collection is not initialized.")
        return []
    
    try:
        variables = variables_collection.find({"id": user_id})
        variables = list(variables_collection.find({"id": user_id}, {"variables": 1, "_id": 0}))[0]["variables"]

        with open("./AI_Integration/kb/templates/variables.json","w") as f:
            f.write(json.dumps(variables,indent=2))
        Rag()
        return variables
    except Exception as e:
        print(f"Error fetching variables from MongoDB: {e}")
        return []