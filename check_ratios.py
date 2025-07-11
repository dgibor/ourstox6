from daily_run.database import DatabaseManager

def check_ratios():
    db = DatabaseManager()
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    
    required_ratios = ['pe_ratio', 'pb_ratio', 'roe', 'debt_to_equity', 'current_ratio', 'revenue_growth_yoy', 'earnings_growth_yoy']
    
    for ticker in tickers:
        print(f'\n{ticker} ratios:')
        result = db.execute_query('''
            SELECT pe_ratio, pb_ratio, roe, debt_to_equity, current_ratio, revenue_growth_yoy, earnings_growth_yoy 
            FROM financial_ratios 
            WHERE ticker = %s 
            ORDER BY calculation_date DESC 
            LIMIT 1
        ''', (ticker,))
        
        if result:
            row = result[0]
            available_count = sum(1 for val in row if val is not None)
            quality_score = int((available_count / len(required_ratios)) * 100)
            
            print(f'  PE: {row[0]}, PB: {row[1]}, ROE: {row[2]}, D/E: {row[3]}, Current: {row[4]}, Rev Growth: {row[5]}, EPS Growth: {row[6]}')
            print(f'  Available: {available_count}/{len(required_ratios)} ratios')
            print(f'  Quality Score: {quality_score}%')
            print(f'  Status: {"success" if quality_score >= 80 else "partial" if quality_score >= 50 else "failed"}')
        else:
            print('  No data')
    
    db.disconnect()

if __name__ == "__main__":
    check_ratios() 