import os
import argparse
from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from pymongo import MongoClient
from langchain_mongodb import MongoDBAtlasVectorSearch
from utils.documents import load_md_files, split_documents, calculate_chunk_ids
# from utils.git import clone_repo, delete_repo

# Global variable declarations
OPENAI_API_KEY = None
MONGODB_ATLAS_CLUSTER_URI = None
DB_NAME = None
DOC_SITE = None
COLLECTION_NAME = None

"""
This function takes a list of documents with IDs and adds them to a vector database
IF the document has a newer last_commit_date than the one in the DB, it will update the document.
Otherwise, it will skip the document.
"""
def add_to_vectorDB(chunks_with_ids: list[Document]):
    atlas_collection, db = connectToMongo()
    
    existing_items_dict = get_existing_items(atlas_collection)  
    
    to_delete_chunks, new_chunks = compare_records(chunks_with_ids, existing_items_dict)
    
    # Handle deletions if any
    if len(to_delete_chunks):
        print(f"🗑️ Deleting outdated documents: {len(to_delete_chunks)}")
        # print(f"to_delete_chunks: {to_delete_chunks}")
        atlas_collection.delete_many({"id": {"$in": to_delete_chunks}})
    else:
        print("✅ No documents to delete")
    
    # Handle additions if any
    if len(new_chunks):
        print(f"👉 Adding new/updated documents: {len(new_chunks)}")
        new_chunk_ids = [chunk.metadata["id"] for chunk in new_chunks]
        #print(f"new_chunk_ids: {new_chunk_ids}")
        db.add_documents(new_chunks, ids=new_chunk_ids)
        #print(f"chunks added: {new_chunks}")
    else:
        print("✅ No new documents to add")
        
    return

def get_existing_items(atlas_collection):
    """
    Get id, last_commit_date, and source for all existing documents
    """
    existing_items = atlas_collection.find({}, {"_id": 0, "id": 1, "last_commit_date": 1, "source": 1})
    existing_items = list(existing_items)
    
    # Create dictionaries for existing items
    existing_items_dict = {item["id"]: {"last_commit_date": item["last_commit_date"], "source": item["source"]} 
                            for item in existing_items}
    return existing_items_dict

def compare_records(chunks_with_ids: list[Document], existing_items_dict: dict):
    """
    Track new/updated documents (chunks) and documents to delete
    """
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
            # Get the last commit date from the first item in the array
            # (assuming all items for the same source have the same date)
            existing_date = source_to_existing[chunk_source][0]["last_commit_date"]
            
            if chunk_date > existing_date:
                print(f"UPDATING: md file {chunk_source} date: {chunk_date} is more recent")
                # Add to new chunks and mark existing ones for deletion
                new_chunks.append(chunk)
                print(f"to_delete_chunks: {chunk.metadata['id']}")
                to_delete_chunks.append(chunk.metadata["id"])
            
        else:
            # Completely new source
            new_chunks.append(chunk)
    
    return to_delete_chunks, new_chunks
    
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
    global OPENAI_API_KEY, MONGODB_ATLAS_CLUSTER_URI, DB_NAME, DOC_SITE, COLLECTION_NAME
    
    load_dotenv(override=True)
    
    parser = argparse.ArgumentParser(description="Load MD files from Elastic Path Docs site in a MongoDB Atlas Cluster")
    parser.add_argument("--doc_site", type=str, required=True, help="The name of the docs site, EPCC or EPSM")
    parser.add_argument("--repo_location", type=str, required=True, help="The location of the repo to load")
    parser.add_argument("--base_url", type=str, required=False, help="The url of the documentation site")
    parser.add_argument("--chunk_size", type=int, default=3000, help="The size of the chunks")
    args = parser.parse_args()
    
    if args.doc_site == "EPCC":
        COLLECTION_NAME = os.getenv("COLLECTION_NAME_EPCC")
        print(f"Setting COLLECTION_NAME for EPCC: {COLLECTION_NAME}")
        directories_to_load = ["docs/commerce-manager", 
                               "docs/composer", 
                               "docs/developer-tools", 
                               "docs/payments", 
                               "docs/partials",
                               "guides"]
    elif args.doc_site == "EPSM":
        COLLECTION_NAME = os.getenv("COLLECTION_NAME_EPSM")
        print(f"Setting COLLECTION_NAME for EPSM: {COLLECTION_NAME}")
        if args.repo_location.endswith("extension-framework"):
            directories_to_load = ["website/versioned_docs/version-1.3.x"]
        else:
            directories_to_load = ["website/versioned_docs/version-8.6.x"]
        
    else:
        print(f"Invalid DOC_SITE: {args.doc_site}")
        return


    print("\nDebug: Environment variables after load_dotenv:")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    print(f"OPENAI_API_KEY exists: {OPENAI_API_KEY is not None}")
    
    MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
    print(f"MONGODB_ATLAS_CLUSTER_URI exists: {MONGODB_ATLAS_CLUSTER_URI is not None}")
    
    DB_NAME = os.getenv("DB_NAME")
    print(f"DB_NAME exists: {DB_NAME is not None}")
    
    print(f"COLLECTION_NAME: {COLLECTION_NAME}")
    print(f"COLLECTION_NAME exists: {COLLECTION_NAME is not None}")

    # Add error messages to assertions for better debugging
    assert OPENAI_API_KEY is not None, f"OPENAI_API_KEY is not set in environment: {os.getenv('OPENAI_API_KEY')}"
    assert MONGODB_ATLAS_CLUSTER_URI is not None, f"MONGODB_ATLAS_CLUSTER_URI is not set in environment: {os.getenv('MONGODB_ATLAS_CLUSTER_URI')}"
    assert DB_NAME is not None, f"DB_NAME is not set in environment: {os.getenv('DB_NAME')}"
    assert COLLECTION_NAME is not None, f"COLLECTION_NAME is not set in environment. COLLECTION_NAME_EPCC: {os.getenv('COLLECTION_NAME_EPCC')}, COLLECTION_NAME_EPSM: {os.getenv('COLLECTION_NAME_EPSM')}"
    

    temp_repo_path = os.path.expanduser(args.repo_location)
    
    for directory in directories_to_load:
        print(f"Processing MD files from repo for {directory} directory")
        if args.doc_site == "EPSM":
            documents = load_md_files(temp_repo_path, directory, args.base_url)
        else:
            documents = load_md_files(temp_repo_path, directory)
        chunks = split_documents(args.chunk_size, documents)
        chunks_with_ids = calculate_chunk_ids(chunks)
        add_to_vectorDB(chunks_with_ids)
    


if __name__ == "__main__":
    main()