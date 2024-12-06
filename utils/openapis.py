import os
import glob
import yaml
from utils.reduce_openapi_spec import reduce_openapi_spec
from langchain_core.documents import Document
import git
import tiktoken
# from caseconverter import kebabcase
import re

def kebab_case_lodash_like(input_string):
    # Replace `/` with space, then split words, numbers, and special cases
    parts = re.sub(r'/', ' ', input_string)  # Replace `/` with space
    parts = re.sub(r'([a-z])([A-Z])', r'\1 \2', parts)  # Split camel case
    parts = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', parts)  # Split digits from letters
    parts = re.sub(r'([a-zA-Z])(\d+)', r'\1 \2', parts)  # Split letters from digits
    
    # Replace multiple spaces with single space
    parts = re.sub(r'\s+', ' ', parts)
    
    # Convert to lowercase and join with '-'
    return '-'.join(parts.lower().split())

def load_yaml_files(directory):
    """
    This function loads YAML files from a specified directory.
    
    :param directory: The `directory` parameter in the `load_yaml_files` function is a string that
    represents the path to a directory where YAML files are located
    
    :return: A dictionary of ReducedOpenAPISpec objects, each representing a loaded YAML file.
    """
    try:
        yaml_files = glob.glob(os.path.join(directory, '**', '*.yaml'), recursive=True) 
        print(f"Found {len(yaml_files)} YAML files in {directory}")
        
        # initialize the git repo
        repo = git.Repo(directory, search_parent_directories=True)
        if not repo:
            print(f"No git repository found for {directory}")
            return None
        repo_root = repo.working_tree_dir  # Get the root directory of the repo
        
        # I want to return a list of documents
        reduced_specs = []
        for file_path in yaml_files:
            
            relative_path = os.path.relpath(file_path, repo_root)
            last_commit_date = repo.git.log('-1', '--format=%cI', '--', relative_path)
            parent_folder = os.path.basename(os.path.dirname(file_path))
            
            with open(file_path, 'r') as f:
                raw_spec = yaml.safe_load(f)
                
            reduced_spec = reduce_openapi_spec(raw_spec,last_commit_date, relative_path, dereference=True)
            print("--------------------------------")
            print(f"adding specs for {parent_folder}")
            print(f"first: {reduced_spec.title}")
            #first create a document with the title and description
            doc = Document(page_content=reduced_spec.title + "\n" + str(reduced_spec.description))
            doc.metadata["id"] = parent_folder
            doc.metadata["source"] = "docs/api/"+kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(reduced_spec.title)
            doc.metadata["last_commit_date"] = last_commit_date
            # doc.metadata["operation_path"] = kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(reduced_spec.title)
            reduced_specs.append(doc)
            
            # print("--------------------------------")
            # print(f"title: {reduced_spec.title}")
            # print(f"description: {len(reduced_spec.description) if reduced_spec.description else 0} characters \
            #     and {count_tokens(reduced_spec.description) if reduced_spec.description else 0} tokens")
            # print(f"servers: {reduced_spec.servers}\n")
            for endpoint in reduced_spec.endpoints:
                # print(f"""endpoint: {endpoint[0]} \
                #     description: {len(endpoint[1]) if endpoint[1] else 0} characters \
                #     docs: {len(str(endpoint[2])) if endpoint[2] else 0} characters """)
                # if endpoint[0] == "GET /v2/carts/{cartID}":
                #     print(f"description: {endpoint[1]}")
                #     print(f"docs: {endpoint[2]}")
                # create a document for each endpoint
                doc = Document(page_content= endpoint[0] + " " + str(endpoint[3]))
                doc.metadata["id"] = endpoint[0]
                doc.metadata["source"] = relative_path
                doc.metadata["last_commit_date"] = last_commit_date
                if endpoint[2]:  # Only add operation_path if endpoint[2] exists
                    # doc.metadata["operation_path"] = "docs/api/"+ kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(endpoint[2])
                    doc.metadata["source"] = "docs/api/"+ kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(endpoint[2])
                reduced_specs.append(doc)
                # print(f"added {endpoint[0]}")
        return reduced_specs
    
    except Exception as e:
        print(f"Error searching for YAML files in {directory}: {str(e)}")
        return None
    

    
def count_tokens(text):
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = encoding.encode(text)
    return len(tokens)

