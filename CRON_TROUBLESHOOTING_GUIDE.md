# Cron Job Troubleshooting Guide

## 🚨 **Current Issue: Cron Job Crashes**

Your Railway cron job is crashing. This guide provides step-by-step solutions to identify and fix the problems.

---

## 🔧 **Immediate Solutions**

### **✅ Solution 1: Run the Debug Script**

First, run the diagnostic script to identify the exact issues:

```bash
python debug_cron_issues.py
```

This will check:
- ✅ Environment variables
- ✅ Dependencies installation
- ✅ File structure
- ✅ Database connection
- ✅ Module imports
- ✅ System initialization

### **✅ Solution 2: Use the Improved Cron Script**

I've created an improved version with better error handling:

```bash
# Test the improved script manually
python run_daily_cron_improved.py
```

### **✅ Solution 3: Updated Railway Configuration**

The `railway.toml` now uses the improved script:

```toml
# Primary cron job
[[cron]]
schedule = "5 22 * * *"
command = "python run_daily_cron_improved.py"

# Backup cron job  
[[cron]]
schedule = "5 23 * * *"
command = "python run_daily_cron_improved.py --backup"
```

---

## 🔍 **Common Issues and Solutions**

### **Issue 1: Missing Environment Variables**

**Symptoms:**
- Database connection errors
- API key errors
- "Not Set" in debug output

**Solution:**
1. Go to **Railway Dashboard** → Your Project → **Variables**
2. Add these **CRITICAL** variables:

```bash
# Database (REQUIRED)
DB_HOST=your_database_host
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=5432

# API Keys (REQUIRED for data fetching)
FMP_API_KEY=your_fmp_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key

# Optional (Auto-configured)
PYTHONPATH=/app:/app/daily_run
PYTHONUNBUFFERED=1
TZ=America/New_York
```

### **Issue 2: Missing Dependencies**

**Symptoms:**
- ImportError messages
- "Module not found" errors

**Solution:**
1. Check `requirements.txt` is in project root
2. Verify Railway build logs show successful pip install
3. Add missing packages to `requirements.txt`:

```txt
psycopg2-binary
pandas
numpy
yfinance
requests
python-dotenv
ratelimit
fastapi
uvicorn[standard]
pytz
pandas-market-calendars
pydantic
psutil
```

### **Issue 3: File Structure Issues**

**Symptoms:**
- "File not found" errors
- Import path issues

**Solution:**
1. Ensure these files exist in your project:

```
ourstox6/
├── railway.toml                    # Railway configuration
├── requirements.txt                # Dependencies
├── run_daily_cron_improved.py     # Improved cron script
├── debug_cron_issues.py           # Debug script
├── daily_run/
│   ├── __init__.py
│   ├── daily_trading_system.py
│   ├── common_imports.py
│   ├── database.py
│   ├── error_handler.py
│   ├── monitoring.py
│   ├── batch_price_processor.py
│   ├── earnings_based_fundamental_processor.py
│   ├── enhanced_multi_service_manager.py
│   ├── check_market_schedule.py
│   ├── data_validator.py
│   └── circuit_breaker.py
```

### **Issue 4: Database Connection Problems**

**Symptoms:**
- "Connection refused" errors
- "Authentication failed" errors

**Solution:**
1. Verify database environment variables are correct
2. Check if database is accessible from Railway
3. Test connection manually:

```python
import psycopg2
conn = psycopg2.connect(
    host=os.getenv('DB_HOST'),
    port=os.getenv('DB_PORT'),
    dbname=os.getenv('DB_NAME'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD')
)
```

### **Issue 5: Python Path Issues**

**Symptoms:**
- "Module not found" errors
- Import failures

**Solution:**
1. The improved script automatically sets up Python paths
2. Verify `PYTHONPATH` environment variable is set
3. Check that `daily_run` directory is in the correct location

---

## 🧪 **Testing Steps**

### **Step 1: Run Debug Script**
```bash
python debug_cron_issues.py
```

### **Step 2: Test Manual Execution**
```bash
python run_daily_cron_improved.py
```

### **Step 3: Check Railway Logs**
1. Go to **Railway Dashboard** → Your Project → **Deployments**
2. Click on latest deployment
3. Check **Logs** tab for error messages

