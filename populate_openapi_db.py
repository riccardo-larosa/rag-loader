# from utils.yaml_loader import YamlLoader
import yaml
import os
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from utils.openapis import load_yaml_files

# Global variable declarations
OPENAI_API_KEY = None
MONGODB_ATLAS_CLUSTER_URI = None
DB_NAME = None
COLLECTION_NAME_OPENAPI = None

def add_to_vectorDB(api_specs: dict):
    atlas_collection, db = connectToMongo()
    for spec in api_specs:
        db.add_documents(spec)
    

def connectToMongo():
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small") 
    client = MongoClient(MONGODB_ATLAS_CLUSTER_URI)
    db_name = DB_NAME 
    collection_name = COLLECTION_NAME_OPENAPI
    atlas_collection = client[db_name][collection_name]
    vector_search_index = "vector_index"

    # Create a MongoDBAtlasVectorSearch object
    db = MongoDBAtlasVectorSearch.from_connection_string(
        MONGODB_ATLAS_CLUSTER_URI,
        db_name + "." + collection_name,
        embeddings, #OpenAIEmbeddings(disallowed_special=(), model="text-embedding-3-small") ,
        index_name = vector_search_index
    )
    return atlas_collection, db

def main():
    global OPENAI_API_KEY, MONGODB_ATLAS_CLUSTER_URI, DB_NAME, COLLECTION_NAME_OPENAPI
    
    load_dotenv(override=True)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
    DB_NAME = os.getenv("DB_NAME")
    COLLECTION_NAME_OPENAPI = os.getenv("COLLECTION_NAME_OPENAPI")
    print(f"DB_NAME: {DB_NAME}")
    print(f"COLLECTION_NAME_OPENAPI: {COLLECTION_NAME_OPENAPI}")
    
    
    repo_path = os.path.expanduser("~/tmp_ep_dev/openapispecs")
    api_specs = load_yaml_files(repo_path)
    add_to_vectorDB(api_specs)
    
    # print(api_specs)

if __name__ == "__main__":
    main()