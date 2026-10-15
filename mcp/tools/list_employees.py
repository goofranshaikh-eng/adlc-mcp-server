"""Tool handler for listing employees."""

from __future__ import annotations

from mcp.graphql_client import GraphQLClient, NetworkError

QUERY = """
query {
  employees {
    id
    name
    department
    email
  }
}
"""


def list_employees(graphql_client: GraphQLClient) -> dict:
    """
    Query GraphQL service for all employees.

    Args:
        graphql_client: Initialized GraphQLClient instance

    Returns:
        Success: {"employees": [...]}
        Error: {"error": "<message>"}
    """
    try:
        data, errors = graphql_client.execute_query(QUERY)
    except NetworkError as exc:
        return {"error": f"GraphQL service unavailable: {exc}"}
    except ValueError as exc:
        return {"error": f"Invalid response from GraphQL service: {exc}"}

    if errors:
        message = errors[0].get("message", str(errors[0]))
        return {"error": f"Failed to fetch employees: {message}"}

    if data is None or data.get("employees") is None:
        return {"error": "Failed to fetch employees: no data returned"}

    return {"employees": data["employees"]}
