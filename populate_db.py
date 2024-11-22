import os
import argparse
from dotenv import load_dotenv


load_dotenv( override=True)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
#VECTOR_DB = os.getenv("VECTOR_DB")
MONGODB_ATLAS_CLUSTER_URI = os.getenv("MONGODB_ATLAS_CLUSTER_URI")
DB_NAME = os.getenv("DB_NAME")
COLLECTION_NAME = os.getenv("COLLECTION_NAME")

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