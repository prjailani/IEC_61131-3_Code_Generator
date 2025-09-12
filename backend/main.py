from fastapi import FastAPI, Body, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel,EmailStr
import random
import sys
import os
import json
from pymongo import MongoClient
import re 
from typing import List, Optional
import hashlib

from bson import ObjectId
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from AI_Integration.main import generate_IEC_JSON, regenerate_IEC_JSON
from validator import validator
from generator import generator
from datetime import datetime

# MONGO_URI = os.getenv("MONGO_URI", "mongodb+srv://natrajrakul_db_user:kvxWYOeQXDOc0j7n@converter.wtd1klj.mongodb.net/?retryWrites=true&w=majority&appName=Converter")
# DB_NAME = "iec_code_generator" 
# COLLECTION_NAME = "variables"

# try:
#     client = MongoClient(MONGO_URI)
#     db = client[DB_NAME]
#     variables_collection = db[COLLECTION_NAME]
# except Exception as e:
#     print(f"Failed to connect to MongoDB: {e}")
#     client = None
#     variables_collection=None


# Import your existing modules
try:
    from AI_Integration.main import generate_IEC_JSON, regenerate_IEC_JSON
    from validator import validator
    from generator import generator
except ImportError:
    print("Warning: AI Integration modules not found. Some features may not work.")

MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb+srv://natrajrakul_db_user:kvxWYOeQXDOc0j7n@converter.wtd1klj.mongodb.net/?retryWrites=true&w=majority&appName=Converter"
)
DB_NAME = "iec_code_generator"
COLLECTION_NAME = "Users Credentials"

try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    variables_collection = db[COLLECTION_NAME]
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    client = None
    variables_collection = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== MODELS =====================
class Variable(BaseModel):
    name: str
    dataType: str
    minRange: int
    maxRange: int
    description: str
    tag: Optional[str] = None

class ChatEntry(BaseModel):
    query: str
    time: str
    generatedCode: str

class User(BaseModel):
    id: str
    name: str
    email: str
    password: str
    variables: List[Variable] = []
    chatHistory: List[ChatEntry] = []

class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class NarrativeRequest(BaseModel):
    narrative: str
    user_id: Optional[str] = None

class SaveVariablesRequest(BaseModel):
    user_id: str
    variables: List[Variable]

class AddVariableRequest(BaseModel):
    user_id: str
    variable: Variable


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, hashed: str) -> bool:
    return hash_password(password) == hashed

def serialize_objectid(obj):
    if isinstance(obj, ObjectId):
        return str(obj)
    return obj


