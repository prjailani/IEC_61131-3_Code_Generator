from fastapi import FastAPI, Body
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

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

@app.get("/home")
def root():
    return {"vazhthu":"Vanakkam"}

class NarrativeRequest(BaseModel):
    narrative: str


@app.post("/generate-code")
def generateCode(body:NarrativeRequest):
    intermediate = generate_IEC_JSON(body.narrative)
    response = validator(json.loads(intermediate))

    while(response[0] == False):
        intermediate = regenerate_IEC_JSON(body.narrative ,response[1],intermediate)
        response = validator(json.loads(intermediate))
    
    code = generator(json.loads(intermediate))
    
    return {"status":"ok","code":code}
