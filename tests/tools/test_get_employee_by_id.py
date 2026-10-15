"""Unit tests for get_employee_by_id tool."""

from unittest.mock import MagicMock

from mcp.tools.get_employee_by_id import QUERY, get_employee_by_id

EMPLOYEE = {
    "id": "E-001",
    "name": "Alice Smith",
    "department": "Engineering",
    "email": "alice@example.com",
}


def test_get_employee_by_id_success():
    client = MagicMock()
    client.execute_query.return_value = ({"employee": EMPLOYEE}, [])

    result = get_employee_by_id(client, "E-001")

    assert result == {"employee": EMPLOYEE}
    client.execute_query.assert_called_once()
    call_args = client.execute_query.call_args
    query_arg = call_args.args[0]
    variables = call_args.args[1] if len(call_args.args) > 1 else call_args.kwargs.get(
        "variables"
    )
    assert "employee" in query_arg
    assert "$id" in QUERY
    assert variables == {"id": "E-001"}


def test_get_employee_by_id_missing_id():
    client = MagicMock()

    result = get_employee_by_id(client, None)

    assert result == {"error": "Missing required parameter: id"}
    client.execute_query.assert_not_called()

    result_empty = get_employee_by_id(client, "")
    assert result_empty == {"error": "Missing required parameter: id"}


def test_get_employee_by_id_not_found():
    client = MagicMock()
    client.execute_query.return_value = ({"employee": None}, [])

    result = get_employee_by_id(client, "E-999")

    assert result == {"employee": None}


def test_get_employee_by_id_error():
    client = MagicMock()
    client.execute_query.return_value = (
        None,
        [{"message": "Internal server error"}],
    )

    result = get_employee_by_id(client, "E-001")

    assert result == {
        "error": "Failed to fetch employee E-001: Internal server error"
    }
