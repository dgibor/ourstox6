import os
import psycopg2
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT'),
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD')
}

API_LIMITS = {
    'yahoo': {'calls_per_hour': 2000, 'calls_per_day': 20000, 'reset_hour': 0},
    'finnhub': {'calls_per_minute': 60, 'calls_per_day': 86400, 'reset_hour': 0},
    'alphavantage': {'calls_per_minute': 5, 'calls_per_day': 500, 'reset_hour': 0}
}

class APIRateLimiter:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)
        self.cur = self.conn.cursor()

    def check_limit(self, provider: str, endpoint: str) -> bool:
        """Return True if under limit, False if limit reached."""
        today = datetime.utcnow().date()
        self.cur.execute(
            "SELECT calls_made, calls_limit FROM api_usage_tracking WHERE api_provider=%s AND date=%s AND endpoint=%s",
            (provider, today, endpoint)
        )
        row = self.cur.fetchone()
        if row:
            calls_made, calls_limit = row
            limit = API_LIMITS[provider]['calls_per_day']
            return calls_made < limit
        else:
            return True  # No record yet, under limit

    def record_call(self, provider: str, endpoint: str) -> None:
        today = datetime.utcnow().date()
        self.cur.execute(
            "SELECT calls_made FROM api_usage_tracking WHERE api_provider=%s AND date=%s AND endpoint=%s",
            (provider, today, endpoint)
        )
        row = self.cur.fetchone()
        if row:
            self.cur.execute(
                "UPDATE api_usage_tracking SET calls_made = calls_made + 1 WHERE api_provider=%s AND date=%s AND endpoint=%s",
                (provider, today, endpoint)
            )
        else:
            self.cur.execute(
                "INSERT INTO api_usage_tracking (api_provider, date, endpoint, calls_made, calls_limit) VALUES (%s, %s, %s, 1, %s)",
                (provider, today, endpoint, API_LIMITS[provider]['calls_per_day'])
            )
        self.conn.commit()

    def get_next_available_time(self, provider: str) -> datetime:
        now = datetime.utcnow()
        reset_hour = API_LIMITS[provider].get('reset_hour', 0)
        tomorrow = now + timedelta(days=1)
        reset_time = datetime.combine(tomorrow.date(), datetime.min.time()) + timedelta(hours=reset_hour)
        return reset_time

    def queue_request(self, provider: str, request_data: dict) -> None:
        # For demo: just print, in production use a real queue
        print(f"Queued request for {provider}: {request_data}")

    def close(self):
        self.cur.close()
        self.conn.close()

if __name__ == "__main__":
    # Simple test
    limiter = APIRateLimiter()
    provider = 'yahoo'
    endpoint = '/v1/finance/financials'
    print('Under limit:', limiter.check_limit(provider, endpoint))
    limiter.record_call(provider, endpoint)
    print('Recorded call.')
    print('Next available time:', limiter.get_next_available_time(provider))
    limiter.close() 