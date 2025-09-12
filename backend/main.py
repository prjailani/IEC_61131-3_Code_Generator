from fastapi import FastAPI, Body, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import random
import sys
import os
import json
from pymongo import MongoClient
import re 


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from AI_Integration.main import generate_IEC_JSON, regenerate_IEC_JSON
from validator import validator
from generator import generator

MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://natrajrakul_db_user:kvxWYOeQXDOc0j7n@converter.wtd1klj.mongodb.net/?retryWrites=true&w=majority&appName=Converter")
DB_NAME = "iec_code_generator" 
COLLECTION_NAME = "variables"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    variables_collection = db[COLLECTION_NAME]
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    client = None
    variables_collection=None


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)






@app.get("/home")
def root():
    return {"vazhthu":"Vanakkam"}

class NarrativeRequest(BaseModel):
    narrative: str

class Variable(BaseModel):
    deviceName: str
    dataType: str
    range: str
    MetaData: str
    id: str = None 


class SaveVariablesRequest(BaseModel):
    variables: list[Variable]

@app.post("/generate-code")
def generateCode(body:NarrativeRequest):
    max_attempts = 2
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
    print(intermediate)
    if(response[0]):
        code = generator(json.loads(intermediate))
        
        return {"status":"ok","code":code}
    else:
        raise HTTPException(status_code=400, detail=response[1])








@app.post("/save-variables")
def save_variables(body: SaveVariablesRequest):
  
    if not client:
        return {"status": "error", "message": "Database connection failed."}

    try:
        db_variables = list(variables_collection.find({}, {"deviceName": 1}))
        db_device_names = {doc["deviceName"] for doc in db_variables}
        
        frontend_device_names = {var.deviceName for var in body.variables}
        
        deleted_names = db_device_names - frontend_device_names
        if deleted_names:
            variables_collection.delete_many({"deviceName": {"$in": list(deleted_names)}})

        for var in body.variables:
            query = {"deviceName": {"$regex": f"^{re.escape(var.deviceName)}$", "$options": "i"}}
            variables_collection.update_one(
                query,
                {"$set": var.dict()},
                upsert=True
            )
        
        return {"status": "ok", "message": f"Successfully synchronized {len(body.variables)} variables."}
    except Exception as e:
        print(f"Error synchronizing with database: {e}")
        return {"status": "error", "message": "Failed to save variables to the database."}







@app.post("/upload-variables-json")
async def upload_variables_json(file: UploadFile = File(...)):
   
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

@app.get("/get-variables")
def get_variables():
  
    if not client:
        return {"status": "error", "message": "Database connection failed."}

    try:
        variables = list(variables_collection.find({}, {"_id": 0})) 
        return {"status": "ok", "variables": variables}
    except Exception as e:
        print(f"Error retrieving from MongoDB: {e}")
        return {"status": "error", "message": "Failed to retrieve variables from the database."}







@app.delete("/remove-duplicates")
def remove_duplicates():
   


    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed.")
    
    try:
       
        device_names = [doc["deviceName"] for doc in variables_collection.find({}, {"deviceName": 1})]
        
        seen_names = {}
        for name in device_names:
            lower_name = name.lower()
            if lower_name not in seen_names:
                seen_names[lower_name] = True
            else:
                # Found a duplicate, remove it
                variables_collection.delete_one({"deviceName": name})
        
        return {"status": "ok", "message": "Duplicates have been removed."}
    except Exception as e:
        print(f"Error removing duplicates: {e}")
        raise HTTPException(status_code=500, detail="An error occurred while removing duplicates.")