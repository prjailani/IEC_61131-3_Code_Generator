import os
import glob
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv 
import re
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
# import Prompts
# from Prompts import ReGenerate_System_Instruction, Generate_System_Instruction ,QueryRefineInstruction

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.multi_query import MultiQueryRetriever



# ---------------------------------
#     Get credientials Env
# ---------------------------------


load_dotenv()
llm = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY"],
    model=os.environ.get("GROQ_MODEL_NAME", "llama-3.3-70b-versatile"),
)







ReGenerate_System_Instruction =  """
    You are an IEC 61131 Structured Text to JSON translator. You are a bug fixer.
    Here you work on already generated code, but there are some issues. You need to fix them and return a new, corrected version of the JSON code.
    Use the following context from reference docs:
    {context}

    User request: {question}

    Return only a valid JSON object that follows this schema.
    The top-level object can be a 'program', a 'functionBlock', or a 'function'.

    Example for a 'program':
    [{{
      "program": {{
        "name": "<string>",
        "declarations": [
          {{ "type": "VAR", "name": "<string>", "datatype": "<string>" }}
        ],
        "statements": [
          {{
            "type": "if",
            "condition": "<condition-expression>",
            "then": [
              {{ "type": "assignment", "target": "<var>", "expression": "<value>" }}
            ]
          }}
        ]
      }}
    }}]

    Example for a 'functionBlock':
    [{{
      "functionBlock": {{
        "name": "<string>",
        "inputs": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "outputs": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "locals": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "body": [
          {{ "type": "assignment", "target": "<var>", "expression": "<value>" }}
        ]
      }}
    }}]

    Example for a 'function':
    [{{
      "function": {{
        "name": "<string>",
        "returnType": "<string>",
        "inputs": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "body": [
          {{ "type": "return", "expression": "<value>" }}
        ]
      }}
    }}]
    
    ⚠️ Important: 
      -  RAG information  in json  data:
             -- [
                 "MetaData": "details about that device function ",
                 "dataType": "datatype that device use",
                 "deviceName": "fixed variable name for that device operate",
                 "range": "if numerical there will provide  min - max range "
              ],
              ** note :   you need to  give the name of the variable as give in "DeviceName"   it is case-sensitive
                  time  is special  formate that need to be Give in : [
                     T#5S
                     TIME#100MS
                     T#2H30M10S500MS
                     D#2025-09-02
                     DATE#2025-01-01
                     T#-1S
                     DT#2025-09-02-12:30:00
                     DATE_AND_TIME#2025-09-02-23:59:59.999
                     ]   *** this are the valid  time  formate use this like  formate as bestone 
    - NOTE : IF  NO DEVICENAME FIND FOR USER QUERY [think by you is that device match context or not if else "target ; "NO_DEVICE_FOUND"], NOT MATCH TO RAG DEVICENAME THEN RETURN JSON format INSIDE "NO_DEVICE_FOUND : TRUE"  nothing more

    - Always output **pure JSON**, nothing else.
    - The top-level object must be one of: "program", "functionBlock", or "function".
    - Do not explain the code, just return JSON. Correct the same JSON code without any errors or issues. Fix the bug.
    - When multiple programs, function blocks, or functions are needed, return an array of objects enclosed in [].
    - When handling with conditional statements, use '=' not '==' for equals condition, do not use ternary operator, use AND instead of & or &&, use OR instead of | or ||, use NOT instead of !.
    """








