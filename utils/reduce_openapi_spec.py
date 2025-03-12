"""
ORIGINAL AUTHOR: langchain_community.agent_toolkits.openapi.spec
Quick and dirty representation for OpenAPI specs."""

from dataclasses import dataclass
from typing import List, Tuple
import yaml

from langchain_core.utils.json_schema import dereference_refs


@dataclass(frozen=True)
class ReducedOpenAPISpec:
    """A reduced OpenAPI spec.

    This is a quick and dirty representation for OpenAPI specs.

    Parameters:
        servers: The servers in the spec.
        title: The title of the spec.
        description: The description of the spec.
        endpoints: The endpoints in the spec.
    """

    servers: List[dict]
    title: str
    description: str
    endpoints: List[Tuple[str, str, dict]]
    last_commit_date: str
    source: str


def reduce_openapi_spec(
    spec: dict, last_commit_date: str, source: str, dereference: bool = True
) -> ReducedOpenAPISpec:
    """Simplify/distill/minify a spec somehow.

    I want a smaller target for retrieval and (more importantly)
    I want smaller results from retrieval.
    I was hoping https://openapi.tools/ would have some useful bits
    to this end, but doesn't seem so.

    Args:
        spec: The OpenAPI spec.
        dereference: Whether to dereference the spec. Default is True.

    Returns:
        ReducedOpenAPISpec: The reduced OpenAPI spec.
    """
    # 1. Consider only get, post, patch, put, delete endpoints.
    endpoints = [
        (
            f"{operation_name.upper()} {route}",
            docs.get("description"),
            docs.get("operationId"),
            docs,
        )
        for route, operation in spec["paths"].items()
        for operation_name, docs in operation.items()
        if operation_name in ["get", "post", "patch", "put", "delete"]
    ]

    # 2. Replace any refs so that complete docs are retrieved.
    # Note: probably want to do this post-retrieval, it blows up the size of the spec.
    if dereference:
        endpoints = [
            (
                name,
                description,
                operationId,
                dereference_refs(
                    docs, full_schema=spec, skip_keys=["responses", "examples"]
                ),
            )
            for name, description, operationId, docs in endpoints
        ]

    # endpoints = [
    #     (name, description, operationId, reduce_endpoint_docs(docs))
    #     for name, description, operationId, docs in endpoints
    # ]
    endpoints = [
        (name, description, operationId, format_endpoint_docs_text(docs))
        for name, description, operationId, docs in endpoints
    ]
    return ReducedOpenAPISpec(
        servers=spec["servers"],
        title=spec["info"].get("title", ""),
        description=spec["info"].get("description", ""),
        endpoints=endpoints,
        last_commit_date=last_commit_date,
        source=source,
    )


def format_endpoint_docs_text(endpoint_docs):
    """Format endpoint documentation in a human-readable text format."""
    text_parts = []

    # Add description
    if "description" in endpoint_docs:
        text_parts.append(f"Description: {endpoint_docs['description']}\n")

    # Add parameters
    if "parameters" in endpoint_docs and endpoint_docs["parameters"]:
        text_parts.append("Parameters:")
        for param in endpoint_docs["parameters"]:
            text_parts.append(f"  name: {param.get('name', 'N/A')}")
            text_parts.append(f"  in: {param.get('in', 'N/A')}")
            text_parts.append(f"  required: {param.get('required', 'undefined')}")
            text_parts.append(f"  description: {param.get('description', 'N/A')}\n")

    # Add request body
    if "requestBody" in endpoint_docs and isinstance(
        endpoint_docs["requestBody"], dict
    ):
        text_parts.append(format_request_body(endpoint_docs))

    return "\n".join(text_parts)


def create_example_from_schema(schema):
    """Create an example object from a schema definition."""
    example_obj = {}
    if "properties" in schema:
        for prop_name, prop_schema in schema["properties"].items():
            if "properties" in prop_schema:
                example_obj[prop_name] = create_example_from_schema(prop_schema)
            else:
                example_obj[prop_name] = prop_schema.get("example") or prop_schema.get("default") or ""
    return example_obj

def format_request_body(endpoint_docs):
    """Format request body documentation similar to TypeScript version."""
    if not endpoint_docs.get("requestBody"):
        return "No request body"

    text_parts = []
    request_body = endpoint_docs["requestBody"]
    
    # Add description if present
    if request_body.get("description"):
        text_parts.append(request_body["description"])
    
    # Handle content, focusing on application/json
    if "content" in request_body and "application/json" in request_body["content"]:
        json_content = request_body["content"]["application/json"]
        
        # Handle examples (top level examples)
        if "examples" in json_content:
            text_parts.append("\nExamples:")
            for example_key, example in json_content["examples"].items():
                if example.get("summary"):
                    text_parts.append(f"\n{example['summary']}:")
                else:
                    text_parts.append(f"\n{example_key}:")
                if example.get("value"):
                    text_parts.append(yaml.dump(example["value"], default_flow_style=False))
        
        # Handle schema if no examples
        elif "schema" in json_content:
            schema = json_content["schema"]
            
            # Handle oneOf schemas - these are now dereferenced
            if "oneOf" in schema:
                text_parts.append("\nPossible Schemas:")
                for sub_schema in schema["oneOf"]:
                    if "properties" in sub_schema:
                        example = create_example_from_schema(sub_schema)
                        text_parts.append("\nExample:")
                        text_parts.append(yaml.dump(example, default_flow_style=False))
            
            # Handle allOf schemas - these are now dereferenced
            elif "allOf" in schema:
                text_parts.append("\nCombined Schema Example:")
                # Merge all schemas in allOf
                merged_example = {}
                for sub_schema in schema["allOf"]:
                    if "properties" in sub_schema:
                        example = create_example_from_schema(sub_schema)
                        merged_example.update(example)
                text_parts.append(yaml.dump(merged_example, default_flow_style=False))
            
            # Handle regular schema
            elif "properties" in schema:
                example = create_example_from_schema(schema)
                text_parts.append("\nExample:")
                text_parts.append(yaml.dump(example, default_flow_style=False))
    
    return "\n".join(text_parts)

# 3. Strip docs down to required request args + happy path response.
def reduce_endpoint_docs(docs: dict) -> dict:

    out = {}
    if docs.get("description"):
        out["description"] = docs.get("summary") + " - " + docs.get("description")
    # parameters
    if docs.get("parameters"):
        out["parameters"] = [
            parameter
            for parameter in docs.get("parameters", [])
            if parameter.get("required")
        ]
    # requestBody
    try:
        if docs.get("requestBody"):
            out["requestBody"] = docs.get("requestBody")
    except KeyError:
        print("local" + docs.get("summary"))
        out["requestBody"] = ""

    # responses
    try:
        if "200" in docs["responses"]:
            out["responses"] = docs["responses"]["200"]
    except KeyError:
        print("local" + docs.get("summary"))
        out["responses"] = ""

    return out
