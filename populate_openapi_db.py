# from utils.yaml_loader import YamlLoader
import yaml
import os
import argparse
from dotenv import load_dotenv
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from utils.openapis import load_yaml_files
from langchain.schema import Document

# Global variable declarations
OPENAI_API_KEY = None
MONGODB_ATLAS_CLUSTER_URI = None
DB_NAME = None
COLLECTION_NAME_OPENAPI = None

def add_to_vectorDB(documents: list[Document]):
    atlas_collection, db = connectToMongo()
    existing_items_dict = get_existing_items(atlas_collection)
    
    to_delete_chunks, new_chunks = compare_records(documents, existing_items_dict)
    if len(to_delete_chunks):
        print(f"🗑️ Deleting outdated documents: {len(to_delete_chunks)}")
        atlas_collection.delete_many({"id": {"$in": to_delete_chunks}})
    else:
        print("✅ No documents to delete")
        
    if len(new_chunks):
        print(f"👉 Adding new/updated documents: {len(new_chunks)}")
        db.add_documents(new_chunks)
    else:
        print("✅ No new documents to add")
    
    return

def compare_records(documents: list[Document], existing_items_dict: dict):
    to_delete_chunks = []
    new_chunks = []
    
    print("🔄 Comparing records")
    #check doc.metadata["id"] in existing_items_dict
    for doc in documents:
        if doc.metadata["id"] in existing_items_dict:
            #print(f"document {doc.metadata['id']} already exists")
            # check if last_commit_date is more recent
            if doc.metadata["last_commit_date"] > existing_items_dict[doc.metadata["id"]]["last_commit_date"]:
                #print(f"document {doc.metadata['id']} is more recent")
                new_chunks.append(doc)
                to_delete_chunks.append(doc.metadata["id"])
            #else:
                #print(f"document {doc.metadata['id']} does not need to be updated")
        else:
            # Completely new document
            #print(f"document {doc.metadata['id']} is new")
            new_chunks.append(doc)
    return to_delete_chunks, new_chunks

def get_existing_items(atlas_collection):
    existing_items = atlas_collection.find({}, {"_id": 0, "id": 1, "last_commit_date": 1, "source": 1})
    existing_items = list(existing_items)
    existing_items_dict = {item["id"]: {"last_commit_date": item["last_commit_date"], "source": item["source"]} 
                            for item in existing_items}
    return existing_items_dict

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
    
    parser = argparse.ArgumentParser(description="Load OpenAPI specs from Elastic Path Docs site in a MongoDB Atlas Cluster")
    parser.add_argument("--openapi_dir_location", type=str, required=True, help="The location of the OpenAPI specs to load")
    args = parser.parse_args()
    
    repo_path = os.path.expanduser(args.openapi_dir_location)
    api_specs = load_yaml_files(repo_path)
    #add_to_vectorDB(api_specs)
    


if __name__ == "__main__":
    main()