Generate_System_Instruction = """You are an IEC 61131 Structured Text to JSON translator.
    Use the following context from reference docs:
    {context}

    User request: {question}

    Return only a valid JSON object that follows this schema.
    The top-level object can be a 'program', a 'functionBlock', or a 'function'.

    Example for a 'program':
    [{{
      "program": {{
        "name": "<string>",
        "declarations": [
          {{ "type": "VAR", "name": "<string>", "datatype": "<string>" }}
        ],
        "statements": [
          {{
            "type": "if",
            "condition": "< condition-expression>",
            "then": [
              {{ "type": "assignment", "target": "<var>", "expression": "<value>" }}
            ]
          }}
        ]
      }}
    }}]

    Example for a 'functionBlock':
    [{{
      "functionBlock": {{
        "name": "<string>",
        "inputs": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "outputs": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "locals": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "body": [
          {{ "type": "assignment", "target": "<var>", "expression": "<value>" }}
        ]
      }}
    }}]

    Example for a 'function':
    [{{
      "function": {{
        "name": "<string>",
        "returnType": "<string>",
        "inputs": [ {{ "name": "<string>", "datatype": "<string>" }} ],
        "body": [
          {{ "type": "return", "expression": "<value>" }}
        ]
      }}
    }}]
    
    ⚠️ Important: 
     -  RAG information  provide  in json  data:
             -- " [
                 "metadata": "details about that device function ",
                 "dataType": "datatype that device use",
                 "deviceName": "fixed variable name for that device operate",
                 "range": "if numerical there will provide  min - max range "
              ]
              ** note :   you need to  give the name of the variable as give in "DeviceName"   it is case-sensitive   and 
                     time  is special  formate that need to be Give in : [
                     T#5S
                     TIME#100MS
                     T#2H30M10S500MS
                     D#2025-09-02
                     DATE#2025-01-01
                     T#-1S
                     DT#2025-09-02-12:30:00
                     DATE_AND_TIME#2025-09-02-23:59:59.999
                     ]   *** this are the valid  time  formate use this like  formate as bestone 
    - NOTE : IF  NO DEVICENAME FIND FOR USER QUERY [think by you is that device match context or not if else "target ; "NO_DEVICE_FOUND"], NOT MATCH TO RAG DEVICENAME THEN RETURN JSON format INSIDE "NO_DEVICE_FOUND : TRUE"  nothing more
    - Always output **pure JSON**, nothing else.
    - The top-level object must be one of: "program", "functionBlock", or "function".
    - Do not explain the code, just return JSON.
    - When multiple programs, function blocks, or functions are needed, return an array of objects enclosed in [].
    - When handling with conditional statements, use '=' not '==' for equals condition, do not use ternary operator, use AND instead of & or &&, use OR instead of | or ||, use NOT instead of !.
    """




QueryRefineInstruction="""
     You are a Grammer checker.
    - Take the raw user request below.
    - Rewrite it into a correct grammer and spelling corectly  only for general  words[ if  some word is diffent/doubt leave as orginal.]
    - Preserve all details, numbers, times, and device names.
    - Do not add information that wasn’t given.
    - Fix grammar and structure lightly so it’s understandable.
    - Output only the rewritten instruction, nothing else.

    User request: {user_input}
    """

















def refine_user_query(user_input: str) -> str:
  
    if not user_input or not user_input.strip():
        return "Please provide a valid request."

    cleaned = re.sub(r'\s+', ' ', user_input.strip())

    cleaned = re.sub(r'[,;]+', ', ', cleaned)
    cleaned = re.sub(r'\.+', '.', cleaned)

    cleaned = cleaned[0].upper() + cleaned[1:] if cleaned else cleaned

  
    rewritten_prompt = (
        f"user request: {cleaned}."
    )

    return rewritten_prompt



def ai_refine_user_query(user_input: str) -> str:
   
    template = QueryRefineInstruction

    prompt = ChatPromptTemplate.from_template(template)

    chain = prompt | llm  
    result = chain.invoke({"user_input": user_input})
    
    if hasattr(result, "content"):
        refined = result.content
    elif hasattr(result, "text"):
        refined = result.text
    else:
        refined = str(result)
    print("\n\nRefine prompt Done  ...\n User query : ", refined)

    return refined.strip()




def load_docs_from_path(folder_path: str):
    
    all_files = glob.glob(os.path.join(folder_path, "**/*.*"), recursive=True)
    docs = []
    for f in all_files:
        if f.lower().endswith((".json", ".txt")):
            with open(f, "r", encoding="utf-8") as infile:
                text = infile.read()
                docs.append({"text": text, "source": os.path.basename(f)})
    return docs

# ================================================================================================================================================
#                                              RAG Part ( Rag the data  form Knowledge Base KB)
# ================================================================================================================================================

