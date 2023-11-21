# This file is used to recursively load pdfs documents, split into chunks, and load the data with embeddings into pinecone
# 


# load the necessary environment variables
import os
from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv()) # read local .env file

OPENAI_API_KEY = os.environ['OPENAI_API_KEY']
PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
PINCECONED_ENVIRONMENT = os.environ['PINECONE_ENVIRONMENT']
PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]


#################################################################################################
def load_pdf_docs(path, chunksize=1000, overlap=100):
    """Load documents will recursively load a all the pdfs in a given directory path 
    and return a list of documents. 

    Args:
        chunksize (int, optional): _description_. Defaults to 1000.
        overlap (int, optional): _description_. Defaults to 100.

    Returns:
        _type_: _description_
    """    

    from langchain.document_loaders import PyPDFLoader
    from langchain.document_loaders import DirectoryLoader
    
    # load all pdfs in the directory
    # Each document will be a list of pages
    loader = DirectoryLoader(
        r"pdfs", 
        use_multithreading=True,
        loader_cls=PyPDFLoader,
        show_progress=True,
        recursive=True
    )
    pages = loader.load() # this returns a list of pages as Document types
    return pages

def load_text_docs(path, chunksize=1000, overlap=100):
    """ Load all text files from a given directory

    Args:
        path (str): This is the subfolder path - be sure that this is relative to where you start the program
        chunksize (int, optional): Size of text chunks. Defaults to 1000.
        overlap (int, optional): Overlap between text chunks. Defaults to 100.

    Returns:
        list(Document): Returns a list of LangChain Document types
    """
    documents = [] # look up text loader in LangChain documentation

    return documents # return a list of chunks of text

def load_html_docs(path, chunksize=1000, overlap=100):
    """ Load all text files from a given directory

    Args:
        path (str): This is the subfolder path - be sure that this is relative to where you start the program
        chunksize (int, optional): Size of text chunks. Defaults to 1000.
        overlap (int, optional): Overlap between text chunks. Defaults to 100.

    Returns:
        list(Document): Returns a list of LangChain Document types
    """
    documents = [] # look up html loader in LangChain documentation

    return documents # return a list of chunks of text

def load_json_docs(path, chunksize=1000, overlap=100):
    """ Load all text files from a given directory

    Args:
        path (str): This is the subfolder path - be sure that this is relative to where you start the program
        chunksize (int, optional): Size of text chunks. Defaults to 1000.
        overlap (int, optional): Overlap between text chunks. Defaults to 100.

    Returns:
        list(Document): Returns a list of LangChain Document types
    """
    
    import langchain
    from langchain.document_loaders.json_loader import JSONLoader
    from langchain.document_loaders import DirectoryLoader, TextLoader
        # load all pdfs in the directory
        # Each document will be a list of pages
    loader = DirectoryLoader(
        r"./json", 
        use_multithreading=True,
        glob='**/*.json',
        loader_cls=TextLoader,
        show_progress=True,
        recursive=True
    )
    
    documents = loader.load() # look up json loader in LangChain documentation

    return documents # return a list of chunks of text


#################################################################################################
def split_docs_into_chunks(docs, chunksize=1000, overlap=50):
    """Accepts a list of Documents (see LangChain Document type/schema) and splits them 
    into a list of smaller documents. 

    Args:
        docs (list[Document]): List of LangChain Document types
        chunksize (int, optional): What is the largest page_content size per document. Defaults to 1000.
        overlap (int, optional): How much overlap between chunks. Defaults to 100.

    Returns:
        list[Document]: List of LangChain Document types that are smaller than the original documents
    """
    
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # create a text splitter
    text_splitter = RecursiveCharacterTextSplitter(
       # Set a really small chunk size, just to show.
        chunk_size = chunksize,
        chunk_overlap  = overlap
    )        
    
    # return a list of documents that result from splitting the original documents    
    return text_splitter.split_documents(docs)

#################################################################################################
def get_pinecone_index(dimensions=1536, metric='cosine'):
    """Used for free pinecone service which allows only one index
    Connects to pinecone and creates an index if one does not exist. 
    Deletes all indexes if one does exist.
    
    Requires Environmnet Variables to bet set:
        PINECONE_API_KEY
        PINCECONED_ENV
    
    Args:
        dimensions (int, optional): Dimensions of the vectors. Defaults to 1536.
        metric (str, optional): Distrance metrics to calculate similarity. Defaults to 'cosine'.
    """
    import pinecone
    import time
    import os
    from dotenv import load_dotenv, find_dotenv
    _ = load_dotenv(find_dotenv())  
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    PINECONE_API_KEY = os.environ['PINECONE_API_KEY']
    PINCECONED_ENVIRONMENT = os.environ['PINECONE_ENVIRONMENT']
    

    # initialize pinecone client to connect to account
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINCECONED_ENVIRONMENT)
    
    # for free account, you can only have one index
    # Here we delete all indexes...
    index_list = pinecone.list_indexes()
    while len(index_list) > 0:
        pinecone.delete_index(index_list[-1])
        index_list = pinecone.list_indexes()
        
    if PINECONE_INDEX_NAME not in pinecone.list_indexes():
        pinecone.create_index(
            PINECONE_INDEX_NAME,
            dimension=1536,
            metric='cosine'
        )
        # wait for index to finish initialization
        while not pinecone.describe_index(PINECONE_INDEX_NAME).status['ready']:
            time.sleep(1)
    
    # return a pinecone index connection
    return pinecone.Index(PINECONE_INDEX_NAME)

#################################################################################################
def load_embeddings_into_pinecone(index, chunks):
    """Accepts an an open pinecone index and a list of documents (of type list[Docuement])

    Args:
        index (pinecode.index): Open index to Pinecone index
        chunks (list[Document]): List of LangChain Document types
    """
    from langchain.vectorstores import Pinecone
    from langchain.embeddings.openai import OpenAIEmbeddings
    import os
    from dotenv import load_dotenv, find_dotenv
    _ = load_dotenv(find_dotenv())   

    OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
    PINECONE_INDEX_NAME = os.environ["PINECONE_INDEX_NAME"]
    # load embeddings into pinecone
    Pinecone.from_documents(
        chunks, 
        embedding=OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-ada-002"),
        index_name=PINECONE_INDEX_NAME
    ) 

#################################################################################################
#################################################################################################
def main():
    """ Main function to load documents, split into chunks, and load into pinecone"""
    
    # load docuemnts, split into chunks, and embed
    print(">>>>>>> Loading documents...")
    pdf_docs = load_pdf_docs("pdfs") 
    text_docs = load_text_docs("texts")
    json_docs = load_json_docs("json")
    html_docs = load_html_docs("htmls")
    
    # split documents into chunks
    print(">>>>>>> Splitting documents into chunks...")
    docs = pdf_docs + text_docs + json_docs + html_docs
    chunks = split_docs_into_chunks(docs, chunksize=1000, overlap=50)
    
    # create pinecone index
    print(">>>>>>> Creating pinecone index...")
    index = get_pinecone_index()
        
    # load embeddings into pinecone
    print(">>>>>>> Loading embeddings into pinecone...")
    load_embeddings_into_pinecone(index, chunks) # embeddings are calculated in the function
    
    # print finished message
    print("All finished!")
        

#################################################################################################
if __name__ == "__main__":
    main()