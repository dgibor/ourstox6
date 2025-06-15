import psycopg2

# Old database connection info
OLD_DB = {
    'host': 'localhost',
    'port': 5432,
    'dbname': 'ourstox5',
    'user': 'ourstox5_user',
    'password': 'Testing123'
}

# New database connection info
NEW_DB = {
    'host': 'yamanote.proxy.rlwy.net',
    'port': 38837,
    'dbname': 'railway',
    'user': 'postgres',
    'password': 'KNNUYcidcJqFkwmctFdAnjvYdijsZocv'
}

# Connect to old database
old_conn = psycopg2.connect(**OLD_DB)
old_cur = old_conn.cursor()

# Get all sequence names in public schema
old_cur.execute("""
    SELECT sequencename FROM pg_sequences
    WHERE schemaname = 'public';
""")
sequences = [row[0] for row in old_cur.fetchall()]

# Get CREATE SEQUENCE statements for each sequence
sequence_statements = []
for seq in sequences:
    old_cur.execute(
        """
        SELECT 'CREATE SEQUENCE public.' || quote_ident(s.sequencename) ||
               ' INCREMENT BY ' || s.increment_by ||
               ' MINVALUE ' || s.min_value ||
               ' MAXVALUE ' || s.max_value ||
               ' START ' || s.start_value ||
               ' CACHE ' || s.cache_size ||
               CASE WHEN s.cycle THEN ' CYCLE' ELSE '' END || ';'
        FROM pg_sequences s
        WHERE s.schemaname = 'public' AND s.sequencename = %s;
        """,
        (seq,)
    )
    stmt = old_cur.fetchone()[0]
    sequence_statements.append(stmt)

# Get all table names in public schema
old_cur.execute("""
    SELECT table_name FROM information_schema.tables
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
""")
tables = [row[0] for row in old_cur.fetchall()]

# Get CREATE TABLE statements for each table
create_statements = []
for table in tables:
    old_cur.execute(
        """
        SELECT 'CREATE TABLE ' || quote_ident(schemaname) || '.' || quote_ident(tablename) || E' (\n' || string_agg('    ' || quote_ident(column_name) || ' ' || type ||
            CASE WHEN is_nullable = 'NO' THEN ' NOT NULL' ELSE '' END ||
            CASE WHEN column_default IS NOT NULL THEN ' DEFAULT ' || column_default ELSE '' END, ',\n') || E'\n);'
        FROM (
            SELECT
                n.nspname AS schemaname,
                c.relname AS tablename,
                a.attname AS column_name,
                pg_catalog.format_type(a.atttypid, a.atttypmod) AS type,
                (SELECT pg_catalog.pg_get_expr(d.adbin, d.adrelid)
                 FROM pg_catalog.pg_attrdef d
                 WHERE d.adrelid = a.attrelid AND d.adnum = a.attnum AND a.atthasdef) AS column_default,
                CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable
            FROM pg_catalog.pg_class c
                 JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
                 JOIN pg_catalog.pg_attribute a ON a.attrelid = c.oid
            WHERE c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped
            ORDER BY a.attnum
        ) AS tabledef
        GROUP BY schemaname, tablename;
        """,
        (table,)
    )
    stmt = old_cur.fetchone()[0]
    create_statements.append(stmt)

old_cur.close()
old_conn.close()

# Connect to new database
new_conn = psycopg2.connect(**NEW_DB)
new_cur = new_conn.cursor()

# Execute CREATE SEQUENCE statements in new database
for stmt in sequence_statements:
    try:
        new_cur.execute(stmt)
        print(f"Created sequence with statement:\n{stmt}\n")
    except Exception as e:
        print(f"Failed to create sequence: {e}\nStatement:\n{stmt}\n")
        new_conn.rollback()
    else:
        new_conn.commit()

# Execute CREATE TABLE statements in new database
for stmt in create_statements:
    try:
        new_cur.execute(stmt)
        print(f"Created table with statement:\n{stmt}\n")
    except Exception as e:
        print(f"Failed to create table: {e}\nStatement:\n{stmt}\n")
        new_conn.rollback()
    else:
        new_conn.commit()

new_cur.close()
new_conn.close()

print('All sequences and table structures duplicated successfully.') 