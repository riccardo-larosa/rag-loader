"""
    ORIGINAL AUTHOR: langchain_community.agent_toolkits.openapi.spec
    Quick and dirty representation for OpenAPI specs."""

from dataclasses import dataclass
from typing import List, Tuple

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


def reduce_openapi_spec(spec: dict, last_commit_date: str, source: str, dereference: bool = True) -> ReducedOpenAPISpec:
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
        (f"{operation_name.upper()} {route}", docs.get("description"), docs)
        for route, operation in spec["paths"].items()
        for operation_name, docs in operation.items()
        if operation_name in ["get", "post", "patch", "put", "delete"]
    ]

    # 2. Replace any refs so that complete docs are retrieved.
    # Note: probably want to do this post-retrieval, it blows up the size of the spec.
    if dereference:
        endpoints = [
            (name, description, dereference_refs(docs, full_schema=spec, skip_keys=["responses","examples"]))
            for name, description, docs in endpoints
        ]

    # 3. Strip docs down to required request args + happy path response.
    def reduce_endpoint_docs(docs: dict) -> dict:
        
        out = {}
        if docs.get("description"):
            out["description"] = docs.get("summary") + " - " + docs.get("description")
        if docs.get("parameters"):
            out["parameters"] = [
                parameter
                for parameter in docs.get("parameters", [])
                if parameter.get("required")
            ]
        try:
            if "200" in docs["responses"]:
                out["responses"] = docs["responses"]["200"]
        except KeyError:
            print("local" + docs.get("summary"))
            out["responses"] = ""
        
        try:
            if docs.get("requestBody"):
                out["requestBody"] = docs.get("requestBody")
        except KeyError:
            print("local" + docs.get("summary"))
            out["requestBody"] = ""
        return out
    
    endpoints = [
        (name, description, reduce_endpoint_docs(docs))
        for name, description, docs in endpoints
    ]
    return ReducedOpenAPISpec(
        servers=spec["servers"],
        title=spec["info"].get("title", ""),
        description=spec["info"].get("description", ""),
        endpoints=endpoints,
        last_commit_date=last_commit_date,
        source=source
    )
