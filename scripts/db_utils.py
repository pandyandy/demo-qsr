import duckdb

# Create a global DuckDB connection
_db_connection = duckdb.connect()

def get_db_connection():
    """Returns the DuckDB connection."""
    return _db_connection