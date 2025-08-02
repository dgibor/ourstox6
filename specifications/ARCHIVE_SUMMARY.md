# Archive Summary

**Date:** 2025-06-24

All non-essential files (tests, debug scripts, legacy pipelines, and development utilities) have been moved to:

- `archive_non_essential_20250624_010014/`

## What Was Archived
- Test scripts (test_*.py, quick_test.py, etc.)
- Debug scripts (debug_*.py)
- Data validation/check scripts (check_*.py)
- Fix/update/migration scripts (fix_*.py, update_*.py, migrate_*.py)
- Legacy/old pipeline scripts
- Documentation and design drafts not needed for runtime

## What Remains (Production)
- Main production runner: `daily_trading_system.py`
- Core services: Yahoo, Alpha Vantage, Finnhub, FMP
- Batch/fundamental/technical processors
- Database, error handling, monitoring, config
- Indicators directory
- Production documentation (SYSTEM_DOCUMENTATION.md, IMPLEMENTATION_STATUS.md, etc.)

**The production directory is now clean and ready for deployment.**

If you need to restore any file, copy it back from the archive directory. 