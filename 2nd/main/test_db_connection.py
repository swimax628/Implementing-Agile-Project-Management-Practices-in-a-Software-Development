# # test_db_connection.py

# from sqlalchemy import create_engine, text  # Import 'text'
# from config import TAWOS_DB_URI

# engine = create_engine(TAWOS_DB_URI)

# try:
#     with engine.connect() as connection:
#         result = connection.execute(text("SELECT 1"))  # Wrap query with 'text()'
#         print("Database connection successful.")
# except Exception as e:
#     print(f"Database connection failed: {e}")
