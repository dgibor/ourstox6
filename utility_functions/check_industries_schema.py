import os
import logging
import psycopg2
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Load environment variables
load_dotenv()

def check_industries_schema():
    """Check and print the schema of the industries table"""
    try:
        # Connect to database
        conn = psycopg2.connect(
            dbname=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            host=os.getenv('DB_HOST'),
            port=os.getenv('DB_PORT')
        )
        cur = conn.cursor()

        # Check if table exists
        cur.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'industries'
            );
        """)
        table_exists = cur.fetchone()[0]

        if not table_exists:
            logging.info("industries table does not exist")
            return

        # Get column information
        cur.execute("""
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = 'industries'
            ORDER BY ordinal_position;
        """)
        columns = cur.fetchall()

        logging.info("\nIndustries table schema:")
        for col in columns:
            logging.info(f"Column: {col[0]}, Type: {col[1]}, Nullable: {col[2]}")

        # Get constraints
        cur.execute("""
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'industries'::regclass;
        """)
        constraints = cur.fetchall()

        logging.info("\nConstraints:")
        for con in constraints:
            logging.info(f"Name: {con[0]}, Definition: {con[1]}")

    except Exception as e:
        logging.error(f"Error checking schema: {e}")
    finally:
        if 'cur' in locals():
            cur.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_industries_schema() 