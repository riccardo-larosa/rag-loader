import os
import argparse
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from documents import get_md_files, split_documents

# Global variable declarations
OPENAI_API_KEY = None
MONGODB_ATLAS_CLUSTER_URI = None
DB_NAME = None
COLLECTION_NAME = None

def calculate_chunk_ids(chunks):

    # This will create IDs like "./data_md/docs/commerce-manager/index.mdx:6:2"
    # Page Source : Page Number : Chunk Index

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        source = chunk.metadata.get("source")
        page = chunk.metadata.get("page") #TODO: need to change this to base directory?
        current_page_id = f"{source}:{page}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id

    return chunks

def add_to_vectorDB(chunks: list[Document]):
    
    atlas_collection, db = connectToMongo()
    
    # Calculate Page IDs.
    chunks_with_ids = calculate_chunk_ids(chunks)
    # Add or Update the documents.
    existing_items = atlas_collection.find({}, {"_id": 0, "id": 1})
    existing_items = list(existing_items)
    existing_ids = {item["id"] for item in existing_items}
    # Only add documents that don't exist in the DB.
    new_chunks = []
    for chunk in chunks_with_ids:
        if chunk.metadata["id"] not in existing_ids:
            new_chunks.append(chunk)

    if len(new_chunks):
        print(f"👉 Adding new documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        #print(db)
        db.add_documents(new_chunks, ids=new_chunk_ids)
    else:
        print("✅ No new documents to add")

def connectToMongo():
    
    print("🔗 Connecting to MongoDB Atlas")
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY, model="text-embedding-3-small") 
    
    # Connect to your Atlas cluster
    client = MongoClient(MONGODB_ATLAS_CLUSTER_URI)
    db_name = DB_NAME 
    collection_name = COLLECTION_NAME 
    atlas_collection = client[db_name][collection_name]
    vector_search_index = "vector_index"

    # Create a MongoDBAtlasVectorSearch object
    db = MongoDBAtlasVectorSearch.from_connection_string(
        MONGODB_ATLAS_CLUSTER_URI,
        db_name + "." + collection_name,
        embeddings, #OpenAIEmbeddings(disallowed_special=(), model="text-embedding-3-small") ,
        index_name = vector_search_index
    )
    
    return atlas_collection,db
        

def main():
    global OPENAI_API_KEY, MONGODB_ATLAS_CLUSTER_URI, DB_NAME, COLLECTION_NAME
    
    load_dotenv(override=True)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
    DB_NAME = os.getenv("DB_NAME")
    COLLECTION_NAME = os.getenv("COLLECTION_NAME")
    print(f"Using OPENAI_API_KEY: {OPENAI_API_KEY}")
    print(f"Using MONGODB_ATLAS_CLUSTER_URI: {MONGODB_ATLAS_CLUSTER_URI}")
    print(f"Using DB_NAME: {DB_NAME}")
    print(f"Using COLLECTION_NAME: {COLLECTION_NAME}")
    
    parser = argparse.ArgumentParser(description="Load MD files from Elastic Path Docs site in a MongoDB Atlas Cluster")
    parser.add_argument("--data_path", type=str, help="The path to the data directory.")
    parser.add_argument("--reset", type=bool, help="Reset the database")
    args = parser.parse_args()
    

    
    if args.reset:
        print("Resetting the database: not implemented yet")
        db = connectToMongo()
        if db:
            print("Connected to MongoDB Atlas")
        else:
            print("Failed to connect to MongoDB Atlas")
            return
        
    if args.data_path:
        print(f"Processing MD files from {args.data_path} directory")    
        documents = get_md_files(args.data_path)
        chunks = split_documents(args.chunk_size, documents)
        add_to_vectorDB(chunks, None, None)

if __name__ == "__main__":
    main()