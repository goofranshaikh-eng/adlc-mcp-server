"""Unit tests for get_sales_order_by_id tool."""

from unittest.mock import MagicMock

from mcp.tools.get_sales_order_by_id import QUERY, get_sales_order_by_id

SALES_ORDER = {
    "id": "SO-001",
    "customerId": "C-123",
    "total": 1500.0,
    "status": "shipped",
}


def test_get_sales_order_by_id_success():
    client = MagicMock()
    client.execute_query.return_value = ({"salesOrder": SALES_ORDER}, [])

    result = get_sales_order_by_id(client, "SO-001")

    assert result == {"salesOrder": SALES_ORDER}
    client.execute_query.assert_called_once()
    call_args = client.execute_query.call_args
    query_arg = call_args.args[0]
    variables = (
        call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get("variables")
    )
    assert "salesOrder" in query_arg
    assert "$id" in QUERY
    assert variables == {"id": "SO-001"}


def test_get_sales_order_by_id_missing_id():
    client = MagicMock()

    result = get_sales_order_by_id(client, None)

    assert result == {"error": "Missing required parameter: id"}
    client.execute_query.assert_not_called()

    result_empty = get_sales_order_by_id(client, "  ")
    assert result_empty == {"error": "Missing required parameter: id"}


def test_get_sales_order_by_id_not_found():
    client = MagicMock()
    client.execute_query.return_value = ({"salesOrder": None}, [])

    result = get_sales_order_by_id(client, "SO-999")

    assert result == {"salesOrder": None}


def test_get_sales_order_by_id_error():
    client = MagicMock()
    client.execute_query.return_value = (
        None,
        [{"message": "Internal server error"}],
    )

    result = get_sales_order_by_id(client, "SO-001")

    assert result == {
        "error": "Failed to fetch sales order SO-001: Internal server error"
    }
