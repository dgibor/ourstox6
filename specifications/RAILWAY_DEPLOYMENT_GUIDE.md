# Railway Deployment Guide for Daily Trading System

## 🚨 **Current Issue: Cron Job Not Running**

Your Railway cron job isn't running because of several potential configuration issues. This guide provides multiple solutions.

---

## 🔧 **Solutions Implemented**

### **✅ Solution 1: Fixed railway.toml Configuration**

Updated `railway.toml` with proper environment setup:

```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
runtime = "V2"
numReplicas = 1
startCommand = "uvicorn dashboard_api:app --host 0.0.0.0 --port $PORT"
sleepApplication = false
restartPolicyType = "NEVER"

# Environment variables for the cron job
[deploy.env]
PYTHONPATH = "/app:/app/daily_run"
PYTHONUNBUFFERED = "1"
TZ = "America/New_York"

# Primary cron job - 10:05 PM UTC (5:05 PM ET after market close)
[[cron]]
schedule = "5 22 * * *"
command = "python run_daily_cron.py"

# Backup cron job - 11:05 PM UTC (6:05 PM ET) in case primary fails
[[cron]]
schedule = "5 23 * * *"
command = "python run_daily_cron.py --backup"
```

### **✅ Solution 2: Created Railway-Specific Entry Script**

Created `run_daily_cron.py` that handles:
- ✅ Python path setup for Railway environment
- ✅ Comprehensive error logging
- ✅ Alternative import methods
- ✅ Environment variable checking
- ✅ Backup job support

---

## 🚀 **Deployment Steps**

### **Step 1: Deploy the Updated Configuration**

1. **Commit and push** the updated files:
   ```bash
   git add railway.toml run_daily_cron.py RAILWAY_DEPLOYMENT_GUIDE.md
   git commit -m "fix: Update Railway cron configuration with dedicated entry script"
   git push origin main
   ```

2. **Railway will automatically redeploy** with the new configuration

### **Step 2: Set Required Environment Variables**

In your **Railway Dashboard → Environment Variables**, ensure these are set:

#### **🔴 CRITICAL (Required for cron to work):**
```bash
DB_HOST=your_database_host
DB_NAME=your_database_name  
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=5432
```

#### **🟡 IMPORTANT (Required for data fetching):**
```bash
FMP_API_KEY=your_fmp_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key
```

#### **🟢 OPTIONAL (Auto-configured):**
```bash
PYTHONPATH=/app:/app/daily_run
PYTHONUNBUFFERED=1
TZ=America/New_York
```

### **Step 3: Monitor Cron Job Execution**

1. **Check Railway Logs** at scheduled time (10:05 PM UTC / 5:05 PM ET)
2. **Look for log entries** starting with "Railway PRIMARY CRON" or "Railway BACKUP CRON"
3. **Monitor for successful completion** message

---

## 🔍 **Troubleshooting**

### **Problem: Cron Job Still Not Running**

#### **Check 1: Verify Cron Schedule**
- ✅ **Current**: `5 22 * * *` = 10:05 PM UTC daily
- ✅ **Backup**: `5 23 * * *` = 11:05 PM UTC daily
- 🕐 **Market Close**: 4:00 PM ET = 9:00 PM UTC (standard) / 8:00 PM UTC (DST)

#### **Check 2: Railway Cron Enabled**
Railway cron jobs need to be **explicitly enabled**:
1. Go to **Railway Dashboard** → Your Project
2. Check **"Cron Jobs"** section
3. Ensure cron jobs are **"Enabled"**

#### **Check 3: Deployment Status**
1. Verify **latest deployment succeeded**
2. Check **build logs** for any errors
3. Ensure **railway.toml** is in project root

### **Problem: Cron Runs But Fails**

#### **Check Railway Logs** for these error patterns:

**🔍 Import Errors:**
```bash
# Look for: "Failed to import DailyTradingSystem"
# Solution: Verify PYTHONPATH environment variable
```

**🔍 Database Connection Errors:**
```bash
# Look for: "Database connection failed"
# Solution: Verify database environment variables
```

**🔍 API Key Errors:**
```bash
# Look for: "API key not configured"
# Solution: Set required API keys in Railway environment
```

### **Problem: Environment Variables Not Set**

**Railway Environment Variables Setup:**
1. **Railway Dashboard** → Project → **"Variables"** tab
2. **Add each variable** with correct values
3. **Redeploy** after adding variables

---

## 🧪 **Testing the Configuration**

### **Manual Test Command**

Test the cron script manually in Railway console:

```bash
# In Railway console (if available)
python run_daily_cron.py

# Check if it can import the system
python -c "from daily_run.daily_trading_system import DailyTradingSystem; print('✅ Import successful')"
```

### **Expected Log Output**

**✅ Successful execution should show:**
```bash
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - 🚀 RAILWAY PRIMARY CRON JOB STARTED
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - ⏰ Execution Time: 2025-01-26 22:05:00
2025-01-26 22:05:00 - Railway PRIMARY CRON - INFO - 📊 Importing Daily Trading System...
2025-01-26 22:05:01 - Railway PRIMARY CRON - INFO - ✅ Successfully imported DailyTradingSystem
2025-01-26 22:05:01 - Railway PRIMARY CRON - INFO - 🏗️ Initializing Daily Trading System...
2025-01-26 22:05:02 - Railway PRIMARY CRON - INFO - 🚀 Starting daily trading process...
[... processing logs ...]
2025-01-26 22:10:00 - Railway PRIMARY CRON - INFO - ✅ RAILWAY PRIMARY CRON JOB COMPLETED SUCCESSFULLY
```

---

## 🔄 **Alternative Solutions**

### **If Railway Cron Still Doesn't Work**

#### **Option 1: Use External Cron Service**
- **Cron-job.org**: Free external cron service
- **Setup**: Make HTTP endpoint in your app that triggers the trading system
- **Call**: External service hits your endpoint at scheduled time

#### **Option 2: Use Railway Scheduled Functions**
- Check if Railway has **"Scheduled Functions"** feature
- Alternative to traditional cron jobs

#### **Option 3: Self-Hosted Timer**
- **Long-running process** that sleeps until market close time
- **Built-in scheduler** instead of external cron

---

## 📊 **Monitoring Setup**

### **Success Indicators**
- ✅ Cron job logs appear in Railway dashboard
- ✅ Database gets updated with new daily_charts entries  
- ✅ Technical indicators calculated
- ✅ No error messages in logs

### **Failure Indicators**
- ❌ No cron job logs at scheduled time
- ❌ Database not updated after market close
- ❌ Error messages in Railway logs
- ❌ "Import failed" or "Connection failed" errors

---

## 📞 **Support**

### **If Problems Persist**

1. **Check Railway Documentation**: https://docs.railway.app/guides/cron-jobs
2. **Railway Discord**: Railway community support
3. **Alternative**: Consider switching to **Vercel Cron** or **AWS EventBridge**

### **Immediate Next Steps**

1. ✅ **Deploy the updated configuration** (commit & push)
2. ✅ **Set environment variables** in Railway dashboard  
3. ✅ **Wait for next scheduled time** (10:05 PM UTC)
4. ✅ **Check Railway logs** for execution

---

**The configuration should now work with Railway's cron system. The primary job runs at 10:05 PM UTC (5:05 PM ET) with a backup at 11:05 PM UTC (6:05 PM ET) in case the primary fails.** 