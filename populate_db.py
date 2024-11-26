import os
import argparse
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from documents import load_md_files, split_documents, clone_repo, delete_repo

# Global variable declarations
OPENAI_API_KEY = None
MONGODB_ATLAS_CLUSTER_URI = None
DB_NAME = None
COLLECTION_NAME = None

def calculate_chunk_ids(chunks):

    # This will create IDs like "docs/commerce-manager/index.mdx:2 
    # Page Source : Chunk Index and add the updated_date_time to the metadata

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        # print all the metadata
        print(chunk.metadata)
        source = chunk.metadata.get("source")
        last_commit_date = chunk.metadata.get("last_commit_date") 
        current_page_id = f"{source}"

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
        chunk.metadata["last_commit_date"] = last_commit_date
        


    return chunks

def add_to_vectorDB(chunks_with_ids: list[Document]):
    atlas_collection, db = connectToMongo()
    
    # Add or Update the documents.
    existing_items = atlas_collection.find({}, {"_id": 0, "id": 1, "last_commit_date": 1, "source": 1})
    existing_items = list(existing_items)
    
    # Create dictionaries for existing items
    existing_items_dict = {item["id"]: {"last_commit_date": item["last_commit_date"], "source": item["source"]} 
                            for item in existing_items}
    existing_ids = set(existing_items_dict.keys())
    
    # Track new/updated chunks and chunks to delete
    new_chunks = []
    to_delete_chunks = []
    
    # Group existing items by source
    source_to_existing = {}
    for item_id, item_data in existing_items_dict.items():
        source = item_data["source"]
        if source not in source_to_existing:
            source_to_existing[source] = []
        source_to_existing[source].append({
            "id": item_id,
            "last_commit_date": item_data["last_commit_date"]
        })
    print(f"source_to_existing has {len(source_to_existing)} sources")
    #print(f"source_to_existing: {source_to_existing}")
    
    # Process each chunk
    for chunk in chunks_with_ids:
        chunk_source = chunk.metadata["source"]
        chunk_date = chunk.metadata["last_commit_date"]
        
        if chunk_source in source_to_existing:
            # Source exists - check dates
            #print(f"chunk_source: {chunk_source}")
            
            # Get the last commit date from the first item in the array
            # (assuming all items for the same source have the same date)
            existing_date = source_to_existing[chunk_source][0]["last_commit_date"]
            
            if chunk_date > existing_date:
                print(f"UPDATING: md file {chunk_source} date: {chunk_date} is more recent")
                # Add to new chunks and mark existing ones for deletion
                new_chunks.append(chunk)
                print(f"to_delete_chunks: {chunk.metadata['id']}")
                #to_delete_chunks.extend(item["id"] for item in source_to_existing[chunk_source])
                to_delete_chunks.append(chunk.metadata["id"])
            else:
                #print(f"SKIPPING: md file {chunk_source} date: {chunk_date} is earlier than or equal to {existing_date}")
                # Skip this chunk as there's a newer version in the DB
                continue
            
        else:
            # Completely new source
            new_chunks.append(chunk)
    
    # Handle deletions if any
    if len(to_delete_chunks):
        print(f"🗑️ Deleting outdated documents: {len(to_delete_chunks)}")
        print(f"to_delete_chunks: {to_delete_chunks}")
        # TODO: Implement deletion logic here
        atlas_collection.delete_many({"id": {"$in": to_delete_chunks}})
    
    # Handle additions if any
    if len(new_chunks):
        print(f"👉 Adding new/updated documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        print(f"new_chunk_ids: {new_chunk_ids}")
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
    print(f"DB_NAME: {DB_NAME}")
    print(f"COLLECTION_NAME: {COLLECTION_NAME}")
    
    parser = argparse.ArgumentParser(description="Load MD files from Elastic Path Docs site in a MongoDB Atlas Cluster")
    #parser.add_argument("--data_path", type=str, help="The path to the data directory.")
    parser.add_argument("--reset", type=bool, help="Reset the database")
    parser.add_argument("--chunk_size", type=int, help="The size of the chunks")
    args = parser.parse_args()
    

    
    if args.reset:
        print("Resetting the database: not implemented yet")
        db = connectToMongo()
        if db:
            print("Connected to MongoDB Atlas")
        else:
            print("Failed to connect to MongoDB Atlas")
            return
        
    git_repo_url = "https://github.com/elasticpath/elasticpath-dev.git"
    temp_repo_path = os.path.expanduser("~/temp_repo")
    directory_to_load = "docs/carts-orders"
    print(f"Processing MD files from {git_repo_url} repo for {directory_to_load} directory")    
    #cloned = clone_repo(git_repo_url, temp_repo_path)
    #if not cloned:
    #    print("Failed to clone the repository")
    #    return
    
    documents = load_md_files(temp_repo_path, directory_to_load)
    chunks = split_documents(args.chunk_size, documents)
    chunks_with_ids = calculate_chunk_ids(chunks)
    add_to_vectorDB(chunks_with_ids)
    #cleanup
    #delete_repo(temp_repo_path)

if __name__ == "__main__":
    main()