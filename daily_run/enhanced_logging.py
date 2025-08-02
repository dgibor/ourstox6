#!/usr/bin/env python3
"""
Enhanced Logging for Daily Trading System
Provides detailed logging about stock updates, ratios, and performance metrics
"""

import logging
import time
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict

@dataclass
class ProcessingMetrics:
    """Metrics for processing operations"""
    total_items: int
    successful: int
    failed: int
    processing_time: float
    api_calls_used: int = 0
    data_quality_score: float = 0.0
    
    @property
    def success_rate(self) -> float:
        return (self.successful / self.total_items * 100) if self.total_items > 0 else 0.0

class EnhancedLogger:
    """Enhanced logger with detailed metrics and structured output"""
    
    def __init__(self, logger_name: str = "daily_trading_system"):
        self.logger = logging.getLogger(logger_name)
        self.start_time = time.time()
        self.metrics = {}
        
    def log_phase_start(self, phase_name: str, description: str = ""):
        """Log the start of a processing phase"""
        self.logger.info("=" * 80)
        self.logger.info(f"🚀 PHASE START: {phase_name.upper()}")
        if description:
            self.logger.info(f"📝 Description: {description}")
        self.logger.info(f"⏰ Start Time: {datetime.now()}")
        self.logger.info("=" * 80)
        
    def log_phase_complete(self, phase_name: str, metrics: ProcessingMetrics, details: Dict = None):
        """Log the completion of a processing phase with detailed metrics"""
        self.logger.info("=" * 80)
        self.logger.info(f"✅ PHASE COMPLETE: {phase_name.upper()}")
        self.logger.info(f"📊 Processing Metrics:")
        self.logger.info(f"   • Total Items: {metrics.total_items}")
        self.logger.info(f"   • Successful: {metrics.successful}")
        self.logger.info(f"   • Failed: {metrics.failed}")
        self.logger.info(f"   • Success Rate: {metrics.success_rate:.1f}%")
        self.logger.info(f"   • Processing Time: {metrics.processing_time:.2f}s")
        if metrics.api_calls_used > 0:
            self.logger.info(f"   • API Calls Used: {metrics.api_calls_used}")
        if metrics.data_quality_score > 0:
            self.logger.info(f"   • Data Quality Score: {metrics.data_quality_score:.2f}")
        
        if details:
            self.logger.info(f"📋 Additional Details:")
            for key, value in details.items():
                if isinstance(value, list):
                    self.logger.info(f"   • {key}: {len(value)} items")
                elif isinstance(value, dict):
                    self.logger.info(f"   • {key}: {len(value)} entries")
                else:
                    self.logger.info(f"   • {key}: {value}")
        
        self.logger.info(f"⏰ End Time: {datetime.now()}")
        self.logger.info("=" * 80)
        
    def log_stock_updates(self, operation: str, tickers: List[str], successful: List[str], failed: List[str]):
        """Log detailed information about stock updates"""
        self.logger.info(f"📈 {operation.upper()} - DETAILED RESULTS:")
        self.logger.info(f"   • Total Tickers: {len(tickers)}")
        self.logger.info(f"   • Successful Updates: {len(successful)}")
        self.logger.info(f"   • Failed Updates: {len(failed)}")
        
        if successful:
            self.logger.info(f"   ✅ Successfully Updated ({len(successful)}):")
            # Log in groups of 10 for readability
            for i in range(0, len(successful), 10):
                group = successful[i:i+10]
                self.logger.info(f"      {', '.join(group)}")
        
        if failed:
            self.logger.info(f"   ❌ Failed Updates ({len(failed)}):")
            for i in range(0, len(failed), 10):
                group = failed[i:i+10]
                self.logger.info(f"      {', '.join(group)}")
                
    def log_ratio_calculations(self, ticker: str, ratios_calculated: Dict[str, float], ratios_failed: List[str]):
        """Log detailed information about ratio calculations"""
        self.logger.info(f"📊 RATIO CALCULATIONS FOR {ticker}:")
        self.logger.info(f"   • Total Ratios: {len(ratios_calculated) + len(ratios_failed)}")
        self.logger.info(f"   • Successfully Calculated: {len(ratios_calculated)}")
        self.logger.info(f"   • Failed Calculations: {len(ratios_failed)}")
        
        if ratios_calculated:
            self.logger.info(f"   ✅ Calculated Ratios:")
            for ratio_name, value in ratios_calculated.items():
                if value is not None:
                    self.logger.info(f"      • {ratio_name}: {value:.4f}")
                else:
                    self.logger.info(f"      • {ratio_name}: None")
        
        if ratios_failed:
            self.logger.info(f"   ❌ Failed Ratios:")
            for ratio_name in ratios_failed:
                self.logger.info(f"      • {ratio_name}")
                
    def log_technical_indicators(self, ticker: str, indicators_calculated: Dict[str, float], indicators_failed: List[str]):
        """Log detailed information about technical indicator calculations"""
        self.logger.info(f"📈 TECHNICAL INDICATORS FOR {ticker}:")
        self.logger.info(f"   • Total Indicators: {len(indicators_calculated) + len(indicators_failed)}")
        self.logger.info(f"   • Successfully Calculated: {len(indicators_calculated)}")
        self.logger.info(f"   • Failed Calculations: {len(indicators_failed)}")
        
        if indicators_calculated:
            # Group indicators by category for better readability
            categories = {
                'Momentum': ['rsi_14', 'stoch_k', 'stoch_d', 'cci_20', 'williams_r'],
                'Trend': ['ema_20', 'ema_50', 'macd_line', 'macd_signal', 'macd_histogram', 'adx_14'],
                'Volatility': ['bb_upper', 'bb_middle', 'bb_lower', 'atr_14'],
                'Volume': ['obv', 'vpt', 'vwap'],
                'Support/Resistance': ['pivot_point', 'resistance_1', 'support_1', 'resistance_2', 'support_2']
            }
            
            for category, indicator_names in categories.items():
                category_indicators = {k: v for k, v in indicators_calculated.items() if k in indicator_names}
                if category_indicators:
                    self.logger.info(f"   📊 {category} Indicators:")
                    for indicator_name, value in category_indicators.items():
                        if value is not None:
                            self.logger.info(f"      • {indicator_name}: {value:.4f}")
                        else:
                            self.logger.info(f"      • {indicator_name}: None")
        
        if indicators_failed:
            self.logger.info(f"   ❌ Failed Indicators:")
            for indicator_name in indicators_failed:
                self.logger.info(f"      • {indicator_name}")
                
    def log_performance_summary(self, total_processing_time: float, phase_metrics: Dict[str, ProcessingMetrics]):
        """Log a comprehensive performance summary"""
        self.logger.info("=" * 80)
        self.logger.info("📊 COMPREHENSIVE PERFORMANCE SUMMARY")
        self.logger.info("=" * 80)
        
        total_items = sum(m.total_items for m in phase_metrics.values())
        total_successful = sum(m.successful for m in phase_metrics.values())
        total_failed = sum(m.failed for m in phase_metrics.values())
        total_api_calls = sum(m.api_calls_used for m in phase_metrics.values())
        
        self.logger.info(f"🎯 OVERALL METRICS:")
        self.logger.info(f"   • Total Processing Time: {total_processing_time:.2f}s")
        self.logger.info(f"   • Total Items Processed: {total_items}")
        self.logger.info(f"   • Total Successful: {total_successful}")
        self.logger.info(f"   • Total Failed: {total_failed}")
        self.logger.info(f"   • Overall Success Rate: {(total_successful/total_items*100):.1f}%" if total_items > 0 else "N/A")
        self.logger.info(f"   • Total API Calls Used: {total_api_calls}")
        
        self.logger.info(f"📋 PHASE BREAKDOWN:")
        for phase_name, metrics in phase_metrics.items():
            self.logger.info(f"   • {phase_name}:")
            self.logger.info(f"     - Items: {metrics.total_items}")
            self.logger.info(f"     - Success Rate: {metrics.success_rate:.1f}%")
            self.logger.info(f"     - Time: {metrics.processing_time:.2f}s")
            if metrics.api_calls_used > 0:
                self.logger.info(f"     - API Calls: {metrics.api_calls_used}")
        
        self.logger.info("=" * 80)
        
    def log_error_details(self, operation: str, error: Exception, context: Dict = None):
        """Log detailed error information"""
        self.logger.error("=" * 80)
        self.logger.error(f"❌ ERROR IN {operation.upper()}")
        self.logger.error(f"🚨 Error Type: {type(error).__name__}")
        self.logger.error(f"📝 Error Message: {str(error)}")
        
        if context:
            self.logger.error(f"🔍 Error Context:")
            for key, value in context.items():
                self.logger.error(f"   • {key}: {value}")
        
        import traceback
        self.logger.error(f"🔍 Full Traceback:")
        self.logger.error(traceback.format_exc())
        self.logger.error("=" * 80)

# Global enhanced logger instance
enhanced_logger = EnhancedLogger() 