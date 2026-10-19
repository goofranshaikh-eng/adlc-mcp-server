"""MCP tools for sales orders and employees.

Queries match the TriNet GraphQL schema (PER-5) and the stdio tool payloads.
"""

from graphql_client import GraphQLClient, GraphQLClientError

LIST_SALES_ORDERS = """
query ListSalesOrders {
  salesorder_list {
    id
    accountName
    amount
    status
  }
}
"""

LIST_EMPLOYEES = """
query ListEmployees {
  employee_list {
    id
    firstName
    lastName
    department
    email
  }
}
"""

GET_SALES_ORDER_BY_ID = """
query GetSalesOrderById($id: String!) {
  get_salesorder_by_id(id: $id) {
    id
    accountName
    amount
    status
  }
}
"""

GET_EMPLOYEE_BY_ID = """
query GetEmployeeById($id: String!) {
  get_employee_by_id(id: $id) {
    id
    firstName
    lastName
    department
    email
  }
}
"""


def _error(exc: Exception) -> dict:
    message = str(exc).strip() or exc.__class__.__name__
    return {"error": message}


def _missing_id(value: str | None) -> bool:
    return value is None or not str(value).strip()


def _with_name(employee: dict | None) -> dict | None:
    if employee is None:
        return None
    first = employee.get("firstName") or ""
    last = employee.get("lastName") or ""
    return {**employee, "name": f"{first} {last}".strip()}


async def _execute(client: GraphQLClient, query: str, variables: dict | None = None) -> dict:
    try:
        return await client.execute(query, variables)
    except GraphQLClientError as exc:
        return _error(exc)
    except Exception as exc:
        return _error(exc)


async def list_sales_order(client: GraphQLClient) -> dict:
    """Return sales orders, or an error payload if GraphQL fails."""
    data = await _execute(client, LIST_SALES_ORDERS)
    if "error" in data and "salesorder_list" not in data:
        return data
    orders = data.get("salesorder_list")
    if not isinstance(orders, list):
        return {"error": "Failed to fetch sales orders: no data returned"}
    return {"salesOrders": orders}


async def list_employees(client: GraphQLClient) -> dict:
    """Return employees, or an error payload if GraphQL fails."""
    data = await _execute(client, LIST_EMPLOYEES)
    if "error" in data and "employee_list" not in data:
        return data
    employees = data.get("employee_list")
    if not isinstance(employees, list):
        return {"error": "Failed to fetch employees: no data returned"}
    return {"employees": [_with_name(employee) for employee in employees]}


async def get_sales_order_by_id(client: GraphQLClient, id: str | None = None) -> dict:
    """Return one sales order. Missing or blank ids are an error payload."""
    if _missing_id(id):
        return {"error": "Missing required parameter: id"}
    data = await _execute(client, GET_SALES_ORDER_BY_ID, {"id": id})
    if "error" in data and "get_salesorder_by_id" not in data:
        return data
    return {"salesOrder": data.get("get_salesorder_by_id")}


async def get_employee_by_id(client: GraphQLClient, id: str | None = None) -> dict:
    """Return one employee. Missing or blank ids are an error payload."""
    if _missing_id(id):
        return {"error": "Missing required parameter: id"}
    data = await _execute(client, GET_EMPLOYEE_BY_ID, {"id": id})
    if "error" in data and "get_employee_by_id" not in data:
        return data
    return {"employee": _with_name(data.get("get_employee_by_id"))}


def register_tools(mcp, client: GraphQLClient) -> None:
    """Register the four GraphQL tools on the shared FastMCP instance."""

    @mcp.tool(
        name="list_sales_order",
        description="Query GraphQL service for all sales orders",
    )
    async def list_sales_order_tool() -> dict:
        """Query GraphQL service for all sales orders."""
        return await list_sales_order(client)

    @mcp.tool(
        name="list_employees",
        description="Query GraphQL service for all employees",
    )
    async def list_employees_tool() -> dict:
        """Query GraphQL service for all employees."""
        return await list_employees(client)

    @mcp.tool(
        name="get_sales_order_by_id",
        description="Query GraphQL service for a sales order by ID",
    )
    async def get_sales_order_by_id_tool(id: str | None = None) -> dict:
        """Query GraphQL service for a sales order by ID."""
        return await get_sales_order_by_id(client, id)

    @mcp.tool(
        name="get_employee_by_id",
        description="Query GraphQL service for an employee by ID",
    )
    async def get_employee_by_id_tool(id: str | None = None) -> dict:
        """Query GraphQL service for an employee by ID."""
        return await get_employee_by_id(client, id)
