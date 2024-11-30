import os
import glob
import yaml
from utils.reduce_openapi_spec import reduce_openapi_spec

def load_yaml_files(directory):
    try:
        yaml_files = glob.glob(os.path.join(directory, '**', '*.yaml'), recursive=True) 
        print(f"Found {len(yaml_files)} YAML files in {directory}")
        reduced_specs = {}
        for file_path in yaml_files:
            print(file_path)
            #file_size = os.path.getsize(file_path)
            #print(f"Size: {file_size} bytes")
            with open(file_path, 'r') as f:
                raw_spec = yaml.safe_load(f)
            reduced_spec = reduce_openapi_spec(raw_spec, dereference=True)
            # reduced_spec_str = yaml.dump(reduced_spec)
            # print(f"Reduced spec size: {len(reduced_spec_str)} bytes")
            # print("--------------------------------")
            print(f"title: {reduced_spec.title}")
            # print(f"description: {len(reduced_spec.description) if reduced_spec.description else 0} characters\n")
            #print(f"servers: {reduced_spec.servers}\n")
            for endpoint in reduced_spec.endpoints:
                print(f"endpoint: {endpoint[0]}")
            #     print(f"description: {len(endpoint[1]) if endpoint[1] else 0} characters")
            #     print(f"docs: {len(str(endpoint[2])) if endpoint[2] else 0} characters\n")
            reduced_specs[reduced_spec.title] = reduced_spec
        return reduced_specs
    except Exception as e:
        print(f"Error searching for YAML files in {directory}: {str(e)}")
        return []

