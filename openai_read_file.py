from langchain.document_loaders import CSVLoader
from langchain.indexes import VectorstoreIndexCreator
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
import pandas as pd
import os
os.environ["OPENAI_API_KEY"] = "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"

# Load the dataset
# link to download data I used: https://www.kaggle.com/datasets/ashishraut64/indian-startups-top-300?resource=download
loader = CSVLoader(file_path='Startups1.csv')

# Create an index using the loaded documents
index_creator = VectorstoreIndexCreator()
docsearch = index_creator.from_loaders([loader])

# Create a question-answering chain using the index
chain = RetrievalQA.from_chain_type(llm=OpenAI(), chain_type="stuff", retriever=docsearch.vectorstore.as_retriever(), input_key="question")

# Pass a query to the data
query = "Who is the founder of BimaPe?"
response = chain({"question": query})
print(response['result'])