retriever =None

def Rag():
    global retriever 

    script_directory = os.path.dirname(__file__)
    folder_path = os.path.join(script_directory, "kb")
    raw_docs = load_docs_from_path(folder_path)
    
    if not raw_docs:
        raise ValueError("No documents found in KB folder!")
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,     # Adjust as needed
        chunk_overlap=150,   # Helps preserve context across chunks
        separators=["\n\n", "\n", " ", ""]
    )
    
    chunked_texts = []
    for d in raw_docs:
        chunks = text_splitter.split_text(d["text"])
        for i, chunk in enumerate(chunks):
            chunked_texts.append({
                "text": chunk,
                "metadata": {
                    "source": d["source"],
                    "chunk_id": i
                }
            })
    
    
    
    
    
    
    
    embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    
    texts = [c["text"] for c in chunked_texts]
    metadatas = [c["metadata"] for c in chunked_texts]
    
    vectorstore = FAISS.from_texts(texts, embedding=embeddings, metadatas=metadatas)
    
    base_retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
    retriever= MultiQueryRetriever.from_llm(retriever=base_retriever, llm=llm)
    print("\nRag done successfuly....")

Rag()

# print(retriever)


# ================================================================================================================================================
#                                               Generate IEC_intermediate code
# ================================================================================================================================================


def generate_IEC_JSON(user_query):


    template = Generate_System_Instruction       

    prompt = ChatPromptTemplate.from_template(template)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
    )

    # print("\n\n\nHere  is the  qu_chain \n\n", qa_chain, " \n\n")
    print("\nGeneration Done  ...\n")

    # print(qa_chain)

    query = "Generate logic: " + user_query
    result = qa_chain.invoke({"query": query})

    return result["result"]




# ================================================================================================================================================
#                                               re- Generate IEC_intermediate code
# ================================================================================================================================================





def regenerate_IEC_JSON(user_query, issue, generated_code):
    

    template = ReGenerate_System_Instruction

    prompt = ChatPromptTemplate.from_template(template)

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=retriever,
        chain_type_kwargs={"prompt": prompt},
    )
    print("\nReGeneration Done  ...\n")
    query = "previous user query: " + user_query + "\n\n issue in exiting code : " + issue + " \n\n Already Generated_code : \n" + generated_code
    result = qa_chain.invoke({"query": query})

    return result["result"]



# print(ai_refine_user_query("turn on motor at 6 mornign and  off at  2pm then on the kitchen lgight at 3 pm" ))
# print(refine_user_query("turn on motor at 6 mornign and  off at  2pm then on the kitchen lgight at 3 pm"))

































 
#==================================================================================================================

#                                             testing Area 

#==================================================================================================================

# user_query = "add two numbers"
# generated_code = """
# [{
#   "function": {
#     "name": "AddNubers", 
#     "returnType": "INT",
#     "inputs": [
#       { "name": "a", "datatype": "INT" },
#       { "name": "b", "datatype": "INT" }
#     ],
#     "body": [
#       { "type": "return", "expression": "a+b" }
#     ]
#   }
# },
# {
#   "program": {
#     "name": "FunctionCallExample",
#     "declarations": [
#       { "type": "VAR", "name": "a", "datatype": "INT" },
#       { "type": "VAR", "name": "b", "datatype": "INT" },
#       { "type": "VAR", "name": "result", "datatype": "INT" }
#     ],
#     "statements": [
#       {
#         "type": "functionCall",
#         "name": "AddNumbers",
#         "arguments": ["a", "b"]
#       },
#       {
#         "type": "assignment",
#         "target": "result",
#         "expression": "AddNumbers(a, b)"
#       }
#     ]
#   }
# }]
# """
# issue = "error: Function 'AddNumbers' not defined"

# # Example of how to call the updated functions:
# # This will generate the correct JSON for both the function and program.



# print(generate_IEC_JSON("Turn on the master betrooms AC'S at 8pm  and set cool at 30  then  close  door"))

# # print(regenerate_IEC_JSON(user_query, issue, generated_code))