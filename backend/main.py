"""
IEC 61131-3 Code Generator Backend API

FastAPI application entry point.
Converts natural language to IEC 61131-3 Structured Text code.
"""

import logging
import sys
import os
import json
import re
from contextlib import asynccontextmanager
from typing import List, Optional
from pathlib import Path

from dotenv import load_dotenv

# Load .env from parent directory (project root)
root_env = Path(__file__).parent.parent / ".env"
load_dotenv(root_env)

from fastapi import FastAPI, HTTPException, Request, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Add parent directory for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import core modules
from core import settings, init_database, close_database, get_collection, db_manager
from models import (
    NarrativeRequest, 
    Variable, 
    SaveVariablesRequest, 
    GenerateResponse,
    HealthResponse,
)
from services import (
    generate_code as generate_code_service,
    CodeGenerationError,
    variables_service,
    VariablesServiceError,
)

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown."""
    # Startup
    logger.info("Starting IEC 61131-3 Code Generator API")
    init_database()
    yield
    # Shutdown
    close_database()
    logger.info("Shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="IEC 61131-3 Code Generator API",
    description="Convert natural language to IEC 61131-3 Structured Text",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"status": "error", "message": "An internal server error occurred"}
    )


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.get("/", response_model=HealthResponse)
@app.get("/home", response_model=HealthResponse)
def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="ok",
        message="IEC 61131-3 Code Generator API",
        database_connected=db_manager.is_connected
    )


# ============================================================================
# Code Generation Endpoints
# ============================================================================

@app.post("/generate-code", response_model=GenerateResponse)
def generate_code(body: NarrativeRequest):
    """
    Generate IEC 61131-3 Structured Text code from natural language.
    
    The process involves:
    1. AI generates intermediate JSON representation
    2. Validator checks the JSON for errors
    3. If errors found, regeneration is attempted (up to 2 times)
    4. Generator converts valid JSON to Structured Text
    """
    try:
        code = generate_code_service(body.narrative)
        logger.info("Code generation successful")
        return GenerateResponse(status="ok", code=code)
        
    except CodeGenerationError as e:
        if e.is_validation_error:
            raise HTTPException(status_code=400, detail=str(e))
        raise HTTPException(status_code=500, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error in code generation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred")


# ============================================================================
# Variables Management Endpoints
# ============================================================================

@app.get("/get-variables")
def get_variables():
    """Get all variables from the database."""
    try:
        variables = variables_service.get_all()
        return {"status": "ok", "variables": variables}
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error getting variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve variables")


@app.post("/save-variables")
def save_variables(body: SaveVariablesRequest):
    """
    Synchronize variables with the database.
    Deletes removed items, updates existing, and adds new ones.
    """
    try:
        result = variables_service.save_all(body.variables)
        return result
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error saving variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to save variables")


@app.post("/upload-variables-json")
async def upload_variables_json(file: UploadFile = File(...)):
    """Upload variables from a JSON file."""
    # Validate file type
    if not file.filename.endswith('.json'):
        raise HTTPException(status_code=400, detail="Only JSON files are allowed")
    
    # Read and check size
    contents = await file.read()
    if len(contents) > settings.max_upload_size:
        max_mb = settings.max_upload_size // 1024 // 1024
        raise HTTPException(status_code=400, detail=f"File too large. Maximum size is {max_mb}MB")
    
    # Parse JSON
    try:
        variables_list = json.loads(contents.decode("utf-8"))
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON file format")
    
    # Validate format
    if not isinstance(variables_list, list):
        raise HTTPException(status_code=400, detail="JSON must be an array of variables")
    
    for i, var in enumerate(variables_list):
        if not isinstance(var, dict):
            raise HTTPException(status_code=400, detail=f"Item {i} is not a valid object")
        if 'deviceName' not in var or 'dataType' not in var:
            raise HTTPException(status_code=400, detail=f"Item {i} missing required fields")
    
    # Upload
    try:
        result = variables_service.upload_from_list(variables_list)
        return result
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error uploading variables: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to upload variables")


@app.delete("/remove-duplicates")
def remove_duplicates():
    """Remove duplicate variables (case-insensitive by deviceName)."""
    try:
        result = variables_service.remove_duplicates()
        return result
        
    except VariablesServiceError as e:
        raise HTTPException(status_code=503, detail=str(e))
        
    except Exception as e:
        logger.error(f"Error removing duplicates: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to remove duplicates")


# ============================================================================
# Application Info
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
