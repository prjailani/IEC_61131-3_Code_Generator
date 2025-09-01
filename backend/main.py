from fastapi import FastAPI, Body, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from AI_Integration.main import generate_IEC_JSON, regenerate_IEC_JSON
from validator import validator
from generator import generator
import os
import json
from pymongo import MongoClient

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://natrajrakul_db_user:kvxWYOeQXDOc0j7n@converter.wtd1klj.mongodb.net/?retryWrites=true&w=majority&appName=Converter")
DB_NAME = "iec_code_generator" 
COLLECTION_NAME = "variables"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    variables_collection = db[COLLECTION_NAME]
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    client = None
    variables_collection = None
# --- END: MONGODB CONFIGURATION ---


def fetch_variables():
    """
    Fetches all variable documents from the MongoDB collection.
    
    Returns:
        list: A list of variable documents.
    """
    if variables_collection is None:
        print("MongoDB collection is not initialized.")
        return []
    
    try:
        variables = list(variables_collection.find({}))
        for i in variables:
            del i['_id']
            del i['id']

        with open("variables.json","w") as f:
            f.write(json.dumps(variables,indent=2))
        return variables
    except Exception as e:
        print(f"Error fetching variables from MongoDB: {e}")
        return []

fetch_variables()

@app.get("/home")
def root():
    return {"vazhthu":"Vanakkam"}

class NarrativeRequest(BaseModel):
    narrative: str

class Variable(BaseModel):
    id: str
    deviceName: str
    dataType: str
    range: str

class SaveVariablesRequest(BaseModel):
    variables: list[Variable]

@app.post("/generate-code")
def generateCode(body:NarrativeRequest):
    max_attempts = 5
    intermediate = generate_IEC_JSON(body.narrative)
    response = validator(json.loads(intermediate))

    
    while(response[0] == False and max_attempts>0):
        max_attempts -= 1
        print("Regenerating IEC JSON due to validation errors...")
        print(intermediate)
        print(response[1])
        print("\n\n\n\n")
        intermediate = regenerate_IEC_JSON(body.narrative ,response[1],intermediate)
        response = validator(json.loads(intermediate))
    
    code = generator(json.loads(intermediate))
    
    return {"status":"ok","code":code}


@app.post("/save-variables")
def save_variables(body: SaveVariablesRequest):
    """
    This endpoint receives a list of variables from the frontend and saves them
    to a MongoDB database.
    """
    if not client:
        return {"status": "error", "message": "Database connection failed."}

    variables_data = [v.dict() for v in body.variables]
    
    try:
        operations = [
            variables_collection.update_one(
                {"id": var["id"]},
                {"$set": var},
                upsert=True
            ) for var in variables_data
        ]
        
        return {"status": "ok", "message": f"Successfully saved {len(variables_data)} variables."}
    except Exception as e:
        print(f"Error saving to MongoDB: {e}")
        return {"status": "error", "message": "Failed to save variables to the database."}

@app.post("/upload-variables-json")
async def upload_variables_json(file: UploadFile = File(...)):
    """
    This endpoint receives a JSON file, parses its contents, and saves the
    variables to a MongoDB database.
    """
    if not client:
        return {"status": "error", "message": "Database connection failed."}
    
    try:
        contents = await file.read()
        variables_list = json.loads(contents.decode("utf-8"))

        for var in variables_list:
            variables_collection.update_one(
                {"id": var.get("id", str(random.getrandbits(32)))},
                {"$set": var},
                upsert=True
            )
        
        return {"status": "ok", "message": f"Successfully uploaded and saved {len(variables_list)} variables."}
    except json.JSONDecodeError:
        return {"status": "error", "message": "Invalid JSON file format."}
    except Exception as e:
        print(f"Error processing file upload: {e}")
        return {"status": "error", "message": "An unexpected error occurred during file upload."}
