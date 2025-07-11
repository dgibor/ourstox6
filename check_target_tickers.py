from daily_run.database import DatabaseManager

def check_ticker_data():
    db = DatabaseManager()
    tickers = ['NVDA', 'MSFT', 'GOOGL', 'AAPL', 'BAC', 'XOM']
    
    print('=== DATA AVAILABILITY CHECK ===')
    for ticker in tickers:
        print(f'\n{ticker}:')
        
        # Check daily charts
        result = db.execute_query('SELECT COUNT(*) FROM daily_charts WHERE ticker = %s', (ticker,))
        charts = result[0][0] if result else 0
        
        # Check fundamentals
        result = db.execute_query('SELECT COUNT(*) FROM company_fundamentals WHERE ticker = %s', (ticker,))
        fund = result[0][0] if result else 0
        
        # Check financial ratios
        result = db.execute_query('SELECT COUNT(*) FROM financial_ratios WHERE ticker = %s', (ticker,))
        ratios = result[0][0] if result else 0
        
        # Check technical indicators
        result = db.execute_query('SELECT COUNT(*) FROM technical_indicators WHERE ticker = %s', (ticker,))
        tech = result[0][0] if result else 0
        
        # Check earnings calendar
        result = db.execute_query('SELECT COUNT(*) FROM earnings_calendar WHERE ticker = %s', (ticker,))
        earnings = result[0][0] if result else 0
        
        print(f'  Daily Charts: {charts}, Fundamentals: {fund}, Ratios: {ratios}, Technical: {tech}, Earnings: {earnings}')
    
    db.disconnect()

if __name__ == "__main__":
    check_ticker_data() 