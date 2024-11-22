import os
import argparse
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_community.embeddings import OpenAIEmbeddings
from pymongo import MongoClient, MongoDBAtlasVectorSearch

load_dotenv( override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#VECTOR_DB = os.getenv("VECTOR_DB")
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

def calculate_chunk_ids(chunks):

    # This will create IDs like "data/monopoly.pdf:6:2"
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

def add_to_vectorDB(chunks: list[Document], vector_db, vectordb_path):
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small") 
    print("Using embeddings: ", embeddings)
    
    print("🔗 Connecting to MongoDB Atlas")
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
        OpenAIEmbeddings(disallowed_special=(), model="text-embedding-3-small") ,
        index_name = vector_search_index
    )
    
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
        

def main():
    
    parser = argparse.ArgumentParser(description="Load MD files from Elastic Path Docs site in a MongoDB Atlas Cluster")
    parser.add_argument("--data_path", type=str, help="The path to the data directory.")
    parser.add_argument("--reset", type=bool, help="Reset the database")
    args = parser.parse_args()
    if args.data_path:
        print(f"Processing MD files from {args.data_path} directory")

    if args.reset:
        print("Resetting the database")

if __name__ == "__main__":
    main()