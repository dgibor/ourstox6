# Daily Run Folder - Unused Files Analysis

*Generated: July 11, 2025*

This document analyzes all files in the `daily_run` folder and identifies which ones are not being used in the current production system, what they do, and which database tables they connect to.

## 📊 Summary

**Total Files in daily_run:** 40+ files
**Currently Used (Production):** 11 files
**Unused/Legacy:** 29+ files
**Archive Folders:** 3 directories

---

## 🟢 CURRENTLY USED FILES (Production System)

These files are actively used by the main `daily_trading_system.py`:

### Core System Files
| File | Purpose | Database Tables | Import Status |
|------|---------|----------------|---------------|
| `daily_trading_system.py` | Main orchestrator | `daily_charts`, `stocks`, `company_fundamentals` | ✅ Used |
| `database.py` | Database manager | All tables | ✅ Used |
| `config.py` | Configuration management | None (config only) | ✅ Used |
| `check_market_schedule.py` | Market calendar checking | None | ✅ Used |

### Data Processing Files
| File | Purpose | Database Tables | Import Status |
|------|---------|----------------|---------------|
| `batch_price_processor.py` | Batch price updates | `daily_charts` | ✅ Used |
| `earnings_based_fundamental_processor.py` | Fundamental updates | `company_fundamentals`, `earnings_calendar` | ✅ Used |
| `data_validator.py` | Data validation | None (validation only) | ✅ Used |
| `circuit_breaker.py` | Service fallback management | None | ✅ Used |

### Support Files
| File | Purpose | Database Tables | Import Status |
|------|---------|----------------|---------------|
| `common_imports.py` | Shared imports | None | ✅ Used |
| `error_handler.py` | Error management | None | ✅ Used |
| `monitoring.py` | System monitoring | Various (health checks) | ✅ Used |

### Indicator Files (Used by technical calculations)
All files in `indicators/` directory are used:
- `rsi.py`, `ema.py`, `macd.py`, `bollinger_bands.py`, `atr.py`, `cci.py`, `stochastic.py`, `vwap.py`, `adx.py`, `support_resistance.py`

---

## 🔴 UNUSED FILES (Not in Production Workflow)

### 1. Alternative Service Implementations

#### `fmp_service.py` (26KB, 534 lines)
- **Purpose**: Financial Modeling Prep API service implementation
- **Database Tables**: `company_fundamentals`, `stocks`
- **Why Unused**: Replaced by simplified service in `batch_price_processor.py`
- **SQL Operations**: `DELETE FROM company_fundamentals`, `INSERT INTO company_fundamentals`
- **Status**: 🗑️ Can be archived (functionality replaced)

#### `alpha_vantage_service.py` (25KB, 539 lines)
- **Purpose**: Alpha Vantage API service implementation
- **Database Tables**: `fundamentals`, `key_statistics` (non-standard tables)
- **Why Unused**: Not integrated into main workflow
- **SQL Operations**: `INSERT INTO fundamentals`, `INSERT INTO key_statistics`
- **Status**: 🔄 Could be integrated for redundancy

#### `enhanced_service_factory.py` (13KB, 344 lines)
- **Purpose**: Advanced service factory with monitoring
- **Database Tables**: None directly
- **Why Unused**: Main system uses simpler service instantiation
- **Status**: 🔄 Could replace current service management

#### `service_factory.py` (7.8KB, 210 lines)
- **Purpose**: Basic service factory
- **Database Tables**: None
- **Why Unused**: Superseded by enhanced version
- **Status**: 🗑️ Can be archived

#### `base_service.py` (7.9KB, 212 lines)
- **Purpose**: Abstract base class for services
- **Database Tables**: None
- **Why Unused**: Services don't inherit from base class in current system
- **Status**: 🔄 Could be used for better service standardization

### 2. Legacy Update Scripts

#### `update_company_fundamentals.py` (10KB, 266 lines)
- **Purpose**: Legacy fundamental data updater
- **Database Tables**: `company_fundamentals`
- **Why Unused**: Replaced by `earnings_based_fundamental_processor.py`
- **SQL Operations**: `INSERT INTO company_fundamentals`
- **Status**: 🗑️ Can be archived

#### `update_company_fundamentals_fixed.py` (10KB, 274 lines)
- **Purpose**: Fixed version of legacy updater
- **Database Tables**: `company_fundamentals`
- **Why Unused**: Replaced by new earnings-based approach
- **SQL Operations**: `INSERT INTO company_fundamentals`
- **Status**: 🗑️ Can be archived

#### `update_missing_data.py` (2.6KB, 75 lines)
- **Purpose**: Quick fix for missing data
- **Database Tables**: `stocks`
- **Why Unused**: One-time fix, not part of daily workflow
- **SQL Operations**: `UPDATE stocks SET`
- **Status**: 🗑️ Can be archived

#### `update_all_fundamental_scores.py` (13KB, 343 lines)
- **Purpose**: Score calculation system
- **Database Tables**: `stocks`, score-related tables
- **Why Unused**: Scoring system not implemented in main workflow
- **SQL Operations**: `SELECT ticker FROM stocks`
- **Status**: 🔄 Could be integrated if scoring is needed

#### `update_fundamental_scores.py` (2.5KB, 63 lines)
- **Purpose**: Simple score updater
- **Database Tables**: Score-related tables
- **Why Unused**: Part of unimplemented scoring system
- **Status**: 🗑️ Can be archived

### 3. Complex Alternative Workflows

