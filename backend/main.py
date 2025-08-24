from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from settings import settings
from pydantic import BaseModel
import random

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


def validator(intermediate):
    return True

@app.post("/generate-code")
def generateCode(body:NarrativeRequest):
    #params = {"key" :settings.key,q:message }
    # requests.request(setting.api_link, params = params)   
    

    
    print(body.narrative)
    messages = ["Structured Text naale Namma Dhan","Naa dhan da Leo...Leo doss...",
                "Nee enna thetre la enna padam vena ottu, aana rohini nu varappo thala dhan..!!!"
                ,"Sooriyan kitta kooda modhalam, Aana Coolie kitta modhave koodadhu","Trump phone panni Coolie ku rohini fdfs ticket irukkuma nu kekkuran","Narikki puduven","Anandh uh... ","Dummy Baava"]
    return {"status":"ok","code":random.choice(messages)}
