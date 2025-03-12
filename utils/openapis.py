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
    # Step 1: Replace `/` and other separators with a space
    parts = re.sub(r'[\/_]', ' ', input_string)
    
    # Step 2: Handle camel case by splitting uppercase letters followed by lowercase letters
    parts = re.sub(r'([a-z])([A-Z])', r'\1 \2', parts)
    parts = re.sub(r'([A-Z])([A-Z][a-z])', r'\1 \2', parts)  # Split consecutive uppercase words properly

    # Step 3: Handle digits and letters separation
    parts = re.sub(r'(\d+)([a-zA-Z])', r'\1 \2', parts)
    parts = re.sub(r'([a-zA-Z])(\d+)', r'\1 \2', parts)
    
    # Step 4: Normalize spaces (collapse multiple spaces into one)
    parts = re.sub(r'\s+', ' ', parts.strip())
    
    # Step 5: Convert to lowercase and join with '-'
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
            print(f"file_path: {file_path}")
            relative_path = os.path.relpath(file_path, repo_root)
            last_commit_date = repo.git.log('-1', '--format=%cI', '--', relative_path)
            parent_folder = os.path.basename(os.path.dirname(file_path))
            
            with open(file_path, 'r') as f:
                raw_spec = yaml.safe_load(f)
                
            reduced_spec = reduce_openapi_spec(raw_spec,last_commit_date, relative_path, dereference=True)
            print("--------------------------------")
            print(f"adding specs for {parent_folder}")
            print(f"Title: {reduced_spec.title}")
            print(f"Description: {reduced_spec.description}")
            #first create a document with the title and description
            doc = Document(page_content=reduced_spec.title + "\n" + str(reduced_spec.description))
            doc.metadata["id"] = parent_folder
            doc.metadata["source"] = "docs/api/"+kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(reduced_spec.title)
            doc.metadata["last_commit_date"] = last_commit_date
            # doc.metadata["operation_path"] = kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(reduced_spec.title)
            reduced_specs.append(doc)
            
            for endpoint in reduced_spec.endpoints:
                print("--------------------------------")
                print(f"endpoint: {endpoint[0]}")
                doc = Document(page_content= endpoint[0] + " " + str(endpoint[3]))
                doc.metadata["operationId"] = endpoint[2]
                doc.metadata["id"] = endpoint[0]
                doc.metadata["source"] = relative_path
                doc.metadata["api_name"] = parent_folder
                doc.metadata["last_commit_date"] = last_commit_date
                if endpoint[2]:  # Only add operation_path if endpoint[2] exists
                    # doc.metadata["operation_path"] = "docs/api/"+ kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(endpoint[2])
                    doc.metadata["source"] = "docs/api/"+ kebab_case_lodash_like(parent_folder)+"/"+kebab_case_lodash_like(endpoint[2])
                reduced_specs.append(doc)
                
                #print(doc)
        return reduced_specs
    
    except Exception as e:
        print(f"Error searching for YAML files in {directory}: {str(e)}")
        return None
    

    
def count_tokens(text):
    encoding = tiktoken.encoding_for_model("text-embedding-3-small")
    tokens = encoding.encode(text)
    return len(tokens)

def format_endpoint_docs_text(endpoint_docs):
    """Format endpoint documentation in a human-readable text format."""
    text_parts = []
    
    # Add description
    if 'description' in endpoint_docs:
        text_parts.append(f"Description: {endpoint_docs['description']}\n")
    
    # Add parameters
    if 'parameters' in endpoint_docs and endpoint_docs['parameters']:
        text_parts.append("Parameters:")
        for param in endpoint_docs['parameters']:
            text_parts.append(f"  name: {param.get('name', 'N/A')}")
            text_parts.append(f"  in: {param.get('in', 'N/A')}")
            text_parts.append(f"  required: {param.get('required', 'undefined')}")
            text_parts.append(f"  description: {param.get('description', 'N/A')}\n")
    
    # Add request body
    if 'requestBody' in endpoint_docs:
        text_parts.append("Request Body:")
        request_body = endpoint_docs['requestBody']
        
        # Add description if present
        if 'description' in request_body:
            text_parts.append(f"  Description: {request_body['description']}")
        
        if 'content' in request_body:
            for content_type, content in request_body['content'].items():
                text_parts.append(f"  Content Type: {content_type}")
                
                # Handle schema if present
                if 'schema' in content:
                    schema = content['schema']
                    if 'type' in schema:
                        text_parts.append(f"  Type: {schema['type']}")
                    if 'properties' in schema:
                        text_parts.append("  Properties:")
                        for prop_name, prop_details in schema['properties'].items():
                            text_parts.append(f"    {prop_name}:")
                            for key, value in prop_details.items():
                                text_parts.append(f"      {key}: {value}")
                
                # Handle examples
                if 'example' in content:
                    text_parts.append("\nExample:")
                    text_parts.append(yaml.dump(content['example'], default_flow_style=False, indent=2))
                elif 'examples' in content:
                    text_parts.append("\nExamples:")
                    for example_name, example in content['examples'].items():
                        text_parts.append(f"\n{example_name}:")
                        if 'value' in example:
                            text_parts.append(yaml.dump(example['value'], default_flow_style=False, indent=2))
    
    return "\n".join(text_parts)



