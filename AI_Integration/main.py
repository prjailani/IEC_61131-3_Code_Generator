"""
IEC 61131-3 AI Integration Module

Uses LangChain with Groq LLM and RAG (Retrieval Augmented Generation)
to convert natural language to IEC 61131-3 JSON intermediate representation.
"""

import os
import glob
import logging
from pathlib import Path
from typing import Optional

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.prompts import ChatPromptTemplate
from langchain_classic.chains import RetrievalQA
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# System instruction for regenerating code (bug fixing)
ReGenerate_System_Instruction = """
You are an IEC 61131-3 JSON bug fixer. Fix the validation errors in the provided code.

AVAILABLE DEVICES FROM DATABASE:
{context}

Error to fix: {question}

STRICT RULES:

1. **USE ONLY DEVICE NAMES FROM THE CONTEXT ABOVE**
   - The "deviceName" field contains the EXACT variable name to use
   - The "dataType" field contains the EXACT type to use
   - DO NOT invent names - use only what's in the context

2. **COMMON FIXES:**
   - "Variable X not found" → Use exact deviceName from context
   - "Type mismatch" → Use exact dataType from context
   - If the error says a variable doesn't exist, check context for correct spelling

3. **OUTPUT FORMAT** - Return ONLY valid JSON:

[{{
  "program": {{
    "name": "ProgramName",
    "declarations": [
      {{ "type": "VAR", "name": "EXACT_DEVICE_NAME", "datatype": "EXACT_DATATYPE" }}
    ],
    "statements": [
      {{ "type": "assignment", "target": "EXACT_DEVICE_NAME", "expression": "value" }}
    ]
  }}
}}]

4. **DATATYPE VALUES:**
   - BOOL: TRUE or FALSE
   - INT: integer values within the "range" field
   - REAL: decimal values

5. **IEC 61131-3 SYNTAX:**
   - Use '=' for equality
   - Use 'AND', 'OR', 'NOT'
   - No ternary operators

Output ONLY the corrected JSON, no explanations.
"""


# System instruction for generating new code
Generate_System_Instruction = """
You are an IEC 61131-3 Structured Text to JSON translator.

AVAILABLE DEVICES FROM DATABASE:
{context}

User request: {question}

STRICT RULES - YOU MUST FOLLOW THESE EXACTLY:

1. **USE ONLY DEVICE NAMES FROM THE CONTEXT ABOVE**
   - Extract "deviceName" values from the context JSON
   - Use these EXACT names (case-sensitive) in declarations and statements
   - DO NOT invent or guess variable names
   - If context shows {{"deviceName": "Fan", "dataType": "INT"}}, use "Fan" with type "INT"

2. **If no matching devices exist in context, return:**
   {{"NO_DEVICE_FOUND": true}}

3. **OUTPUT FORMAT** - Return ONLY valid JSON, no explanations:

For a 'program':
[{{
  "program": {{
    "name": "ProgramName",
    "declarations": [
      {{ "type": "VAR", "name": "EXACT_DEVICE_NAME_FROM_CONTEXT", "datatype": "EXACT_DATATYPE_FROM_CONTEXT" }}
    ],
    "statements": [
      {{ "type": "assignment", "target": "EXACT_DEVICE_NAME", "expression": "value" }}
    ]
  }}
}}]

4. **DATATYPE RULES:**
   - BOOL: Use TRUE or FALSE
   - INT/SINT/DINT: Use integer values (e.g., 1, 5, 100)
   - REAL: Use decimal values (e.g., 1.0, 25.5)
   - Check the "range" field for valid values

5. **IEC 61131-3 SYNTAX:**
   - Use '=' for equality (not '==')
   - Use 'AND', 'OR', 'NOT' (not &&, ||, !)
   - TIME literals: T#5S, T#100MS
   - No ternary operators

6. **TURNING ON/OFF:**
   - For BOOL: TRUE = on, FALSE = off
   - For INT: Use max value from range for "on", 0 for "off"
   - For INT with range "1-5": 5 = full on, 0 = off
"""


# Load environment variables
load_dotenv()


def get_api_key() -> str:
    """Get the Groq API key from environment variables."""
    # Try multiple possible key names
    for key_name in ["GROQ_API_KEY", "GROQ_API_KEY2", "GROQ_API_KEY3"]:
        api_key = os.environ.get(key_name)
        if api_key:
            return api_key
    
    raise ValueError(
        "No Groq API key found. Please set GROQ_API_KEY environment variable."
    )


