import os
import glob

from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA

from dotenv  import load_dotenv

load_dotenv()
# ---- 1. Setup LLM (Groq) ----
llm = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY"],
    model=os.environ.get("GROQ_MODEL_NAME", "llama-3.1-70b-versatile"),
)

# ---- 2. Load docs from a folder ----
def load_docs_from_path(folder_path: str):
    all_files = glob.glob(os.path.join(folder_path, "**/*.txt"), recursive=True)
    docs = []
    for f in all_files:
        with open(f, "r", encoding="utf-8") as infile:
            docs.append(infile.read())
    return docs

# Example: put your knowledge docs in ./kb/

script_directory = os.path.dirname(__file__)
folder_path = os.path.join(script_directory, "kb")
docs = load_docs_from_path(folder_path)

if not docs:
    raise ValueError("No documents found in KB folder!")

# ---- 3. Create embeddings + vector store ----
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_texts(docs, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

def generate_IEC_JSON(user_query):
    # ---- 4. Build QA chain with JSON output ----
      template = """You are an IEC 61131 Structured Text to JSON translator.
      Use the following context from reference docs:
      {context}

      User request: {question}

      Return only a valid JSON object that follows this schema:
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
              ],
              "else": [
                {{ "type": "assignment", "target": "<var>", "expression": "<value>" }}
              ]
            }}
          ]
        }}
      }}
      ]

      ⚠️ Important: 
      - Always output **pure JSON**, nothing else.
      - Keys must be exactly: "program", "name", "declarations", "statements", "type", "condition", "then", "else", "target", "expression", "datatype".
      - Do not explain the code, just return JSON.
      - When multiple programs are needed, return an list of program objects enclosed in [].
      """

      prompt = ChatPromptTemplate.from_template(template)

      qa_chain = RetrievalQA.from_chain_type(
          llm=llm,
          retriever=retriever,
          chain_type_kwargs={"prompt": prompt},
      )

      query = "Generate logic: "+user_query
      result = qa_chain.invoke({"query": query})

      return result["result"]





def regenerate_IEC_JSON(user_query,  issue , generated_code) :
    # ---- 4. Build QA chain with JSON output ----
      template = """
      You are an IEC 61131 Structured Text to JSON translator. .Bug Fixer
      Here you work in the  already generated code  but there is some issues araised  you need to fix and return same  new version of JSON code 
      Use the following context from reference docs:
      {context}

      User request: {question}

      Already Generated code   : " generated_code  "

      Return only a valid JSON object that follows this schema:
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
              ],
              "else": [
                {{ "type": "assignment", "target": "<var>", "expression": "<value>" }}
              ]
            }}
          ]
        }}
      }}]

      ⚠️ Important: 
      - Always output **pure JSON**, nothing else.
      - Keys must be exactly: "program", "name", "declarations", "statements", "type", "condition", "then", "else", "target", "expression", "datatype".
      - Do not explain the code, just return JSON. correct the  same json code without any error/ issues. fix that bug
      - When multiple programs are needed, return an list of program objects enclosed in [].
      """

      prompt = ChatPromptTemplate.from_template(template)

      qa_chain = RetrievalQA.from_chain_type(
          llm=llm,
          retriever=retriever,
          chain_type_kwargs={"prompt": prompt},
      )

      query = "previous user query: "+user_query+"\n\n issue in exiting code : "+ issue  +" \n\n Already Generated_code : \n"+ generated_code
      result = qa_chain.invoke({"query": query})

      # print("Generated JSON:\n", result["result"])
      return result["result"]






#==================================================================================================================

#                                         testing Area 

#==================================================================================================================

# user =  input(" (-_-) Ask What you need  >>> ")


# user_query =  input("Ask  : ")
# user_query= "add two numbers"
# generated_code =  """
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
# }
# ,
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
# issue = "error : Function 'AddNumbers' not defined"

# # regenerate_IEC_JSON(user_query ,issue,generated_code)

# generate_IEC_JSON( user_query)