import os
import psycopg2
import pandas as pd
from dotenv import load_dotenv
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/find_missing_tickers.log'),
        logging.StreamHandler()
    ]
)

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

def find_missing_tickers():
    """Find tickers that don't have the new information and create a CSV file"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        logging.info("🔍 Finding tickers with missing information...")
        
        # Query to find tickers missing the new information
        query = """
        SELECT 
            ticker,
            company_name,
            sector,
            industry,
            market_cap,
            exchange,
            country,
            description,
            business_model,
            market_cap_b,
            moat_1,
            moat_2,
            moat_3,
            moat_4,
            peer_a,
            peer_b,
            peer_c
        FROM stocks 
        WHERE 
            description IS NULL 
            OR description = ''
            OR business_model IS NULL 
            OR business_model = ''
            OR market_cap_b IS NULL
            OR moat_1 IS NULL 
            OR moat_1 = ''
        ORDER BY ticker
        """
        
        cur.execute(query)
        results = cur.fetchall()
        
        # Get column names
        columns = [desc[0] for desc in cur.description]
        
        # Create DataFrame
        df = pd.DataFrame(results, columns=columns)
        
        logging.info(f"📊 Found {len(df)} tickers with missing information")
        
        if len(df) > 0:
            # Create output directory if it doesn't exist
            output_dir = '../pre_filled_stocks/missing_data'
            os.makedirs(output_dir, exist_ok=True)
            
            # Save to CSV
            output_file = f'{output_dir}/missing_tickers.csv'
            df.to_csv(output_file, index=False)
            
            logging.info(f"💾 Saved missing tickers to: {output_file}")
            
            # Create a summary report
            create_summary_report(df, output_dir)
            
            # Display sample of missing tickers
            logging.info("\n📋 Sample of tickers with missing information:")
            for i, row in df.head(10).iterrows():
                logging.info(f"   - {row['ticker']}: {row['company_name']}")
            
            if len(df) > 10:
                logging.info(f"   ... and {len(df) - 10} more")
                
        else:
            logging.info("✅ All tickers have complete information!")
            
        return df
        
    except Exception as e:
        logging.error(f"❌ Error finding missing tickers: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def create_summary_report(df, output_dir):
    """Create a summary report of missing data"""
    
    # Count missing fields by type
    missing_description = len(df[df['description'].isna() | (df['description'] == '')])
    missing_business_model = len(df[df['business_model'].isna() | (df['business_model'] == '')])
    missing_market_cap = len(df[df['market_cap_b'].isna()])
    missing_moat = len(df[df['moat_1'].isna() | (df['moat_1'] == '')])
    
    # Create summary
    summary = f"""
# Missing Data Summary Report

## Overview
Total tickers with missing information: {len(df)}

## Missing Data Breakdown
- Missing description: {missing_description}
- Missing business model: {missing_business_model}
- Missing market cap: {missing_market_cap}
- Missing moat data: {missing_moat}

## Sample Missing Tickers
"""
    
    # Add sample tickers to summary
    for i, row in df.head(20).iterrows():
        summary += f"- {row['ticker']}: {row['company_name']}\n"
    
    if len(df) > 20:
        summary += f"\n... and {len(df) - 20} more tickers\n"
    
    # Save summary report
    summary_file = f'{output_dir}/missing_data_summary.md'
    with open(summary_file, 'w') as f:
        f.write(summary)
    
    logging.info(f"📄 Summary report saved to: {summary_file}")

def analyze_data_completeness():
    """Analyze overall data completeness in the database"""
    
    conn = psycopg2.connect(**DB_CONFIG)
    cur = conn.cursor()
    
    try:
        logging.info("\n📈 Analyzing overall data completeness...")
        
        # Get total count
        cur.execute("SELECT COUNT(*) FROM stocks")
        total_count = cur.fetchone()[0]
        
        # Count records with each field
        fields = ['description', 'business_model', 'market_cap_b', 'moat_1', 'peer_a']
        completeness = {}
        
        for field in fields:
            cur.execute(f"SELECT COUNT(*) FROM stocks WHERE {field} IS NOT NULL AND {field} != ''")
            count = cur.fetchone()[0]
            percentage = (count / total_count) * 100
            completeness[field] = {'count': count, 'percentage': percentage}
        
        logging.info(f"📊 Total stocks in database: {total_count}")
        logging.info("📋 Data completeness by field:")
        
        for field, stats in completeness.items():
            logging.info(f"   - {field}: {stats['count']} ({stats['percentage']:.1f}%)")
        
        return completeness
        
    except Exception as e:
        logging.error(f"❌ Error analyzing data completeness: {e}")
        return None
    finally:
        cur.close()
        conn.close()

def main():
    """Main execution function"""
    logging.info("🚀 Starting missing tickers analysis...")
    
    # Analyze overall completeness
    completeness = analyze_data_completeness()
    
    # Find missing tickers
    missing_df = find_missing_tickers()
    
    if missing_df is not None and len(missing_df) > 0:
        logging.info(f"\n🎯 Analysis complete! Found {len(missing_df)} tickers with missing information.")
        logging.info("📁 Check the 'pre_filled_stocks/missing_data/' directory for the CSV file and summary report.")
    else:
        logging.info("\n🎉 All tickers have complete information!")

if __name__ == "__main__":
    main() 