import pyodbc
from typing import List, Dict, Any
import os
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

class SQLServerConnection:
    """
    Manages SQL Server connections for manufacturing data
    """
    
    def __init__(self):
        environment = os.getenv("ENVIRONMENT", "dev")

        if environment == "dev":
            self.server = os.getenv("MSSQL_LOCAL_SERVER")
            self.database = os.getenv("MSSQL_LOCAL_DATABASE")
            self.username = os.getenv("MSSQL_LOCAL_USER")
            self.password = os.getenv("MSSQL_LOCAL_PWD")
            
            if not all([self.server, self.database, self.username, self.password]):
                raise ValueError("Missing local SQL Server configuration in .env file")
            
            # Escape special characters in password (handle semicolons, etc.)
            # If password contains semicolon, wrap it in braces
            if ';' in self.password or '{' in self.password or '}' in self.password:
                escaped_password = '{' + self.password + '}'
            else:
                escaped_password = self.password
            
            self.connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={escaped_password};"
            )
            print(f"Using SQL Authentication for {self.database} as {self.username}") 
            
        else:
            # Azure SQL
            self.server = os.getenv("AZURE_SQL_SERVER")
            self.database = os.getenv("AZURE_SQL_DATABASE")
            self.username = os.getenv("AZURE_SQL_USER")
            self.password = os.getenv("AZURE_SQL_PWD")
            
            if not all([self.server, self.database, self.username, self.password]):
                raise ValueError("Missing Azure SQL configuration in .env file")
            
            self.connection_string = (
                f"DRIVER={{ODBC Driver 17 for SQL Server}};"
                f"SERVER={self.server};"
                f"DATABASE={self.database};"
                f"UID={self.username};"
                f"PWD={self.password};"
            )
            print(f"✓ Using Azure SQL Authentication for {self.database}")
    
    def test_connection(self) -> bool:
        """Test if database connection works"""
        try:
            print(f"Connecting to: {self.server}")
            print(f"Database: {self.database}")
            print(f"Username: {self.username}")
            
            conn = pyodbc.connect(self.connection_string, timeout=10)
            cursor = conn.cursor()
            
            # Test query
            cursor.execute("SELECT @@VERSION, DB_NAME()")
            row = cursor.fetchone()
            version = row[0]
            current_db = row[1]
            
            print(f"\n✓ Successfully connected!")
            print(f"✓ Database: {current_db}")
            print(f"✓ SQL Server: {version.split(chr(10))[0]}")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"\n✗ Connection failed!")
            print(f"Error: {e}")
            return False
    
    def execute_query(self, query: str) -> List[Dict[str, Any]]:
        """
        Execute SQL query and return results as list of dictionaries
        
        Args:
            query: SQL SELECT query to execute
            
        Returns:
            List of dictionaries, one per row
        """
        if not query.strip().upper().startswith(("SELECT", "WITH")):
            raise ValueError("Only SELECT queries are allowed")
        
        try:
            conn = pyodbc.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute(query)
            
            # Get column names
            columns = [column[0] for column in cursor.description]
            
            # Fetch results
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            raise Exception(f"Query execution failed: {str(e)}")

    def execute_write(self, query: str) -> None:
        """Execute an INSERT, UPDATE, or DELETE query"""
        try:
            conn = pyodbc.connect(self.connection_string)
            conn.autocommit = True
            cursor = conn.cursor()
            cursor.execute(query)
            cursor.close()
            conn.close()
        except Exception as e:
            raise Exception(f"Write query failed: {str(e)}")

    def get_row_count(self, table: str) -> int:
        """Return number of rows in a table"""
        results = self.execute_query(f"SELECT COUNT(*) AS cnt FROM {table}")
        return results[0]['cnt'] if results else 0

    def list_tables(self) -> List[str]:
        """
        List all tables in the database
        
        Returns:
            List of table names
        """
        query = """
        SELECT TABLE_NAME 
        FROM INFORMATION_SCHEMA.TABLES 
        WHERE TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """
        
        results = self.execute_query(query)
        return [r["TABLE_NAME"] for r in results]
    
    def get_table_schema(self, table_name: str) -> List[Dict[str, Any]]:
        """
        Get schema information for a table
        
        Args:
            table_name: Name of the table
            
        Returns:
            List of column definitions
        """
        query = f"""
        SELECT 
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            CHARACTER_MAXIMUM_LENGTH,
            NUMERIC_PRECISION,
            NUMERIC_SCALE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = '{table_name}'
        ORDER BY ORDINAL_POSITION
        """
        
        return self.execute_query(query)


if __name__ == "__main__":
    print("=" * 70)
    print("DATABASE CONNECTION TEST")
    print("=" * 70)
    
    db = SQLServerConnection()
    
    if db.test_connection():
        print("\n" + "=" * 70)
        print("LISTING TABLES")
        print("=" * 70)
        
        try:
            tables = db.list_tables()
            print(f"\n✓ Found {len(tables)} tables:")
            for i, table in enumerate(tables, 1):
                print(f"  {i}. {table}")
            
            if tables:
                # Show schema of first table as example
                print(f"\n" + "=" * 70)
                print(f"SAMPLE SCHEMA: {tables[0]}")
                print("=" * 70)
                schema = db.get_table_schema(tables[0])
                for col in schema:
                    print(f"  - {col['COLUMN_NAME']}: {col['DATA_TYPE']}")
        except Exception as e:
            print(f"\n✗ Error listing tables: {e}")
    else:
        print("\n✗ Connection test failed. Please check your credentials.")
        print("\nTroubleshooting steps:")
        print("1. Verify password in .env (remove any trailing semicolons)")
        print("2. Check SQL Server allows SQL authentication:")
        print("   - Open SQL Server Configuration Manager")
        print("   - Check SQL Server is in 'Mixed Mode' authentication")
        print("3. Verify 'sa' account is enabled in SQL Server")
        print("4. Make sure SQL Server service is running")