# ----------------- USER MANAGEMENT -----------------
@app.post("/register")
def register_user(request: CreateUserRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        existing_user = variables_collection.find_one({"email": request.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="User with this email already exists")

        user_data = {
            "id": f"user{random.randint(1000, 9999)}",
            "name": request.name,
            "email": request.email,
            "password": hash_password(request.password),
            "variables": [],
            "chatHistory": []
        }
        result = variables_collection.insert_one(user_data)
        user_data["_id"] = str(result.inserted_id)
        return {
            "status": "ok",
            "message": "User registered successfully",
            "user": {
                "id": user_data["id"],
                "name": user_data["name"],
                "email": user_data["email"]
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail="Failed to register user")

@app.post("/login")
def login_user(request: LoginRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        user = variables_collection.find_one({"email": request.email})
        if not user or not verify_password(request.password, user["password"]):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        return {
            "status": "ok",
            "message": "Login successful",
            "user": {
                "id": user["id"],
                "name": user["name"],
                "email": user["email"],
                "_id": str(user["_id"])
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error during login: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

# @app.get("/users/{user_id}")
# def get_user(user_id: str):
#     if not client:
#         raise HTTPException(status_code=500, detail="Database connection failed")
#     try:
#         user = variables_collection.find_one({"id": user_id})
#         if not user:
#             raise HTTPException(status_code=404, detail="User not found")
#         user["_id"] = str(user["_id"])
#         return {"status": "ok", "user": user}
#     except HTTPException:
#         raise
#     except Exception as e:
#         print(f"Error fetching user: {e}")
#         raise HTTPException(status_code=500, detail="Failed to fetch user")










@app.get("/users/{user_id}")
def get_user(user_id: str):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        user = variables_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user["_id"] = str(user["_id"])
        return {"status": "ok", "user": user}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching user: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch user")

# ----------------- VARIABLE MANAGEMENT -----------------
@app.get("/get-variables/{user_id}")
def get_variables(user_id: str):
    if not client:
        return {"status": "error", "message": "Database connection failed"}
    try:
        user = variables_collection.find_one({"id": user_id})
        if not user:
            return {"status": "error", "message": "User not found"}
        variables = user.get("variables", [])
        return {"status": "ok", "variables": variables}
    except Exception as e:
        print(f"Error retrieving variables: {e}")
        return {"status": "error", "message": "Failed to retrieve variables"}


@app.post("/save-variables")
def save_variables(request: SaveVariablesRequest):
    if not client:
        return {"status": "error", "message": "Database connection failed"}
    try:
        result = variables_collection.update_one(
            {"id": request.user_id},
            {"$set": {"variables": [var.dict() for var in request.variables]}}
        )
        if result.matched_count == 0:
            return {"status": "error", "message": "User not found"}
        return {"status": "ok", "message": f"Saved {len(request.variables)} variables"}
    except Exception as e:
        print(f"Error saving variables: {e}")
        return {"status": "error", "message": "Failed to save variables"}

@app.post("/add-variable")
def add_variable(request: AddVariableRequest):
    if not client:
        return {"status": "error", "message": "Database connection failed"}
    try:
        result = variables_collection.update_one(
            {"id": request.user_id},
            {"$push": {"variables": request.variable.dict()}}
        )
        if result.matched_count == 0:
            return {"status": "error", "message": "User not found"}
        return {"status": "ok", "message": "Variable added successfully"}
    except Exception as e:
        print(f"Error adding variable: {e}")
        return {"status": "error", "message": "Failed to add variable"}

@app.delete("/remove-variable")
def remove_variable(user_id: str, variable_name: str):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        result = variables_collection.update_one(
            {"id": user_id},
            {"$pull": {"variables": {"name": variable_name}}}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "ok", "message": "Variable removed successfully"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing variable: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove variable")









# ----------------- CODE GENERATION -----------------
@app.post("/generate-code")
def generate_code(request: NarrativeRequest):
    try:
        max_attempts = 2
        intermediate = generate_IEC_JSON(request.narrative)
        response = validator(json.loads(intermediate))

        while response[0] == False and max_attempts > 0:
            max_attempts -= 1
            intermediate = regenerate_IEC_JSON(request.narrative, response[1], intermediate)
            response = validator(json.loads(intermediate))

        if response[0]:
            code = generator(json.loads(intermediate))
            if request.user_id and client:
                chat_entry = {
                    "query": request.narrative,
                    "time": datetime.utcnow().isoformat(),
                    "generatedCode": code
                }
                variables_collection.update_one(
                    {"id": request.user_id},
                    {"$push": {"chatHistory": chat_entry}}
                )
            return {"status": "ok", "code": code}
        else:
            raise HTTPException(status_code=400, detail=response[1])
    except Exception as e:
        print(f"Error generating code: {e}")
        raise HTTPException(status_code=500, detail="Code generation failed")

# ----------------- CHAT HISTORY -----------------
@app.get("/chat-history/{user_id}")
def get_chat_history(user_id: str):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        user = variables_collection.find_one({"id": user_id})
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "ok", "chatHistory": user.get("chatHistory", [])}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")

# ----------------- REMOVE DUPLICATES -----------------
@app.delete("/remove-duplicates")
def remove_duplicates(user_id: Optional[str] = None):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        removed_count = 0
        if user_id:
            user = variables_collection.find_one({"id": user_id})
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            variables = user.get("variables", [])
            seen = set()
            unique = []
            for var in variables:
                if var["name"].lower() not in seen:
                    seen.add(var["name"].lower())
                    unique.append(var)
            variables_collection.update_one({"id": user_id}, {"$set": {"variables": unique}})
            removed_count = len(variables) - len(unique)
        else:
            for user in variables_collection.find({}):
                variables = user.get("variables", [])
                seen = set()
                unique = []
                for var in variables:
                    if var["name"].lower() not in seen:
                        seen.add(var["name"].lower())
                        unique.append(var)
                if len(unique) < len(variables):
                    variables_collection.update_one({"_id": user["_id"]}, {"$set": {"variables": unique}})
                    removed_count += len(variables) - len(unique)
        return {"status": "ok", "message": f"Removed {removed_count} duplicate variables"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error removing duplicates: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove duplicates")



























# class LoginRequest(BaseModel):
#     email: str
#     password: str

# class RegisterRequest(BaseModel):
#     name: str
#     email: str
#     password: str

# # ----------- Dummy Endpoints -----------

# @app.post("/login")
# def login(data: LoginRequest):
   
#     return {
#         "status": "ok",
#         "message": "Login successful (dummy)",
#         "user": {
#             "id": 1,
#             "name": "Dummy User",
#             "email": data.email
#         },
#         "token": "dummy-token-123"
#     }

# @app.post("/register")
# def register(data: RegisterRequest):
   
#     return {
#         "status": "ok",
#         "message": "Registration successful (dummy)",
#         "user": {
#             "id": 2,
#             "name": data.name,
#             "email": data.email
#         },
#         "token": "dummy-token-456"
#     }


@app.get("/home")
def root():
    return {"vazhthu":"Vanakkam"}

# class NarrativeRequest(BaseModel):
#     narrative: str

# class Variable(BaseModel):
#     deviceName: str
#     dataType: str
#     range: str
#     MetaData: str
#     id: str = None 


# class SaveVariablesRequest(BaseModel):
#     variables: list[Variable]

# @app.post("/generate-code")
# def generateCode(body:NarrativeRequest):
#     max_attempts = 2
#     intermediate = generate_IEC_JSON(body.narrative)
#     response = validator(json.loads(intermediate))

    
#     while(response[0] == False and max_attempts>0):
#         max_attempts -= 1
#         print("Regenerating IEC JSON due to validation errors...")
#         print(intermediate)
#         print(response[1])
#         print("\n\n\n\n")
#         intermediate = regenerate_IEC_JSON(body.narrative ,response[1],intermediate)
#         response = validator(json.loads(intermediate))
#     print(intermediate)
#     if(response[0]):
#         code = generator(json.loads(intermediate))
        
#         return {"status":"ok","code":code}
#     else:
#         raise HTTPException(status_code=400, detail=response[1])








# @app.post("/save-variables")
# def save_variables(body: SaveVariablesRequest):
  
#     if not client:
#         return {"status": "error", "message": "Database connection failed."}

#     try:
#         db_variables = list(variables_collection.find({}, {"deviceName": 1}))
#         db_device_names = {doc["deviceName"] for doc in db_variables}
        
#         frontend_device_names = {var.deviceName for var in body.variables}
        
#         deleted_names = db_device_names - frontend_device_names
#         if deleted_names:
#             variables_collection.delete_many({"deviceName": {"$in": list(deleted_names)}})

#         for var in body.variables:
#             query = {"deviceName": {"$regex": f"^{re.escape(var.deviceName)}$", "$options": "i"}}
#             variables_collection.update_one(
#                 query,
#                 {"$set": var.dict()},
#                 upsert=True
#             )
        
#         return {"status": "ok", "message": f"Successfully synchronized {len(body.variables)} variables."}
#     except Exception as e:
#         print(f"Error synchronizing with database: {e}")
#         return {"status": "error", "message": "Failed to save variables to the database."}







# @app.post("/upload-variables-json")
# async def upload_variables_json(file: UploadFile = File(...)):
   
#     if not client:
#         return {"status": "error", "message": "Database connection failed."}
    
#     try:
#         contents = await file.read()
#         variables_list = json.loads(contents.decode("utf-8"))

#         for var in variables_list:
#             variables_collection.update_one(
#                 {"id": var.get("id", str(random.getrandbits(32)))},
#                 {"$set": var},
#                 upsert=True
#             )
        
#         return {"status": "ok", "message": f"Successfully uploaded and saved {len(variables_list)} variables."}
#     except json.JSONDecodeError:
#         return {"status": "error", "message": "Invalid JSON file format."}
#     except Exception as e:
#         print(f"Error processing file upload: {e}")
#         return {"status": "error", "message": "An unexpected error occurred during file upload."}

# @app.get("/get-variables")
# def get_variables():
  
#     if not client:
#         return {"status": "error", "message": "Database connection failed."}

#     try:
#         variables = list(variables_collection.find({}, {"_id": 0})) 
#         return {"status": "ok", "variables": variables}
#     except Exception as e:
#         print(f"Error retrieving from MongoDB: {e}")
#         return {"status": "error", "message": "Failed to retrieve variables from the database."}







# @app.delete("/remove-duplicates")
# def remove_duplicates():
   


#     if not client:
#         raise HTTPException(status_code=500, detail="Database connection failed.")
    
#     try:
       
#         device_names = [doc["deviceName"] for doc in variables_collection.find({}, {"deviceName": 1})]
        
#         seen_names = {}
#         for name in device_names:
#             lower_name = name.lower()
#             if lower_name not in seen_names:
#                 seen_names[lower_name] = True
#             else:
#                 # Found a duplicate, remove it
#                 variables_collection.delete_one({"deviceName": name})
        
#         return {"status": "ok", "message": "Duplicates have been removed."}
#     except Exception as e:
#         print(f"Error removing duplicates: {e}")
#         raise HTTPException(status_code=500, detail="An error occurred while removing duplicates.")