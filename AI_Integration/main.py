import os
import glob
from langchain_groq import ChatGroq
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.prompts import ChatPromptTemplate
from langchain.chains import RetrievalQA
from dotenv import load_dotenv 
import Prompts



# ---------------------------------
#     Get credientials Env
# ---------------------------------


load_dotenv()
llm = ChatGroq(
    groq_api_key=os.environ["GROQ_API_KEY2"],
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


    template = Prompts.Generate_System_Instruction         # //  get the System Instruction

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
    

    template = Prompts.ReGenerate_System_Instruction

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

# # This will attempt to fix the typo in the function name ("AddNubers" -> "AddNumbers").
# # print(regenerate_IEC_JSON(user_query, issue, generated_code))