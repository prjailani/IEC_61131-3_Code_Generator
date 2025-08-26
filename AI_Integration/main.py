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
folder_path = "./kb"
docs = load_docs_from_path(folder_path)

if not docs:
    raise ValueError("No documents found in KB folder!")

# ---- 3. Create embeddings + vector store ----
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
vectorstore = FAISS.from_texts(docs, embedding=embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

# ---- 4. Build QA chain with JSON output ----
template = """You are an IEC 61131 Structured Text to JSON translator.
Use the following context from reference docs:
{context}

User request: {question}

Return only a valid JSON object that follows this schema:
{{
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

⚠️ Important: 
- Always output **pure JSON**, nothing else.
- Keys must be exactly: "program", "name", "declarations", "statements", "type", "condition", "then", "else", "target", "expression", "datatype".
- Do not explain the code, just return JSON.
"""

prompt = ChatPromptTemplate.from_template(template)

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    retriever=retriever,
    chain_type_kwargs={"prompt": prompt},
)

# ---- 5. Run example query ----
user_query =  input("Ask  : ")
query = "Generate logic: "+user_query
result = qa_chain.invoke({"query": query})

print("Generated JSON:\n", result["result"])
