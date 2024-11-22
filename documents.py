import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document

MD_DATA_PATH = "./data_md/docs/commerce-manager"

def get_md_files(directory):
    # Find all .md files in the directory and subdirectories
    md_files = glob.glob(os.path.join(directory, '**', '*.md*'), recursive=True) #TODO: change to include .mdx files
    print(f"Found {len(md_files)} .md files")
    documents = []
    for file_path in md_files:
        # Load each .md file using LangChain's TextLoader
        print(f"Loading {file_path}")
        loader = TextLoader(file_path)
        documents.extend(loader.load())
    
    return documents