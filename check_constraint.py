import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def check_constraint():
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=os.getenv('DB_PORT', '5432')
        )
        
        cursor = conn.cursor()
        
        # Check the fundamental_risk_level constraint
        print("=== FUNDAMENTAL_RISK_LEVEL CONSTRAINT ===")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = 'company_scores_current'::regclass 
            AND conname LIKE '%fundamental_risk_level%';
        """)
        
        constraints = cursor.fetchall()
        for constraint in constraints:
            print(f"Constraint: {constraint[0]}")
            print(f"Definition: {constraint[1]}")
            print()
        
        # Check the overall_grade constraint
        print("=== OVERALL_GRADE CONSTRAINT ===")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = 'company_scores_current'::regclass 
            AND conname LIKE '%overall_grade%';
        """)
        
        constraints = cursor.fetchall()
        for constraint in constraints:
            print(f"Constraint: {constraint[0]}")
            print(f"Definition: {constraint[1]}")
            print()
        
        # Check the technical_risk_level constraint
        print("=== TECHNICAL_RISK_LEVEL CONSTRAINT ===")
        cursor.execute("""
            SELECT conname, pg_get_constraintdef(oid) 
            FROM pg_constraint 
            WHERE conrelid = 'company_scores_current'::regclass 
            AND conname LIKE '%technical_risk_level%';
        """)
        
        constraints = cursor.fetchall()
        for constraint in constraints:
            print(f"Constraint: {constraint[0]}")
            print(f"Definition: {constraint[1]}")
            print()
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_constraint() 