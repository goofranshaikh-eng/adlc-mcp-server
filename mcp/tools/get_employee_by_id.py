"""Tool handler for fetching an employee by ID."""

from __future__ import annotations

from mcp.graphql_client import GraphQLClient, NetworkError

QUERY = """
query GetEmployee($id: ID!) {
  employee(id: $id) {
    id
    name
    department
    email
  }
}
"""


def get_employee_by_id(graphql_client: GraphQLClient, id: str | None) -> dict:
    """
    Query GraphQL service for an employee by ID.

    Args:
        graphql_client: Initialized GraphQLClient instance
        id: Employee ID (required)

    Returns:
        Success (found): {"employee": {...}}
        Success (not found): {"employee": null}
        Error: {"error": "<message>"}
    """
    if id is None or str(id).strip() == "":
        return {"error": "Missing required parameter: id"}

    try:
        data, errors = graphql_client.execute_query(QUERY, {"id": id})
    except NetworkError as exc:
        return {"error": f"GraphQL service unavailable: {exc}"}
    except ValueError as exc:
        return {"error": f"Invalid response from GraphQL service: {exc}"}

    if errors:
        message = errors[0].get("message", str(errors[0]))
        return {"error": f"Failed to fetch employee {id}: {message}"}

    if data is None:
        return {"error": f"Failed to fetch employee {id}: no data returned"}

    return {"employee": data.get("employee")}
