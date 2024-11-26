import os
import glob
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import git
import shutil
from git import RemoteProgress
import time

def load_md_files(temp_repo_path, directory_to_load):
    # Find all .md and .mdx files in the directory and subdirectories
    directory =os.path.join(temp_repo_path, directory_to_load)
    #directory = os.path.expanduser(directory)  # Expand ~ to full home directory path
    print(f"Searching in directory: {os.path.abspath(directory)}")
    
    md_files = glob.glob(os.path.join(directory, '**', '*.md*'), recursive=True) 
    print(f"in {directory} found {len(md_files)} .md files")
    
    documents = []
    try:
        repo = git.Repo(directory, search_parent_directories=True)
        repo_root = repo.working_tree_dir  # Get the root directory of the repo
        print(f"Found git repository at: {repo.git_dir}")
    except git.exc.InvalidGitRepositoryError:
        print(f"Warning: No git repository found for {directory}")
        repo = None
    
    for file_path in md_files:
        # Get the last commit date for the file using git log (only if repo exists)
        last_commit_date = None
        if repo:
            try:
                # Convert absolute path to relative path from repo root
                relative_path = os.path.relpath(file_path, repo_root)
                last_commit_date = repo.git.log('-1', '--format=%cI', '--', relative_path)
            except git.exc.GitCommandError as e:
                print(f"Error getting git log: {e}")
                print(f"No git history found for {file_path}")
        
        # Load each .md file using LangChain's TextLoader
        print(f"Loading {file_path}")
        loader = TextLoader(file_path)
        file_documents = loader.load()
        for doc in file_documents:
            relative_path = os.path.relpath(file_path, temp_repo_path)
            doc.metadata["source"] = relative_path
            doc.metadata["last_commit_date"] = last_commit_date
            documents.append(doc)
        
    return documents

def clone_repo(git_repo_url, temp_repo_path="~/temp_repo"):
    
    class Progress(RemoteProgress):
        def update(self, op_code, cur_count, max_count=None, message=''):
            print(f'\rProgress: {cur_count}/{max_count} {message}', end='')
    
    try:
        temp_repo_path = os.path.expanduser(temp_repo_path)
        # Clean up directory if it exists
        if os.path.exists(temp_repo_path):
            print(f"Cleaning up existing directory: {temp_repo_path}")
            shutil.rmtree(temp_repo_path)
        print(f"Cloning {git_repo_url} into {temp_repo_path}")
        git.Repo.clone_from(
            git_repo_url, 
            temp_repo_path,
            progress=Progress(),
            depth=1  # Shallow clone for faster download
        )

        print(f"\n✅ Repository cloned successfully in {temp_repo_path}")
        
    except Exception as e:
        print(f"❌ Clone failed: {e}")
        return False

    return True

def split_documents(chunk_size, documents: list[Document]):
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_size * 0.1,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)

def delete_repo(temp_repo_path):
    if os.path.exists(temp_repo_path):
        print(f"Cleaning up existing directory: {temp_repo_path}")
        shutil.rmtree(temp_repo_path)

#TEMPORARY
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python documents.py <repository_url> [output_directory]")
        sys.exit(1)
        
    repo_url = sys.argv[1]
    subdir = sys.argv[2] if len(sys.argv) > 2 else None
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "docs"
    
    #download_md_files(repo_url, subdir, output_dir)