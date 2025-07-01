import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

COLUMNS_TO_UPDATE = [
    'sector', 'industry', 'business_model', 'peer_a', 'peer_b', 'peer_c'
]

ALTER_TYPE = 'text'

def get_dependent_views(cur):
    # Find all regular views that reference the stocks table
    cur.execute('''
        SELECT table_schema, table_name
        FROM information_schema.views
        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
    ''')
    views = cur.fetchall()
    dependent_views = []
    for schema, view in views:
        cur.execute(f"SELECT pg_get_viewdef('{schema}.{view}', true)")
        definition = cur.fetchone()[0]
        if 'stocks' in definition:
            dependent_views.append((schema, view))
    # Find all materialized views that reference the stocks table
    cur.execute('''
        SELECT schemaname, matviewname, definition
        FROM pg_matviews
    ''')
    matviews = cur.fetchall()
    dependent_matviews = []
    for schema, matview, definition in matviews:
        if 'stocks' in definition:
            dependent_matviews.append((schema, matview))
    return dependent_views, dependent_matviews

def drop_views(cur, views, matviews):
    for schema, view in views:
        print(f"Dropping view: {schema}.{view}")
        cur.execute(f'DROP VIEW IF EXISTS {schema}.{view} CASCADE;')
    for schema, matview in matviews:
        print(f"Dropping materialized view: {schema}.{matview}")
        cur.execute(f'DROP MATERIALIZED VIEW IF EXISTS {schema}.{matview} CASCADE;')

def alter_columns(cur):
    for col in COLUMNS_TO_UPDATE:
        print(f"Altering column: {col} to type {ALTER_TYPE}")
        cur.execute(f"ALTER TABLE stocks ALTER COLUMN {col} TYPE {ALTER_TYPE};")

def main():
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    try:
        print("Finding dependent views...")
        views, matviews = get_dependent_views(cur)
        if not views and not matviews:
            print("No dependent views found.")
        else:
            print(f"Found {len(views)} views and {len(matviews)} materialized views to drop.")
            drop_views(cur, views, matviews)
        
        print("Altering columns...")
        alter_columns(cur)
        conn.commit()
        print("✅ Columns altered successfully!")
        print("\n⚠️  Please recreate the dropped views/materialized views as needed.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Error: {e}")
        raise
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    main() 