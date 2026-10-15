"""Unit tests for list_employees tool."""

from unittest.mock import MagicMock

from mcp.tools.list_employees import QUERY, list_employees

EMPLOYEES = [
    {
        "id": "E-001",
        "name": "Alice Smith",
        "department": "Engineering",
        "email": "alice@example.com",
    }
]


def test_list_employees_success():
    client = MagicMock()
    client.execute_query.return_value = ({"employees": EMPLOYEES}, [])

    result = list_employees(client)

    assert result == {"employees": EMPLOYEES}
    client.execute_query.assert_called_once()
    query_arg = client.execute_query.call_args.args[0]
    assert "employees" in query_arg
    assert "department" in query_arg
    assert "employees" in QUERY


def test_list_employees_error():
    client = MagicMock()
    client.execute_query.return_value = (
        None,
        [{"message": "Internal server error"}],
    )

    result = list_employees(client)

    assert result == {"error": "Failed to fetch employees: Internal server error"}