def get_model_name() -> str:
    """Get the model name from environment variables."""
    return os.environ.get("GROQ_MODEL_NAME", "llama-3.1-70b-versatile")


def initialize_llm() -> ChatGroq:
    """Initialize the Groq LLM with error handling."""
    try:
        api_key = get_api_key()
        model_name = get_model_name()
        
        llm = ChatGroq(
            groq_api_key=api_key,
            model=model_name,
        )
        logger.info(f"LLM initialized with model: {model_name}")
        return llm
    except Exception as e:
        logger.error(f"Failed to initialize LLM: {e}")
        raise


def load_docs_from_path(folder_path: str) -> list:
    """
    Load all JSON documents from a folder for RAG.
    
    Args:
        folder_path: Path to the knowledge base folder
    
    Returns:
        List of document contents as strings
    """
    all_files = glob.glob(os.path.join(folder_path, "**/*.json"), recursive=True)
    docs = []
    
    for f in all_files:
        try:
            with open(f, "r", encoding="utf-8") as infile:
                content = infile.read()
                if content.strip():
                    docs.append(content)
        except Exception as e:
            logger.warning(f"Failed to read file {f}: {e}")
    
    return docs


def initialize_rag() -> tuple:
    """
    Initialize the RAG components (embeddings, vectorstore, retriever).
    
    Returns:
        Tuple of (vectorstore, retriever)
    """
    script_directory = Path(__file__).parent
    folder_path = script_directory / "kb"
    
    logger.info(f"Loading documents from: {folder_path}")
    docs = load_docs_from_path(str(folder_path))
    
    if not docs:
        logger.warning("No documents found in KB folder!")
        # Create a minimal document to avoid errors
        docs = ['{"info": "No device data available"}']
    
    logger.info(f"Loaded {len(docs)} documents for RAG")
    
    # Initialize embeddings
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2"
    )
    
    # Create vector store
    vectorstore = FAISS.from_texts(docs, embedding=embeddings)
    
    # Create retriever with configurable k
    retriever = vectorstore.as_retriever(
        search_kwargs={"k": int(os.environ.get("RAG_K", 3))}
    )
    
    return vectorstore, retriever


# Initialize components
try:
    llm = initialize_llm()
    vectorstore, retriever = initialize_rag()
except Exception as e:
    logger.error(f"Failed to initialize AI components: {e}")
    raise


def generate_IEC_JSON(user_query: str) -> str:
    """
    Generate IEC 61131-3 intermediate JSON from a natural language query.
    
    Args:
        user_query: Natural language description of the desired logic
    
    Returns:
        JSON string representing the intermediate code
    
    Raises:
        Exception: If generation fails
    """
    try:
        template = Generate_System_Instruction
        prompt = ChatPromptTemplate.from_template(template)
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
        )
        
        query = f"Generate logic: {user_query}"
        logger.info(f"Generating code for query: {user_query[:100]}...")
        
        result = qa_chain.invoke({"query": query})
        
        response = result.get("result", "")
        
        # Clean up response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        logger.info("Code generation completed")
        return response
        
    except Exception as e:
        logger.error(f"Error generating IEC JSON: {e}", exc_info=True)
        raise


def regenerate_IEC_JSON(user_query: str, issue: str, generated_code: str) -> str:
    """
    Regenerate IEC 61131-3 intermediate JSON to fix issues.
    
    Args:
        user_query: Original natural language description
        issue: Description of the validation error
        generated_code: Previously generated code with issues
    
    Returns:
        Fixed JSON string
    
    Raises:
        Exception: If regeneration fails
    """
    try:
        template = ReGenerate_System_Instruction
        prompt = ChatPromptTemplate.from_template(template)
        
        qa_chain = RetrievalQA.from_chain_type(
            llm=llm,
            retriever=retriever,
            chain_type_kwargs={"prompt": prompt},
        )
        
        query = (
            f"Previous user query: {user_query}\n\n"
            f"Issue in existing code: {issue}\n\n"
            f"Already generated code:\n{generated_code}"
        )
        
        logger.info(f"Regenerating code to fix: {issue[:100]}...")
        
        result = qa_chain.invoke({"query": query})
        
        response = result.get("result", "")
        
        # Clean up response
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        logger.info("Code regeneration completed")
        return response
        
    except Exception as e:
        logger.error(f"Error regenerating IEC JSON: {e}", exc_info=True)
        raise
