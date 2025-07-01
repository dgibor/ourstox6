import pandas as pd
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from datetime import datetime
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_db_connection():
    """Get database connection"""
    try:
        conn = psycopg2.connect(
            host=os.getenv('DB_HOST', 'yamanote.proxy.rlwy.net'),
            database=os.getenv('DB_NAME', 'railway'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', 'KNNUYcidcJqFkwmctFdAnjvYdijsZocv'),
            port=os.getenv('DB_PORT', '38837')
        )
        return conn
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        raise

def read_batch9_csv():
    """Read batch9.csv file"""
    try:
        df = pd.read_csv('pre_filled_stocks/batch9.csv')
        logger.info(f"Successfully read batch9.csv with {len(df)} records")
        return df
    except Exception as e:
        logger.error(f"Failed to read batch9.csv: {e}")
        raise

def clean_data(df):
    """Clean and prepare data for database insertion"""
    # Handle missing values
    df = df.fillna('')
    
    # Clean market cap - remove 'B' and convert to numeric
    df['Market Cap (B)'] = df['Market Cap (B)'].astype(str).str.replace('B', '').str.strip()
    df['Market Cap (B)'] = pd.to_numeric(df['Market Cap (B)'], errors='coerce').fillna(0)
    
    # Clean text fields - remove extra whitespace
    text_columns = ['Company Name', 'Industry', 'Sector', 'Description', 'Business_Model', 
                   'Products_Services', 'Main_Customers', 'Markets', 'Moat 1', 'Moat 2', 
                   'Moat 3', 'Moat 4', 'Peer A', 'Peer B', 'Peer C']
    
    for col in text_columns:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    
    # Handle duplicate KLA entries - keep KLAC as it's more specific
    df = df[df['Ticker'] != 'KLA']  # Remove the duplicate KLA entry
    
    logger.info(f"Data cleaned. Final record count: {len(df)}")
    return df

def update_stocks_table(df):
    """Update stocks table with batch9 data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        updated_count = 0
        inserted_count = 0
        error_count = 0
        
        for index, row in df.iterrows():
            try:
                # Check if ticker exists
                cursor.execute("SELECT id FROM stocks WHERE ticker = %s", (row['Ticker'],))
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # Update existing record
                    update_query = """
                    UPDATE stocks SET 
                        company_name = %s,
                        sector = %s,
                        industry = %s,
                        market_cap_b = %s,
                        description = %s,
                        business_model = %s,
                        products_services = %s,
                        main_customers = %s,
                        markets = %s,
                        moat_1 = %s,
                        moat_2 = %s,
                        moat_3 = %s,
                        moat_4 = %s,
                        peer_a = %s,
                        peer_b = %s,
                        peer_c = %s,
                        last_updated = %s
                    WHERE ticker = %s
                    """
                    
                    cursor.execute(update_query, (
                        row['Company Name'],
                        row['Sector'],
                        row['Industry'],
                        row['Market Cap (B)'],
                        row['Description'],
                        row['Business_Model'],
                        row['Products_Services'],
                        row['Main_Customers'],
                        row['Markets'],
                        row['Moat 1'],
                        row['Moat 2'],
                        row['Moat 3'],
                        row['Moat 4'],
                        row['Peer A'],
                        row['Peer B'],
                        row['Peer C'],
                        datetime.now(),
                        row['Ticker']
                    ))
                    updated_count += 1
                    
                else:
                    # Insert new record
                    insert_query = """
                    INSERT INTO stocks (
                        ticker, company_name, sector, industry, market_cap_b,
                        description, business_model, products_services, main_customers,
                        markets, moat_1, moat_2, moat_3, moat_4,
                        peer_a, peer_b, peer_c, last_updated
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """
                    
                    cursor.execute(insert_query, (
                        row['Ticker'],
                        row['Company Name'],
                        row['Sector'],
                        row['Industry'],
                        row['Market Cap (B)'],
                        row['Description'],
                        row['Business_Model'],
                        row['Products_Services'],
                        row['Main_Customers'],
                        row['Markets'],
                        row['Moat 1'],
                        row['Moat 2'],
                        row['Moat 3'],
                        row['Moat 4'],
                        row['Peer A'],
                        row['Peer B'],
                        row['Peer C'],
                        datetime.now()
                    ))
                    inserted_count += 1
                
                # Commit every 10 records
                if (index + 1) % 10 == 0:
                    conn.commit()
                    logger.info(f"Processed {index + 1} records...")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error processing {row['Ticker']}: {e}")
                continue
        
        # Final commit
        conn.commit()
        
        logger.info(f"Batch9 upload completed:")
        logger.info(f"  - Updated: {updated_count} records")
        logger.info(f"  - Inserted: {inserted_count} records")
        logger.info(f"  - Errors: {error_count} records")
        
        return updated_count, inserted_count, error_count
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function to upload batch9.csv"""
    logger.info("Starting batch9.csv upload process...")
    
    try:
        # Read and clean data
        df = read_batch9_csv()
        df = clean_data(df)
        
        # Upload to database
        updated, inserted, errors = update_stocks_table(df)
        
        logger.info("Batch9 upload process completed successfully!")
        
    except Exception as e:
        logger.error(f"Batch9 upload process failed: {e}")
        raise

if __name__ == "__main__":
    main() 