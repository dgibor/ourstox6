# Cron-Only Railway Setup

## 🎯 **Configuration Overview**

This setup runs **only the daily trading system** on a schedule without a web dashboard.

---

## 📋 **Railway Configuration**

### **railway.toml**
```toml
[build]
builder = "NIXPACKS"
buildCommand = "pip install -r requirements.txt"

[deploy]
runtime = "V2"
numReplicas = 1
startCommand = "python run_cron_only.py"
sleepApplication = true
restartPolicyType = "NEVER"

# Environment variables
[deploy.env]
PYTHONPATH = "/app:/app/daily_run"
PYTHONUNBUFFERED = "1"
TZ = "America/New_York"

# Cron jobs
[[cron]]
schedule = "5 22 * * *"
command = "python run_cron_only.py"

[[cron]]
schedule = "5 23 * * *"
command = "python run_cron_only.py"
```

---

## 🔧 **Key Changes**

### **✅ Removed Web Dashboard**
- ❌ No `uvicorn dashboard_api:app` start command
- ❌ No web interface
- ❌ No HTTP endpoints

### **✅ Cron-Only Operation**
- ✅ `sleepApplication = true` - Sleep after execution
- ✅ Simple `run_cron_only.py` script
- ✅ Runs once and exits
- ✅ Scheduled via Railway cron jobs

---

## 🚀 **How It Works**

### **Startup Behavior**
1. **Railway starts** the service
2. **Runs `run_cron_only.py`** once
3. **Executes daily trading process**
4. **Exits successfully**
5. **Service sleeps** until next cron trigger

### **Scheduled Execution**
1. **10:05 PM UTC daily**: Primary cron job runs
2. **11:05 PM UTC daily**: Backup cron job runs (if primary failed)
3. **Each run**: Updates database with latest data
4. **Logs**: Detailed execution logs in Railway dashboard

---

## 📊 **Expected Log Output**

**✅ Successful execution:**
```
2025-01-26 22:05:00 - CRON ONLY - INFO - 🚀 CRON-ONLY DAILY TRADING SYSTEM STARTED
2025-01-26 22:05:00 - CRON ONLY - INFO - ⏰ Execution Time: 2025-01-26 22:05:00
2025-01-26 22:05:00 - CRON ONLY - INFO - 📁 Working Directory: /app
2025-01-26 22:05:01 - CRON ONLY - INFO - ✅ DailyTradingSystem imported successfully
2025-01-26 22:05:01 - CRON ONLY - INFO - ✅ DailyTradingSystem initialized successfully
2025-01-26 22:05:01 - CRON ONLY - INFO - 🚀 Starting daily trading process...
[... processing logs ...]
2025-01-26 22:10:00 - CRON ONLY - INFO - 📈 DAILY TRADING PROCESS COMPLETED SUCCESSFULLY
2025-01-26 22:10:00 - CRON ONLY - INFO - ✅ CRON-ONLY JOB COMPLETED SUCCESSFULLY
```

---

## 🔧 **Required Environment Variables**

Set these in **Railway Dashboard → Variables**:

```bash
# Database (REQUIRED)
DB_HOST=your_database_host
DB_NAME=your_database_name
DB_USER=your_database_user
DB_PASSWORD=your_database_password
DB_PORT=5432

# API Keys (REQUIRED)
FMP_API_KEY=your_fmp_api_key
ALPHA_VANTAGE_API_KEY=your_alpha_vantage_key
FINNHUB_API_KEY=your_finnhub_key

# Optional (Auto-configured)
PYTHONPATH=/app:/app/daily_run
PYTHONUNBUFFERED=1
TZ=America/New_York
```

---

## 🚀 **Deployment Steps**

### **Step 1: Commit and Push**
```bash
git add railway.toml run_cron_only.py CRON_ONLY_SETUP.md
git commit -m "feat: Switch to cron-only Railway setup"
git push origin main
```

### **Step 2: Set Environment Variables**
1. Go to **Railway Dashboard** → Your Project → **Variables**
2. Add all required environment variables
3. Railway will auto-redeploy

### **Step 3: Monitor Execution**
1. Wait for next scheduled time (10:05 PM UTC)
2. Check Railway logs for execution
3. Verify database is updated

---

## ✅ **Benefits of Cron-Only Setup**

1. **Simpler**: No web server complexity
2. **Cost-effective**: Only runs when needed
3. **Focused**: Single purpose - data processing
4. **Reliable**: Less moving parts
5. **Efficient**: Sleeps when not in use

---

## 📞 **Monitoring**

### **Check Execution Status**
1. **Railway Dashboard** → Your Project → **Deployments**
2. **Click latest deployment** → **Logs** tab
3. **Look for cron execution logs**

### **Verify Data Updates**
- Check database tables for new data
- Monitor `update_log` table for successful runs
- Verify `daily_charts` table has latest prices

---

## 🔄 **Manual Execution**

If you need to run manually:

```bash
# In Railway console (if available)
python run_cron_only.py

# Or trigger via Railway dashboard
# Go to Deployments → Latest → Redeploy
```

---

## 📋 **Summary**

This cron-only setup:
- ✅ Runs daily trading system automatically
- ✅ Updates database with latest data
- ✅ No web interface (data processing only)
- ✅ Cost-effective and simple
- ✅ Reliable scheduled execution

**Perfect for automated data processing without web dashboard needs.** 