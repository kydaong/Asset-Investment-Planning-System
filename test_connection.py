"""
Test script to verify SQL Server connection
"""
from app.core.database import SQLServerConnection

def main():
    print("=" * 60)
    print("Asset Intelligence System - Database Connection Test")
    print("=" * 60)
    print()
    
    try:
        print("Initializing database connection...")
        db = SQLServerConnection()
        print("✓ Database configuration loaded")
        print()
        
        print("Testing connection...")
        if db.test_connection():
            print("✓ Connection successful!")
            print()
            
            print("Retrieving available tables...")
            tables = db.list_tables()
            
            if tables:
                print(f"✓ Found {len(tables)} table(s):")
                print()
                for i, table in enumerate(tables, 1):
                    print(f"  {i}. {table}")
            else:
                print("⚠ No tables found in database")
            
        else:
            print("✗ Connection failed")
            print()
            print("Please check your .env file:")
            print("  - SQL_SERVER")
            print("  - SQL_DATABASE")
            print("  - SQL_USERNAME")
            print("  - SQL_PASSWORD")
    
    except ValueError as e:
        print(f"✗ Configuration error: {e}")
        print()
        print("Please ensure .env file exists with all required variables")
    
    except Exception as e:
        print(f"✗ Error: {e}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()

