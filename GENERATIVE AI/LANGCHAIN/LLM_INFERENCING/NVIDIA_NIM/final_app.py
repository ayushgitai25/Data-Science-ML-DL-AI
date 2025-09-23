import streamlit as st
import os
from langchain_nvidia_ai_endpoints import NVIDIAEmbeddings, ChatNVIDIA
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import create_retrieval_chain
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
import time  # Import time module for timing functionality
import datetime  # Import datetime for timestamps

load_dotenv()

os.environ["NVIDIA_API_KEY"] = os.getenv("NVIDIA_API_KEY")

llm = ChatNVIDIA(model="meta/llama-3.3-70b-instruct")

def get_current_timestamp():
    """Get the current timestamp in a readable format."""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def vector_embeddings():
    if "vectors" not in st.session_state:
        start_time = time.time()  # Start timing the embedding process
        
        # Use path relative to this script's location
        script_dir = os.path.dirname(__file__)
        directory = os.path.join(script_dir, "us_census")
        
        # Ensure the directory exists
        if not os.path.exists(directory):
            os.makedirs(directory)
            st.warning(f"Created directory '{directory}' since it didn't exist. Please add PDFs to it and try again.")
            return  # Exit if we just created it (no files yet)
        
        st.session_state.embeddings = NVIDIAEmbeddings()
        st.session_state.loader = PyPDFDirectoryLoader(directory)  # Read PDFs from this directory
        st.session_state.docs = st.session_state.loader.load()
        
        # Check if documents were loaded
        if not st.session_state.docs:
            st.error(f"No documents found in '{directory}'. Please add PDFs and try again.")
            return  # Exit the function if no docs
        
        st.session_state.text_splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=50)
        st.session_state.final_documents = st.session_state.text_splitter.split_documents(st.session_state.docs[:50])
        
        # Check if final_documents is not empty
        if not st.session_state.final_documents:
            st.error("No document chunks created after splitting. The documents may be empty or too short.")
            return  # Exit if no chunks
        
        st.session_state.vectors = FAISS.from_documents(st.session_state.final_documents, st.session_state.embeddings)
        
        end_time = time.time()  # End timing
        elapsed_time = end_time - start_time
        st.write(f"Embedding completed at {get_current_timestamp()}. Time taken: {elapsed_time:.2f} seconds.")

st.title("NVIDIA NIM DEMO")

prompt = ChatPromptTemplate.from_template(
    """
    Answer the following questions based on the provided context only.
    Please provide the most accurate response based on the question.
    <context>
    {context}
    </context>

    Question: {input}
    """
)

prompt1 = st.text_input("Enter your Question from Documents:")

if st.button("Document Embedding"):
    vector_embeddings()
    st.write("FAISS Vector Store DB is Ready using NVIDIA Embedding.")

if prompt1:
    if "vectors" not in st.session_state:
        st.error("Please embed the documents first by clicking the 'Document Embedding' button.")
    else:
        start_time = time.time()  # Start timing the query process
        
        document_chain = create_stuff_documents_chain(llm, prompt)
        retriever = st.session_state.vectors.as_retriever()
        retrieval_chain = create_retrieval_chain(retriever, document_chain)
        
        # Perform the query
        result = retrieval_chain.invoke({"input": prompt1})
        
        # Extract context and answer from the result
        answer = result["answer"] if "answer" in result else "No answer found."
        context = result.get("context", "Context not available.")
        
        end_time = time.time()  # End timing
        elapsed_time = end_time - start_time
        
        st.write("Answer:", answer)
        st.write("Context:", context)
        st.write(f"Query processed at {get_current_timestamp()}. Time taken: {elapsed_time:.2f} seconds.")
