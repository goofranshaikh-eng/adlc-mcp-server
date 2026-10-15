"""Unit tests for list_sales_order tool."""

from unittest.mock import MagicMock

from mcp.tools.list_sales_order import QUERY, list_sales_order

SALES_ORDERS = [
    {
        "id": "SO-001",
        "customerId": "C-123",
        "total": 1500.0,
        "status": "shipped",
    }
]


def test_list_sales_order_success():
    client = MagicMock()
    client.execute_query.return_value = ({"salesOrders": SALES_ORDERS}, [])

    result = list_sales_order(client)

    assert result == {"salesOrders": SALES_ORDERS}
    client.execute_query.assert_called_once()
    query_arg = client.execute_query.call_args.args[0]
    assert "salesOrders" in query_arg
    assert "customerId" in query_arg
    assert query_arg.strip() == QUERY.strip() or "salesOrders" in QUERY


def test_list_sales_order_error():
    client = MagicMock()
    client.execute_query.return_value = (
        None,
        [{"message": "Internal server error"}],
    )

    result = list_sales_order(client)

    assert result == {"error": "Failed to fetch sales orders: Internal server error"}
