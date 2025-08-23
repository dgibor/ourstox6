#!/usr/bin/env python3
"""
Updated Analyst Database Manager
Handles storing, updating, and querying analyst data in the database
Now integrates with multi-account Finnhub system for Priority 6 daily runs
"""
import logging
import sys
from datetime import datetime, date, timedelta
from typing import Dict, List, Optional, Any
import pandas as pd

try:
    from daily_run.database import DatabaseManager
except ImportError:
    from database import DatabaseManager

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class AnalystDatabaseManager:
    """
    Manages analyst data storage and retrieval from database
    Now uses multi-account Finnhub system as primary method
    """
    
    def __init__(self):
        self.db = DatabaseManager()
        self.multi_account_collector = None
        self.legacy_analyst_service = None
    
    def _initialize_multi_account_collector(self):
        """Initialize the multi-account Finnhub collector"""
        try:
            if self.multi_account_collector is None:
                import sys
                import os
                from pathlib import Path
                
                # Add parent directory to path for multi-account modules
                current_dir = os.path.dirname(os.path.abspath(__file__))
                parent_dir = os.path.dirname(current_dir)
                
                if parent_dir not in sys.path:
                    sys.path.insert(0, parent_dir)
                
                from multi_account_analyst_with_database import MultiAccountAnalystCollectorWithDB
                self.multi_account_collector = MultiAccountAnalystCollectorWithDB()
                logger.info("✅ Multi-Account Analyst Collector initialized successfully")
                return True
                
        except ImportError as e:
            logger.error(f"❌ Failed to import Multi-Account Analyst Collector: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error initializing Multi-Account Analyst Collector: {e}")
            return False
    
    def _initialize_legacy_service(self):
        """Initialize legacy analyst service as fallback"""
        try:
            if self.legacy_analyst_service is None:
                from analyst_data_service import AnalystDataService
                self.legacy_analyst_service = AnalystDataService()
                logger.info("✅ Legacy Analyst Service initialized as fallback")
                return True
                
        except ImportError as e:
            logger.error(f"❌ Failed to import Legacy Analyst Service: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Error initializing Legacy Analyst Service: {e}")
            return False
    
    def collect_and_store_analyst_data(self, tickers: List[str]) -> Dict[str, Any]:
        """
        PRIORITY 6: Collect and store analyst data for multiple tickers
        Primary: Multi-account Finnhub system
        Fallback: Legacy analyst service
        """
        try:
            logger.info(f"🎯 PRIORITY 6: Collecting analyst data for {len(tickers)} tickers")
            
            results = {
                'total_tickers': len(tickers),
                'successful_storage': 0,
                'failed_storage': 0,
                'tickers_processed': [],
                'tickers_failed': [],
                'system_used': 'unknown',
                'processing_time': 0
            }
            
            start_time = datetime.now()
            
            # Try multi-account system first
            if self._initialize_multi_account_collector():
                logger.info("🚀 Using multi-account Finnhub system for analyst data collection")
                results = self._collect_with_multi_account_system(tickers)
                results['system_used'] = 'multi_account_finnhub'
            else:
                logger.warning("⚠️ Multi-account system unavailable, trying legacy service...")
                
                if self._initialize_legacy_service():
                    logger.info("🔄 Using legacy analyst service as fallback")
                    results = self._collect_with_legacy_service(tickers)
                    results['system_used'] = 'legacy_service'
                else:
                    logger.error("❌ Both systems failed to initialize")
                    results['error'] = 'All analyst data collection systems failed to initialize'
                    return results
            
            # Calculate processing time
            end_time = datetime.now()
            results['processing_time'] = (end_time - start_time).total_seconds()
            
            # Log final results
            success_rate = (results['successful_storage'] / results['total_tickers'] * 100) if results['total_tickers'] > 0 else 0
            logger.info(f"🎉 PRIORITY 6: Analyst data collection completed")
            logger.info(f"   System: {results['system_used']}")
            logger.info(f"   Success: {results['successful_storage']}/{results['total_tickers']} ({success_rate:.1f}%)")
            logger.info(f"   Processing time: {results['processing_time']:.2f} seconds")
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Critical error in analyst data collection: {e}")
            return {
                'error': str(e),
                'total_tickers': len(tickers),
                'successful_storage': 0,
                'failed_storage': len(tickers),
                'system_used': 'error'
            }
    
    def _collect_with_multi_account_system(self, tickers: List[str]) -> Dict[str, Any]:
        """Collect analyst data using multi-account Finnhub system"""
        try:
            results = {
                'total_tickers': len(tickers),
                'successful_storage': 0,
                'failed_storage': 0,
                'tickers_processed': [],
                'tickers_failed': []
            }
            
            # Process tickers in batches to avoid overwhelming the system
            batch_size = 50  # Process 50 tickers at a time
            for i in range(0, len(tickers), batch_size):
                batch = tickers[i:i + batch_size]
                logger.info(f"📊 Processing batch {i//batch_size + 1}: {len(batch)} tickers")
                
                for ticker in batch:
                    try:
                        # Get analyst data using the new system
                        analyst_data = self.multi_account_collector.get_analyst_data(ticker)
                        
                        if analyst_data:
                            # Store in database using the new system
                            if self.multi_account_collector.save_analyst_data_to_database(analyst_data):
                                results['successful_storage'] += 1
                                results['tickers_processed'].append(ticker)
                                logger.info(f"✅ {ticker} - Data stored successfully via multi-account system")
                            else:
                                results['failed_storage'] += 1
                                results['tickers_failed'].append(ticker)
                                logger.warning(f"⚠️ {ticker} - Failed to store data via multi-account system")
                        else:
                            results['failed_storage'] += 1
                            results['tickers_failed'].append(ticker)
                            logger.warning(f"⚠️ {ticker} - No analyst data available")
                        
                    except Exception as e:
                        logger.error(f"❌ Error processing {ticker}: {e}")
                        results['failed_storage'] += 1
                        results['tickers_failed'].append(ticker)
                
                # Small delay between batches to be respectful to APIs
                if i + batch_size < len(tickers):
                    import time
                    time.sleep(2)
            
            logger.info(f"🎉 Multi-account analyst data collection completed: {results['successful_storage']}/{results['total_tickers']} successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in multi-account analyst data collection: {e}")
            raise e
    
    def _collect_with_legacy_service(self, tickers: List[str]) -> Dict[str, Any]:
        """Fallback to legacy analyst service if multi-account system fails"""
        try:
            logger.info(f"🔄 Using legacy analyst service for {len(tickers)} tickers")
            
            results = {
                'total_tickers': len(tickers),
                'successful_storage': 0,
                'failed_storage': 0,
                'tickers_processed': [],
                'tickers_failed': []
            }
            
            for i, ticker in enumerate(tickers, 1):
                logger.info(f"📊 Processing {ticker} ({i}/{len(tickers)}) with legacy service...")
                
                try:
                    # Get analyst data using legacy service
                    analyst_data = self.legacy_analyst_service.get_comprehensive_analyst_data(ticker)
                    
                    # Store in database
                    if self.store_analyst_data(ticker, analyst_data):
                        results['successful_storage'] += 1
                        results['tickers_processed'].append(ticker)
                        logger.info(f"✅ {ticker} - Data stored successfully via legacy service")
                    else:
                        results['failed_storage'] += 1
                        results['tickers_failed'].append(ticker)
                        logger.warning(f"⚠️ {ticker} - Failed to store data via legacy service")
                        
                except Exception as e:
                    logger.error(f"❌ Error processing {ticker} with legacy service: {e}")
                    results['failed_storage'] += 1
                    results['tickers_failed'].append(ticker)
            
            logger.info(f"🎉 Legacy analyst data collection completed: {results['successful_storage']}/{results['total_tickers']} successful")
            return results
            
        except Exception as e:
            logger.error(f"❌ Error in legacy analyst data collection: {e}")
            raise e
    
    def store_analyst_data(self, ticker: str, analyst_data: Dict[str, Any]) -> bool:
        """
        Store comprehensive analyst data for a ticker
        This method is used by the legacy service fallback
        """
        try:
            if not analyst_data.get('success'):
                logger.warning(f"⚠️ No valid analyst data to store for {ticker}")
                return False
            
            self.db.connect()
            cursor = self.db.connection.cursor()
            
            current_price = self._get_current_stock_price(ticker)
            today = date.today()
            
            success_count = 0
            
            # 1. Store/Update Current Analyst Targets
            if analyst_data.get('target_data'):
                success_count += self._store_current_targets(cursor, ticker, analyst_data['target_data'], current_price)
            
            # 2. Store Historical Target Data
            if analyst_data.get('target_data'):
                success_count += self._store_target_history(cursor, ticker, analyst_data['target_data'], current_price, today)
            
            # 3. Store Rating Trends
            if analyst_data.get('rating_data'):
                success_count += self._store_rating_trends(cursor, ticker, analyst_data['rating_data'], today)
            
            # 4. Store Individual Analyst Actions
            if analyst_data.get('actions_data'):
                success_count += self._store_analyst_actions(cursor, ticker, analyst_data['actions_data'])
            
            # Commit all changes
            self.db.connection.commit()
            cursor.close()
            self.db.disconnect()
            
            logger.info(f"✅ Stored analyst data for {ticker} - {success_count} operations successful")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ Error storing analyst data for {ticker}: {e}")
            if hasattr(self.db, 'connection') and self.db.connection:
                self.db.connection.rollback()
            return False
    
    def _get_current_stock_price(self, ticker: str) -> Optional[float]:
        """Get current stock price for calculations"""
        try:
            self.db.connect()
            cursor = self.db.connection.cursor()
            
            cursor.execute("""
                SELECT close FROM daily_charts 
                WHERE ticker = %s 
                ORDER BY date DESC 
                LIMIT 1
            """, (ticker,))
            
            result = cursor.fetchone()
            cursor.close()
            self.db.disconnect()
            
            if result and result[0]:
                return float(result[0]) / 100  # Convert from cents
            return None
            
        except Exception as e:
            logger.error(f"❌ Error getting current price for {ticker}: {e}")
            return None
    
    def _store_current_targets(self, cursor, ticker: str, target_data: Dict, current_price: float) -> int:
        """Store current analyst targets (latest consensus)"""
        try:
            avg_target = target_data.get('avg_target_price')
            high_target = target_data.get('high_target_price')
            low_target = target_data.get('low_target_price')
            num_analysts = target_data.get('num_analysts', 0)
            data_source = target_data.get('data_source', 'unknown')
            
            # Calculate upside potential
            upside_potential = None
            if avg_target and current_price and current_price > 0:
                upside_potential = ((avg_target - current_price) / current_price) * 100
            
            # Calculate confidence level
            confidence_level = self._calculate_confidence_level(avg_target, high_target, low_target, num_analysts)
            
            # Upsert into analyst_targets table
            upsert_query = """
            INSERT INTO analyst_targets 
            (ticker, avg_target_price, high_target_price, low_target_price, num_analysts, 
             upside_potential, current_price, data_source, confidence_level, last_updated)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (ticker) DO UPDATE SET
                avg_target_price = EXCLUDED.avg_target_price,
                high_target_price = EXCLUDED.high_target_price,
                low_target_price = EXCLUDED.low_target_price,
                num_analysts = EXCLUDED.num_analysts,
                upside_potential = EXCLUDED.upside_potential,
                current_price = EXCLUDED.current_price,
                data_source = EXCLUDED.data_source,
                confidence_level = EXCLUDED.confidence_level,
                last_updated = EXCLUDED.last_updated
            """
            
            cursor.execute(upsert_query, (
                ticker, avg_target, high_target, low_target, num_analysts,
                upside_potential, current_price, data_source, confidence_level, datetime.now()
            ))
            
            return 1
            
        except Exception as e:
            logger.error(f"❌ Error storing current targets for {ticker}: {e}")
            return 0
    
    def _store_target_history(self, cursor, ticker: str, target_data: Dict, current_price: float, date: date) -> int:
        """Store historical target data"""
        try:
            avg_target = target_data.get('avg_target_price')
            high_target = target_data.get('high_target_price')
            low_target = target_data.get('low_target_price')
            num_analysts = target_data.get('num_analysts', 0)
            data_source = target_data.get('data_source', 'unknown')
            
            # Calculate upside potential
            upside_potential = None
            if avg_target and current_price and current_price > 0:
                upside_potential = ((avg_target - current_price) / current_price) * 100
            
            # Insert into analyst_target_history
            insert_query = """
            INSERT INTO analyst_target_history 
            (ticker, date, avg_target_price, high_target_price, low_target_price, 
             num_analysts, upside_potential, current_price, data_source, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                ticker, date, avg_target, high_target, low_target, num_analysts,
                upside_potential, current_price, data_source, datetime.now()
            ))
            
            return 1
            
        except Exception as e:
            logger.error(f"❌ Error storing target history for {ticker}: {e}")
            return 0
    
    def _store_rating_trends(self, cursor, ticker: str, rating_data: Dict, date: date) -> int:
        """Store rating trends data"""
        try:
            strong_buy = rating_data.get('strong_buy', 0)
            buy = rating_data.get('buy', 0)
            hold = rating_data.get('hold', 0)
            sell = rating_data.get('sell', 0)
            strong_sell = rating_data.get('strong_sell', 0)
            total_analysts = rating_data.get('total_analysts', 0)
            consensus_rating = rating_data.get('consensus_rating', 'Hold')
            data_source = rating_data.get('data_source', 'unknown')
            
            # Calculate consensus score
            consensus_score = self._calculate_consensus_score(strong_buy, buy, hold, sell, strong_sell, total_analysts)
            
            # Insert into analyst_rating_trends
            insert_query = """
            INSERT INTO analyst_rating_trends 
            (ticker, period_date, strong_buy_count, buy_count, hold_count, 
             sell_count, strong_sell_count, total_analysts, consensus_rating, 
             consensus_score, data_source, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                ticker, date, strong_buy, buy, hold, sell, strong_sell,
                total_analysts, consensus_rating, consensus_score, data_source, datetime.now()
            ))
            
            return 1
            
        except Exception as e:
            logger.error(f"❌ Error storing rating trends for {ticker}: {e}")
            return 0
    
    def _store_analyst_actions(self, cursor, ticker: str, actions_data: List[Dict]) -> int:
        """Store individual analyst actions"""
        try:
            success_count = 0
            
            for action in actions_data:
                analyst_name = action.get('analyst_name', 'Unknown')
                action_type = action.get('action', 'Unknown')
                rating = action.get('rating', 'Hold')
                target_price = action.get('target_price')
                date = action.get('date', date.today())
                data_source = action.get('data_source', 'unknown')
                
                # Insert into analyst_actions
                insert_query = """
                INSERT INTO analyst_actions 
                (ticker, analyst_name, action, rating, target_price, date, data_source, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                """
                
                cursor.execute(insert_query, (
                    ticker, analyst_name, action_type, rating, target_price, date, data_source, datetime.now()
                ))
                
                success_count += 1
            
            return success_count
            
        except Exception as e:
            logger.error(f"❌ Error storing analyst actions for {ticker}: {e}")
            return 0
    
    def _calculate_confidence_level(self, avg_target: float, high_target: float, low_target: float, num_analysts: int) -> str:
        """Calculate confidence level based on data quality"""
        if not avg_target or num_analysts == 0:
            return "Low"
        
        # Calculate spread as percentage of average
        if high_target and low_target and avg_target > 0:
            spread = ((high_target - low_target) / avg_target) * 100
            if spread < 20:
                confidence = "High"
            elif spread < 40:
                confidence = "Medium"
            else:
                confidence = "Low"
        else:
            confidence = "Medium"
        
        # Adjust based on number of analysts
        if num_analysts >= 20:
            confidence = "High"
        elif num_analysts >= 10:
            if confidence == "Low":
                confidence = "Medium"
        else:
            if confidence == "High":
                confidence = "Medium"
        
        return confidence
    
    def _calculate_consensus_score(self, strong_buy: int, buy: int, hold: int, sell: int, strong_sell: int, total: int) -> float:
        """Calculate consensus score from -2 to +2"""
        if total == 0:
            return 0.0
        
        weighted_score = (strong_buy * 2 + buy * 1 + hold * 0 + sell * -1 + strong_sell * -2) / total
        return round(weighted_score, 2)

def test_analyst_database_manager():
    """Test the updated analyst database manager"""
    try:
        print("🧪 Testing Updated Analyst Database Manager")
        print("=" * 50)
        
        # Initialize manager
        manager = AnalystDatabaseManager()
        
        # Test tickers
        test_tickers = ['AAPL', 'MSFT', 'GOOGL']
        
        print(f"📊 Testing with {len(test_tickers)} tickers...")
        
        # Test collection
        results = manager.collect_and_store_analyst_data(test_tickers)
        
        print(f"✅ Test completed:")
        print(f"   System used: {results.get('system_used', 'unknown')}")
        print(f"   Success: {results.get('successful_storage', 0)}/{results.get('total_tickers', 0)}")
        print(f"   Processing time: {results.get('processing_time', 0):.2f} seconds")
        
        if 'error' in results:
            print(f"   Error: {results['error']}")
        
        return results
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return None

if __name__ == "__main__":
    test_analyst_database_manager()
