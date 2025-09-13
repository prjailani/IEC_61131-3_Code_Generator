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
from fetchvariables import fetch_variables

from bson import ObjectId
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

from AI_Integration.main import generate_IEC_JSON, regenerate_IEC_JSON,ai_refine_user_query
from validator import validator
from generator import generator
from datetime import datetime, timezone

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
    print("\n\nSuccessfully connected to MongoDB!\n\n")
except Exception as e:
    print(f"Failed to connect to MongoDB: {e}")
    client = None
    variables_collection = None

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # or restrict to your frontend origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== MODELS =====================
class Variable(BaseModel):
    name: str
    dataType: str
    minRange: str
    maxRange: str
    description: str
    tag: Optional[str] = None

class ChatEntry(BaseModel):
    user_id : str
    query: str
    response: str
    feedback: str
    time: str


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


class ChatEntryRequest(BaseModel):
    user_id: str
    query: str
    response: str
    feedback: str | None = None



class RegenerateRequest(BaseModel):
    query : str
    feedback: str
    intermediateCode : str
    user_id: Optional[str] = None





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
        fetch_variables( user_data["id"])
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
        fetch_variables( user["id"])
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
            return {"status": "ok", "variables": []}
        variables = user.get("variables", [])
        return {"status": "ok", "variables": variables}
    except Exception as e:
        print(f"Error retrieving variables: {e}")
        return {"status": "error", "message": "Failed to retrieve variables"}


@app.post("/save-variables")
def save_variables( request: SaveVariablesRequest):
    if not client:
        return {"status": "error", "message": "Database connection failed"}
    try:
        result = variables_collection.update_one(
            {"id": request.user_id},
            {"$set": {"variables": [var.model_dump() for var in request.variables]}},
        )
        
        if result.matched_count == 0:
            return {"status": "error", "message": "User not found"}
        fetch_variables(request.user_id)
        return {"status": "ok", "message": f"Saved {len(request.variables)} variables"}
    except Exception as e:
        print(f"Error saving variables: {e}")
        return {"status": "error", "message": "Failed to save variables"}

















@app.post("/generate-code")
def generate_code(request: NarrativeRequest):
  
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        max_attempts = 2
        refinedQuery =ai_refine_user_query(request.narrative)
        intermediate = generate_IEC_JSON(refinedQuery)

        response = validator(json.loads(intermediate))

        while response[0] is False and max_attempts > 0:
            print("Regeneration...",max_attempts)

            max_attempts -= 1
            intermediate = regenerate_IEC_JSON(
                refinedQuery,
                response[1],
                intermediate
            )
            response = validator(json.loads(intermediate))

        if response[0] is False:
            raise HTTPException(status_code=400, detail=response[1])
        code = generator(json.loads(intermediate))

        if request.user_id:
            chat_entry = {
                "id": str(ObjectId()),
                "query": 'Your : '+request.narrative+'\n RefineQuery : '+refinedQuery,
                "generatedCode": code,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            variables_collection.update_one(
                {"id": request.user_id},
                {"$push": {"chatHistory": chat_entry}},
                
            )

        return {"status": "ok", "code": code , "interCode":intermediate,  "Refine": refinedQuery}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error generating code: {e}")
        raise HTTPException(status_code=500, detail="Code generation failed")




@app.post("/regenerate-code")
def regenerate_code(request: RegenerateRequest):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        max_attempts = 2
        refinedQuery =ai_refine_user_query(request.feedback)

        intermediate = regenerate_IEC_JSON(
                request.query,
                refinedQuery,
                request.intermediateCode    
)       
        print( intermediate);

        response = validator(json.loads(intermediate))
        print(response);
        # try regeneration if validation fails
        while response[0] is False and max_attempts > 0:
            print("Regeneration...",max_attempts)
            max_attempts -= 1
            intermediate = regenerate_IEC_JSON(
                refinedQuery,
                response[1],
                intermediate
            )
            response = validator(json.loads(intermediate))

        if response[0] is False:
            raise HTTPException(status_code=400, detail=response[1])
        code = generator(json.loads(intermediate))
        # print(request.feedback,"\n\n\n", code ,"\n\n")
        
        if request.user_id:
            chat_entry = {
                "id": str(ObjectId()),
                "query": 'Your : '+request.narrative+'\n RefineQuery : '+refinedQuery,
                "generatedCode": code,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            variables_collection.update_one(
                {"id": request.user_id},
                {"$push": {"chatHistory": chat_entry}},
            )

        return {"status": "ok", "code": code , "interCode":intermediate , "Refine": refinedQuery}

    except HTTPException:
        raise
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
            return {"status": "ok", "chatHistory": []}  # empty if user not found
        return {"status": "ok", "chatHistory": user.get("chatHistory", [])}
    except Exception as e:
        print(f"Error fetching chat history: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch chat history")


# ----------------- SAVE CHAT ENTRY -----------------

@app.post("/save-chat-entry")
def save_chat_entry(request: ChatEntryRequest):
    if not client:
        return {"status": "error", "message": "Database connection failed"}
    
    try:
        new_entry = {
            "query": request.query,
            "response": request.response,
            "feedback": request.feedback,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        print(request.user_id, new_entry)  # Debugging line
        # Check if user exists first
        user = variables_collection.find_one({"id": request.user_id})
        if not user:
            return {"status": "error", "message": "User not found"}

        # Append to user's chat history
        result = variables_collection.update_one(
            {"id": request.user_id},
            {"$push": {"chatHistory": new_entry}},
        )

        print("Update Result:", result.raw_result)  # Debugging line

        return {"status": "ok", "chatEntry": new_entry}

    except Exception as e:
        print(f"Error saving chat entry: {e}")
        return {"status": "error", "message": "Failed to save chat entry"}
    


    
# ----------------- DELETE CHAT ENTRY -----------------
@app.delete("/delete-chat/{chat_id}")
def delete_chat_entry(chat_id: str):
    if not client:
        raise HTTPException(status_code=500, detail="Database connection failed")
    try:
        # find user having this chat_id
        result = variables_collection.update_many(
            {},
            {"$pull": {"chatHistory": {"id": chat_id}}}
        )
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Chat entry not found")
        return {"status": "ok", "message": "Chat entry deleted"}
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error deleting chat entry: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete chat entry")

