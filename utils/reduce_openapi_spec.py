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
    if "requestBody" in endpoint_docs and isinstance(endpoint_docs["requestBody"], dict):
        text_parts.append(format_request_body(endpoint_docs))

    return "\n".join(text_parts)

def format_request_body(endpoint_docs):
    text_parts = []
    text_parts.append("Request Body:")
    request_body = endpoint_docs["requestBody"]
        
        # Add description if present
    if request_body.get("description"):
        text_parts.append(f"  Description: {request_body['description']}")
        
    if "content" in request_body:
        content = request_body["content"]
        if isinstance(content, dict):
            for content_type, content_details in content.items():
                if isinstance(content_details, dict):  # Make sure content_details is a dict
                    text_parts.append(f"  Content Type: {content_type}")
                        
                    if "schema" in content_details:
                        schema = content_details["schema"]
                        if isinstance(schema, dict):
                            if "allOf" in schema:
                                text_parts.append("  Schema: Uses allOf reference")
                            elif "type" in schema:
                                text_parts.append(f"  Type: {schema['type']}")
                        
                    if "example" in content_details:
                        text_parts.append("\nExample:")
                        text_parts.append(yaml.dump(content_details["example"], default_flow_style=False))
                    elif "examples" in content_details:
                        text_parts.append("\nExamples:")
                        for example_name, example in content_details["examples"].items():
                            text_parts.append(f"{example_name}:")
                            text_parts.append(yaml.dump(example.get("value", {}), default_flow_style=False))
