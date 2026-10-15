"""Tool handler for fetching a sales order by ID."""

from __future__ import annotations

from mcp.graphql_client import GraphQLClient, NetworkError

QUERY = """
query GetSalesOrder($id: ID!) {
  salesOrder(id: $id) {
    id
    customerId
    total
    status
  }
}
"""


def get_sales_order_by_id(graphql_client: GraphQLClient, id: str | None) -> dict:
    """
    Query GraphQL service for a sales order by ID.

    Args:
        graphql_client: Initialized GraphQLClient instance
        id: Sales order ID (required)

    Returns:
        Success (found): {"salesOrder": {...}}
        Success (not found): {"salesOrder": null}
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
        return {"error": f"Failed to fetch sales order {id}: {message}"}

    if data is None:
        return {"error": f"Failed to fetch sales order {id}: no data returned"}

    return {"salesOrder": data.get("salesOrder")}
