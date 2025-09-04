import os
import glob
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv 
# import Prompts



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
# ---------------------------------
#     Get credientials Env
# ---------------------------------


load_dotenv()
llm = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY3"],
    model=os.environ.get("GROQ_MODEL_NAME", "llama-3.1-70b-versatile"),
)




# ================================================================================================================================================
#                                              RAG Part ( Rag the data  form Knowledge Base KB)
# ================================================================================================================================================



def load_docs_from_path(folder_path: str):
    all_files = glob.glob(os.path.join(folder_path, "**/*.json"), recursive=True)
    docs = []
    for f in all_files:
        with open(f, "r", encoding="utf-8") as infile:
            docs.append(infile.read())
    return docs


script_directory = os.path.dirname(__file__)
folder_path = os.path.join(script_directory, "kb")
docs = load_docs_from_path(folder_path)

if not docs:
    raise ValueError("No documents found in KB folder!")

embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_texts(docs, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})



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

    query = "previous user query: " + user_query + "\n\n issue in exiting code : " + issue + " \n\n Already Generated_code : \n" + generated_code
    result = qa_chain.invoke({"query": query})

    return result["result"]

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