import os
import glob
from langchain_community.document_loaders import TextLoader, UnstructuredMarkdownLoader
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
import git


def load_md_files(temp_repo_path, directory_to_load):
    """
    This function loads Markdown files from a specified directory within a temporary repository path.
    
    :param temp_repo_path: The `temp_repo_path` parameter is the path to the temporary repository where
    the markdown files will be loaded
    :param directory_to_load: The `load_md_files` function is used to load Markdown files from a
    specific directory within a temporary repository path. The `temp_repo_path` parameter specifies the
    path to the temporary repository, and the `directory_to_load` parameter specifies the directory
    within the repository from which Markdown files should be loaded
    
    :return: A list of Document objects, each representing a loaded Markdown file. 
    The Document objects also include the last commit date and source path for each file
    
    """
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
        #print(f"Loading {file_path}")
        loader = TextLoader(file_path)
        file_documents = loader.load()
        for doc in file_documents:
            relative_path = os.path.relpath(file_path, temp_repo_path)
            doc.metadata["source"] = relative_path
            doc.metadata["last_commit_date"] = last_commit_date
            documents.append(doc)
        
    return documents



def calculate_chunk_ids(chunks):
    """
    This function calculates and adds the IDs for the given list of chunks.
    The IDs are used to identify the chunks in the vector database.
    This will create IDs like "docs/commerce-manager/index.mdx:2 
    
    :param chunks: A list of chunk sizes or lengths
    :return: A list of chunk IDs
    """

    last_page_id = None
    current_chunk_index = 0

    for chunk in chunks:
        
        # print(chunk.page_content)
        
        source = chunk.metadata.get("source")
        # last_commit_date = chunk.metadata.get("last_commit_date") 
        current_page_id = f"{source}"

        # If the page ID is the same as the last one, increment the index.
        if current_page_id == last_page_id:
            current_chunk_index += 1
        else:
            current_chunk_index = 0
            # print all the metadata, just for the first time
            print(chunk.metadata)

        # Calculate the chunk ID.
        chunk_id = f"{current_page_id}:{current_chunk_index}"
        last_page_id = current_page_id

        # Add it to the page meta-data.
        chunk.metadata["id"] = chunk_id
        # chunk.metadata["last_commit_date"] = last_commit_date
        
    return chunks

def split_documents(chunk_size, documents: list[Document]):
    print(f"Splitting {len(documents)} documents into chunks of {chunk_size} characters")
    # for doc in documents:
    #     print(f"Document: {doc.page_content}")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_size * 0.1,
        length_function=len,
        is_separator_regex=False,
    )
    return text_splitter.split_documents(documents)
