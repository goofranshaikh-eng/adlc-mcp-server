"""Tool handler for listing sales orders."""

from __future__ import annotations

from mcp.graphql_client import GraphQLClient, NetworkError

QUERY = """
query {
  salesOrders {
    id
    customerId
    total
    status
  }
}
"""


def list_sales_order(graphql_client: GraphQLClient) -> dict:
    """
    Query GraphQL service for all sales orders.

    Args:
        graphql_client: Initialized GraphQLClient instance

    Returns:
        Success: {"salesOrders": [...]}
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
        return {"error": f"Failed to fetch sales orders: {message}"}

    if data is None or data.get("salesOrders") is None:
        return {"error": "Failed to fetch sales orders: no data returned"}

    return {"salesOrders": data["salesOrders"]}