#### `multi_service_data_workflow.py` (40KB, 977 lines)
- **Purpose**: Comprehensive multi-service data fetching workflow
- **Database Tables**: `daily_charts`, `company_fundamentals`
- **Why Unused**: Too complex for current needs, replaced by simpler approach
- **SQL Operations**: `INSERT INTO daily_charts`, `SELECT id FROM company_fundamentals`
- **Status**: 🔄 Could be valuable for comprehensive data validation

#### `system_health_check.py` (28KB, 792 lines)
- **Purpose**: Comprehensive system health monitoring
- **Database Tables**: All tables (for health checks)
- **Why Unused**: Basic monitoring in `monitoring.py` is sufficient
- **SQL Operations**: Multiple SELECT queries for health metrics
- **Status**: 🔄 Could be valuable for production monitoring

### 4. Table Creation and Setup

#### `create_earnings_calendar_table.py` (9.2KB, 286 lines)
- **Purpose**: Creates earnings calendar and related tables
- **Database Tables**: `earnings_calendar`, `financial_ratios`, `system_status`, `daily_charts`
- **Why Unused**: Tables created by other means
- **SQL Operations**: `CREATE TABLE` statements
- **Status**: 🔄 Could be useful for fresh installations

#### `earnings_calendar_service.py` (26KB, 623 lines)
- **Purpose**: Earnings calendar data service
- **Database Tables**: `earnings_calendar`
- **Why Unused**: Earnings integration simplified in main system
- **SQL Operations**: `CREATE TABLE`, `INSERT INTO earnings_calendar`
- **Status**: 🔄 Could be integrated for better earnings tracking

### 5. Utility and Support Files

#### `ratio_calculator.py` (3.2KB, 80 lines)
- **Purpose**: Financial ratio calculations
- **Database Tables**: None (calculation only)
- **Why Unused**: Ratios calculated inline in other services
- **Status**: ✅ Actually used by `fmp_service.py` (which is unused)

#### `exceptions.py` (3.4KB, 102 lines)
- **Purpose**: Custom exception classes
- **Database Tables**: None
- **Why Unused**: Simple error handling used instead
- **Status**: 🔄 Could improve error handling

### 6. Empty/Broken Files

#### `daily_earnings_update.py` (1GB, 1 line)
- **Purpose**: Unknown (file is corrupted/empty)
- **Database Tables**: Unknown
- **Why Unused**: File appears corrupted
- **Status**: 🗑️ Should be deleted immediately

### 7. Documentation Files (Not Code)

These are markdown files and don't connect to databases:
- `COMPREHENSIVE_SERVICE_RECOMMENDATIONS.md`
- `OPTIMIZED_SERVICE_PRIORITY.md`
- `SERVICE_PRIORITY_ANALYSIS.md`
- `MULTI_SERVICE_SOLUTION_SUMMARY.md`
- `SYSTEM_DOCUMENTATION.md`
- `DAILY_RUN_FOLDER_SUMMARY.md`
- `IMPLEMENTATION_STATUS.md`
- `PRODUCTION_FILES_LIST.md`
- `ARCHIVE_SUMMARY.md`
- `BATCH_PROCESSING_LOGIC.md`

**Status**: 📚 Keep for reference

---

## 📁 ARCHIVE DIRECTORIES

### `archive_non_essential_20250624_010014/`
- Contains old debugging and test files
- **Status**: 🗑️ Can be deleted (already archived)

### `archive_conflicting_pipelines/`
- Contains conflicting pipeline implementations
- **Status**: 🗑️ Can be deleted (conflicts resolved)

### `archive_20250622_215640/`
- Contains older archived files
- **Status**: 🗑️ Can be deleted (superseded)

### `archive_temp_files/`
- Contains temporary files
- **Status**: 🗑️ Can be deleted

---

## 🎯 RECOMMENDATIONS

### Immediate Actions (Can Delete)
1. **Delete corrupted file**: `daily_earnings_update.py` (1GB corrupted file)
2. **Archive legacy updaters**: `update_company_fundamentals*.py`, `update_missing_data.py`
3. **Archive superseded services**: `service_factory.py`
4. **Delete archive directories**: All `archive_*` folders

### Consider for Integration
1. **`system_health_check.py`**: Comprehensive monitoring for production
2. **`alpha_vantage_service.py`**: Additional data source for redundancy
3. **`enhanced_service_factory.py`**: Better service management
4. **`exceptions.py`**: Improved error handling
5. **`multi_service_data_workflow.py`**: For comprehensive data validation

### Keep for Reference
1. All markdown documentation files
2. **`create_earnings_calendar_table.py`**: For fresh installations
3. **`earnings_calendar_service.py`**: For future earnings integration

---

## 📋 DATABASE TABLE USAGE SUMMARY

### Heavily Used Tables (by production system)
- `daily_charts`: Price data storage
- `stocks`: Stock information
- `company_fundamentals`: Fundamental data

### Lightly Used Tables
- `earnings_calendar`: Only by earnings service
- `market_etf`: Only for ETF data

### Unused Tables (referenced in unused files)
- `fundamentals`: Alpha Vantage specific
- `key_statistics`: Alpha Vantage specific
- `financial_ratios`: Scoring system
- `system_status`: Health monitoring

---

## 💾 DISK SPACE SAVINGS

**Potential savings by archiving unused files:**
- Large files: `multi_service_data_workflow.py` (40KB), `system_health_check.py` (28KB)
- **Corrupted file**: `daily_earnings_update.py` (1GB!) ⚠️ **Priority deletion**
- Total estimated savings: ~1GB+ (mostly from corrupted file)

**Files to keep for potential integration:** ~200KB
**Files safe to archive:** ~500KB (excluding corrupted file)

---

*This analysis helps maintain a clean, efficient production system while preserving valuable code for future enhancements.* 