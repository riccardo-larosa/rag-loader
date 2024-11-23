import os
import glob
from langchain_community.document_loaders import TextLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import git
import shutil
from git import RemoteProgress
import time

def get_md_files(directory):
    # Find all .md and .mdx files in the directory and subdirectories
    md_files = glob.glob(os.path.join(directory, '**', '*.md*'), recursive=True) 
    print(f"Found {len(md_files)} .md files")
    documents = []
    for file_path in md_files:
        # Load each .md file using LangChain's TextLoader
        print(f"Loading {file_path}")
        loader = TextLoader(file_path)
        documents.extend(loader.load())
    
    return documents

def download_md_files(git_repo_url, subdirectory=None, directory_to_clone_to="docs"):
    class Progress(RemoteProgress):
        def update(self, op_code, cur_count, max_count=None, message=''):
            print(f'\rProgress: {cur_count}/{max_count} {message}', end='')
    
    # Clean up directory if it exists
    if os.path.exists(directory_to_clone_to):
        print(f"Cleaning up existing directory: {directory_to_clone_to}")
        shutil.rmtree(directory_to_clone_to)
    
    try:
        temp_repo_path = "temp_repo" 
        print(f"Cloning {git_repo_url} into {directory_to_clone_to}")
        git.Repo.clone_from(
            git_repo_url, 
            temp_repo_path,
            progress=Progress(),
            depth=1  # Shallow clone for faster download
        )
        # Define source and destination paths for the subdirectory
        source_path = os.path.join(temp_repo_path, subdirectory)
        destination_path = os.path.abspath(directory_to_clone_to)

        # Copy the subdirectory to the destination
        if os.path.exists(source_path):
            shutil.copytree(source_path, destination_path)
            print(f"Subdirectory '{subdirectory}' copied to '{directory_to_clone_to}'.")
        else:
            print(f"Subdirectory '{subdirectory}' does not exist in the repository.")
        print("\n✅ Repository cloned successfully")
        
    except Exception as e:
        print(f"❌ Clone failed: {e}")
        return None
    
    finally:
        # Clean up the temporary repository
        if os.path.exists(temp_repo_path):
            shutil.rmtree(temp_repo_path)

    return directory_to_clone_to

def split_documents(chunk_size, documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_size * 0.1,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

#TEMPORARY
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python documents.py <repository_url> [output_directory]")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    subdir = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "docs"
    
    download_md_files(repo_url, subdir, output_dir)