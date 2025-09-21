from fastapi import FastAPI
from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from langserve import add_routes

import os
from dotenv import load_dotenv
load_dotenv()

os.environ['GROQ_API_KEY'] = os.getenv('GROQ_API_KEY')
os.environ['LANGCHAIN_API_KEY'] = os.getenv('LANGCHAIN_API_KEY') ## for LangSmith Tracking
os.environ['LANGSMITH_TRACING_V2'] = "true"
os.environ['LANGCHAIN_PROJECT'] = os.getenv('LANGCHAIN_PROJECT')

llm_groq = ChatGroq(
  model= "Gemma2-9b-It"
)

from langchain_core.prompts import ChatPromptTemplate
from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

generic_template = "Translate the following into {language}:"

prompt = ChatPromptTemplate.from_messages(
  [
    SystemMessagePromptTemplate.from_template(generic_template),
    HumanMessagePromptTemplate.from_template("{text}")
  ]
)

output_parser = StrOutputParser()

chain = prompt | llm_groq | output_parser

## App definition
app = FastAPI(
  title= "LangChain Server", version= "1.0", description= "A simple API server using Langchain runnable interfaces"
)
## Add chain routes FOR LANGSERVE
add_routes(
  app,
  chain,  ## chain we created : chain = prompt | llm_groq | output_parser
  path= "/chain"
)

if __name__ == "__main__":
  import uvicorn
  uvicorn.run(app, host= "127.0.0.1", port= 8000)