### **Step 4: Verify Environment Variables**
1. Go to **Railway Dashboard** → Your Project → **Variables**
2. Ensure all required variables are set
3. Check for typos in variable names

---

## 📊 **Expected Log Output**

**✅ Successful execution should show:**
```
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - 🚀 RAILWAY PRIMARY CRON JOB STARTED
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - 🔍 STEP 1: CHECKING PREREQUISITES
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - ✅ All prerequisites met
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - 🔍 STEP 2: SETTING UP PYTHON PATH
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - ✅ Added current directory to path
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - 🔍 STEP 3: TESTING DATABASE CONNECTION
2025-01-26 22:05:01 - Railway PRIMARY CRON - INFO - ✅ Database connected
2025-01-26 22:05:01 - Railway PRIMARY CRON - INFO - 🔍 STEP 4: TESTING IMPORTS
2025-01-26 22:05:01 - Railway PRIMARY CRON - INFO - ✅ All imports successful
2025-01-26 22:05:01 - Railway PRIMARY CRON - INFO - 🔍 STEP 5: INITIALIZING TRADING SYSTEM
2025-01-26 22:05:02 - Railway PRIMARY CRON - INFO - ✅ DailyTradingSystem initialized successfully
2025-01-26 22:05:02 - Railway PRIMARY CRON - INFO - 🔍 STEP 6: RUNNING TRADING PROCESS
2025-01-26 22:05:02 - Railway PRIMARY CRON - INFO - 🚀 Starting daily trading process...
[... processing logs ...]
2025-01-26 22:10:00 - Railway PRIMARY CRON - INFO - ✅ RAILWAY PRIMARY CRON JOB COMPLETED SUCCESSFULLY
```

---

## 🚨 **Error Patterns and Solutions**

### **Pattern 1: Import Errors**
```
❌ daily_run.daily_trading_system: Import failed - No module named 'daily_run'
```
**Solution:** Check file structure and Python path setup

### **Pattern 2: Database Errors**
```
❌ Database connection failed: connection to server at "localhost" failed
```
**Solution:** Verify database environment variables and connectivity

### **Pattern 3: Missing Dependencies**
```
❌ psycopg2: No module named 'psycopg2'
```
**Solution:** Check requirements.txt and Railway build process

### **Pattern 4: Environment Variable Errors**
```
❌ DB_HOST: NOT SET
```
**Solution:** Set environment variables in Railway dashboard

---

## 🔄 **Deployment Steps**

### **Step 1: Commit and Push Changes**
```bash
git add railway.toml run_daily_cron_improved.py debug_cron_issues.py CRON_TROUBLESHOOTING_GUIDE.md
git commit -m "fix: Add improved cron script and debugging tools"
git push origin main
```

### **Step 2: Set Environment Variables**
1. Go to **Railway Dashboard** → Your Project → **Variables**
2. Add all required environment variables
3. Redeploy the project

### **Step 3: Monitor Execution**
1. Wait for next scheduled time (10:05 PM UTC)
2. Check Railway logs for execution
3. Look for the improved logging output

---

## 📞 **If Problems Persist**

### **Option 1: Manual Testing**
Run the debug script locally to identify issues:
```bash
python debug_cron_issues.py
```

### **Option 2: Check Railway Documentation**
- Railway Cron Jobs: https://docs.railway.app/guides/cron-jobs
- Railway Environment Variables: https://docs.railway.app/develop/variables

### **Option 3: Alternative Solutions**
- Use external cron service (cron-job.org)
- Implement self-hosted timer
- Use Railway scheduled functions (if available)

---

## 📋 **Checklist**

Before running the cron job, ensure:

- [ ] All environment variables are set in Railway
- [ ] `requirements.txt` contains all dependencies
- [ ] All required files exist in correct locations
- [ ] Database is accessible from Railway
- [ ] Debug script runs successfully
- [ ] Improved cron script runs manually
- [ ] Railway cron jobs are enabled
- [ ] Latest deployment succeeded

---

**The improved configuration should resolve the cron job crashes. The enhanced logging will help identify any remaining issues.** 