"""
SQL Tools Provider - Defines tools for Claude to query the database
"""
from typing import List, Dict, Any


class SQLToolsProvider:
    """
    Provides SQL query tools for Claude to use via Anthropic tool use API
    """

    def __init__(self, db):
        self.db = db

    def get_tool_definitions(self) -> List[Dict]:
        """Return tool definitions in Anthropic tool format"""
        return [
            {
                "name": "execute_sql",
                "description": "Execute a SELECT SQL query against the asset database and return results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The SELECT SQL query to execute"
                        }
                    },
                    "required": ["query"]
                }
            },
            {
                "name": "list_tables",
                "description": "List all available tables in the database",
                "input_schema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "get_table_schema",
                "description": "Get the column definitions for a specific table",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "table_name": {
                            "type": "string",
                            "description": "Name of the table to inspect"
                        }
                    },
                    "required": ["table_name"]
                }
            }
        ]

    def execute_tool(self, tool_name: str, tool_input: Dict) -> Any:
        """Execute a tool call from Claude and return the result"""
        if tool_name == "execute_sql":
            try:
                return self.db.execute_query(tool_input["query"])
            except ValueError as e:
                return {"error": str(e), "note": "Only SELECT queries are permitted. Do not use INSERT, UPDATE, DELETE, or DDL statements."}
            except Exception as e:
                return {"error": str(e), "note": "Fix the SQL syntax and retry. Use T-SQL: SELECT TOP N col FROM table (TOP after SELECT), GETDATE(), DATEADD(). Never use LIMIT, CURDATE(), or hardcoded date strings."}

        elif tool_name == "list_tables":
            return self.db.list_tables()

        elif tool_name == "get_table_schema":
            return self.db.get_table_schema(tool_input["table_name"])

        else:
            raise ValueError(f"Unknown tool: {tool_name}") 
        
    

