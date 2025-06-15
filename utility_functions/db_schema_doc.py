import psycopg2
import os

# Database connection info
DB_HOST = 'localhost'
DB_PORT = 5432
DB_NAME = 'ourstox5'
DB_USER = 'ourstox5_user'
DB_PASSWORD = 'Testing123'

# Connect to the PostgreSQL database
conn = psycopg2.connect(
    host=DB_HOST,
    port=DB_PORT,
    dbname=DB_NAME,
    user=DB_USER,
    password=DB_PASSWORD
)

cur = conn.cursor()

# Get all tables in the public schema
cur.execute("""
    SELECT table_name
    FROM information_schema.tables
    WHERE table_schema = 'public'
    ORDER BY table_name;
""")
tables = cur.fetchall()

schema_doc = "# Database Schema Documentation\n\n"

for (table_name,) in tables:
    schema_doc += f"## Table: `{table_name}`\n\n"
    schema_doc += "| Column Name | Data Type | Is Nullable | Default |\n"
    schema_doc += "|-------------|-----------|------------|---------|\n"
    cur.execute("""
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        ORDER BY ordinal_position;
    """, (table_name,))
    columns = cur.fetchall()
    for col in columns:
        col_name, data_type, is_nullable, col_default = col
        schema_doc += f"| {col_name} | {data_type} | {is_nullable} | {col_default or ''} |\n"
    schema_doc += "\n"

cur.close()
conn.close()

# Write the documentation to a Markdown file
with open('db_schema.md', 'w', encoding='utf-8') as f:
    f.write(schema_doc)

print('Database schema documentation generated in db_schema.md') 