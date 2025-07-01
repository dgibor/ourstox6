import pandas as pd
import os

def show_missing_summary():
    """Display a summary of missing tickers"""
    
    csv_file = '../pre_filled_stocks/missing_data/missing_tickers.csv'
    
    if not os.path.exists(csv_file):
        print("❌ Missing tickers CSV file not found!")
        return
    
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    print("🔍 MISSING TICKERS ANALYSIS")
    print("=" * 50)
    print(f"📊 Total tickers with missing information: {len(df)}")
    print()
    
    # Count missing fields
    missing_description = len(df[df['description'].isna() | (df['description'] == '')])
    missing_business_model = len(df[df['business_model'].isna() | (df['business_model'] == '')])
    missing_market_cap = len(df[df['market_cap_b'].isna()])
    missing_moat = len(df[df['moat_1'].isna() | (df['moat_1'] == '')])
    
    print("📋 Missing Data Breakdown:")
    print(f"   - Missing description: {missing_description}")
    print(f"   - Missing business model: {missing_business_model}")
    print(f"   - Missing market cap: {missing_market_cap}")
    print(f"   - Missing moat data: {missing_moat}")
    print()
    
    # Show some tickers that have partial data
    print("📝 Sample Tickers with Partial Data:")
    partial_data = df[
        (df['description'].notna() & (df['description'] != '')) |
        (df['business_model'].notna() & (df['business_model'] != '')) |
        (df['market_cap_b'].notna())
    ].head(10)
    
    for _, row in partial_data.iterrows():
        has_desc = "✅" if row['description'] and str(row['description']).strip() else "❌"
        has_model = "✅" if row['business_model'] and str(row['business_model']).strip() else "❌"
        has_cap = "✅" if pd.notna(row['market_cap_b']) else "❌"
        has_moat = "✅" if row['moat_1'] and str(row['moat_1']).strip() else "❌"
        
        print(f"   - {row['ticker']}: {row['company_name']}")
        print(f"     Desc: {has_desc} | Model: {has_model} | Cap: {has_cap} | Moat: {has_moat}")
    
    print()
    print("📁 Files Created:")
    print("   - CSV file: pre_filled_stocks/missing_data/missing_tickers.csv")
    print("   - Summary: pre_filled_stocks/missing_data/missing_data_summary.md")
    print()
    print("💡 Next Steps:")
    print("   1. Review the CSV file to see all missing tickers")
    print("   2. Prioritize tickers by market cap or sector")
    print("   3. Create additional batch files for missing data")
    print("   4. Run the update function again with new data")

if __name__ == "__main__":
    show_missing_summary() 