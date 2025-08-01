# Database Schema vs Calculations Analysis

## 📊 **Database Schema Analysis**

### **Financial Ratios Table Schema (`financial_ratios`)**

Based on the database schema in `specifications/fundamental_schema.sql`, the `financial_ratios` table has the following columns:

#### **✅ Valuation Ratios (5 columns):**
1. `pe_ratio` NUMERIC(8,4)
2. `pb_ratio` NUMERIC(8,4)
3. `ps_ratio` NUMERIC(8,4)
4. `ev_ebitda` NUMERIC(8,4) - **❌ MISSING**
5. `peg_ratio` NUMERIC(8,4) - **❌ MISSING**

#### **✅ Profitability Ratios (6 columns):**
6. `roe` NUMERIC(8,4) - Return on Equity
7. `roa` NUMERIC(8,4) - Return on Assets
8. `roic` NUMERIC(8,4) - Return on Invested Capital - **❌ MISSING**
9. `gross_margin` NUMERIC(8,4)
10. `operating_margin` NUMERIC(8,4)
11. `net_margin` NUMERIC(8,4)

#### **✅ Financial Health (5 columns):**
12. `debt_to_equity` NUMERIC(8,4)
13. `current_ratio` NUMERIC(8,4)
14. `quick_ratio` NUMERIC(8,4)
15. `interest_coverage` NUMERIC(8,4) - **❌ MISSING**
16. `altman_z_score` NUMERIC(8,4) - **❌ MISSING**

#### **❌ Efficiency Ratios (3 columns):**
17. `asset_turnover` NUMERIC(8,4) - **❌ MISSING**
18. `inventory_turnover` NUMERIC(8,4) - **❌ MISSING**
19. `receivables_turnover` NUMERIC(8,4) - **❌ MISSING**

#### **❌ Growth Metrics (3 columns):**
20. `revenue_growth_yoy` NUMERIC(8,4) - **❌ MISSING**
21. `earnings_growth_yoy` NUMERIC(8,4) - **❌ MISSING**
22. `fcf_growth_yoy` NUMERIC(8,4) - **❌ MISSING**

#### **❌ Quality Metrics (2 columns):**
23. `fcf_to_net_income` NUMERIC(8,4) - **❌ MISSING**
24. `cash_conversion_cycle` INTEGER - **❌ MISSING**

#### **❌ Market Data (2 columns):**
25. `market_cap` NUMERIC(15,2) - **❌ MISSING**
26. `enterprise_value` NUMERIC(15,2) - **❌ MISSING**

#### **❌ Intrinsic Value (1 column):**
27. `graham_number` NUMERIC(8,4) - **❌ MISSING**

---

## 🔍 **Current Calculations Analysis**

### **✅ What We're Currently Calculating (11 ratios):**

From `final_ratio_calculator_v3.py`, we calculate:

1. **Valuation Ratios (3/5):**
   - ✅ `pe_ratio` - P/E Ratio
   - ✅ `pb_ratio` - P/B Ratio
   - ✅ `ps_ratio` - P/S Ratio
   - ❌ `ev_ebitda` - EV/EBITDA Ratio
   - ❌ `peg_ratio` - PEG Ratio

2. **Profitability Ratios (5/6):**
   - ✅ `roe` - Return on Equity
   - ✅ `roa` - Return on Assets
   - ❌ `roic` - Return on Invested Capital
   - ✅ `gross_margin` - Gross Margin
   - ✅ `operating_margin` - Operating Margin
   - ✅ `net_margin` - Net Margin

3. **Financial Health (3/5):**
   - ✅ `debt_to_equity` - Debt-to-Equity Ratio
   - ✅ `current_ratio` - Current Ratio
   - ✅ `quick_ratio` - Quick Ratio
   - ❌ `interest_coverage` - Interest Coverage Ratio
   - ❌ `altman_z_score` - Altman Z-Score

4. **Missing Categories (0/9):**
   - ❌ Efficiency Ratios (0/3)
   - ❌ Growth Metrics (0/3)
   - ❌ Quality Metrics (0/2)
   - ❌ Market Data (0/2)
   - ❌ Intrinsic Value (0/1)

---

## ❌ **Missing Calculations (16 ratios)**

### **🔧 Valuation Ratios (2 missing):**
1. **`ev_ebitda`** - Enterprise Value to EBITDA
   - Formula: `(Market Cap + Total Debt - Cash) / EBITDA`
   - Requires: Market cap, total debt, cash, EBITDA

2. **`peg_ratio`** - Price/Earnings to Growth
   - Formula: `P/E Ratio / Earnings Growth Rate`
   - Requires: P/E ratio, earnings growth rate

### **🔧 Profitability Ratios (1 missing):**
3. **`roic`** - Return on Invested Capital
   - Formula: `Net Income / (Total Equity + Total Debt)`
   - Requires: Net income, total equity, total debt

### **🔧 Financial Health (2 missing):**
4. **`interest_coverage`** - Interest Coverage Ratio
   - Formula: `Operating Income / Interest Expense`
   - Requires: Operating income, interest expense

5. **`altman_z_score`** - Altman Z-Score
   - Formula: Complex bankruptcy prediction model
   - Requires: Multiple balance sheet and income statement items

### **🔧 Efficiency Ratios (3 missing):**
6. **`asset_turnover`** - Asset Turnover
   - Formula: `Revenue / Average Total Assets`
   - Requires: Revenue, total assets (current and previous)

7. **`inventory_turnover`** - Inventory Turnover
   - Formula: `Cost of Goods Sold / Average Inventory`
   - Requires: COGS, inventory (current and previous)

8. **`receivables_turnover`** - Receivables Turnover
   - Formula: `Revenue / Average Accounts Receivable`
   - Requires: Revenue, accounts receivable (current and previous)

### **🔧 Growth Metrics (3 missing):**
9. **`revenue_growth_yoy`** - Revenue Growth Year-over-Year
   - Formula: `(Current Revenue - Previous Revenue) / Previous Revenue * 100`
   - Requires: Current and previous year revenue

10. **`earnings_growth_yoy`** - Earnings Growth Year-over-Year
    - Formula: `(Current Net Income - Previous Net Income) / Previous Net Income * 100`
    - Requires: Current and previous year net income

11. **`fcf_growth_yoy`** - Free Cash Flow Growth Year-over-Year
    - Formula: `(Current FCF - Previous FCF) / Previous FCF * 100`
    - Requires: Current and previous year free cash flow

### **🔧 Quality Metrics (2 missing):**
12. **`fcf_to_net_income`** - Free Cash Flow to Net Income
    - Formula: `Free Cash Flow / Net Income`
    - Requires: Free cash flow, net income

13. **`cash_conversion_cycle`** - Cash Conversion Cycle
    - Formula: `Days Inventory Outstanding + Days Sales Outstanding - Days Payables Outstanding`
    - Requires: Inventory, receivables, payables, COGS, revenue

### **🔧 Market Data (2 missing):**
14. **`market_cap`** - Market Capitalization
    - Formula: `Current Price * Shares Outstanding`
    - Requires: Current price, shares outstanding

15. **`enterprise_value`** - Enterprise Value
    - Formula: `Market Cap + Total Debt - Cash`
    - Requires: Market cap, total debt, cash

### **🔧 Intrinsic Value (1 missing):**
16. **`graham_number`** - Graham Number
    - Formula: `√(22.5 × EPS × Book Value Per Share)`
    - Requires: EPS, book value per share

---

## 📊 **Summary Statistics**

### **Coverage Analysis:**
- **Total Database Columns:** 27 ratios
- **Currently Calculating:** 11 ratios
- **Missing Calculations:** 16 ratios
- **Coverage Percentage:** 40.7% (11/27)

### **Category Coverage:**
- **Valuation Ratios:** 60% (3/5) ✅
- **Profitability Ratios:** 83% (5/6) ✅
- **Financial Health:** 60% (3/5) ✅
- **Efficiency Ratios:** 0% (0/3) ❌
- **Growth Metrics:** 0% (0/3) ❌
- **Quality Metrics:** 0% (0/2) ❌
- **Market Data:** 0% (0/2) ❌
- **Intrinsic Value:** 0% (0/1) ❌

---

## 🎯 **Recommendations**

### **✅ High Priority (Essential for Stock Screening):**
1. **`ev_ebitda`** - Critical valuation metric
2. **`market_cap`** - Essential for filtering
3. **`enterprise_value`** - Important for valuation
4. **`roic`** - Key profitability metric
5. **`interest_coverage`** - Important financial health metric

### **✅ Medium Priority (Important for Analysis):**
6. **`peg_ratio`** - Growth-adjusted valuation
7. **`asset_turnover`** - Efficiency metric
8. **`revenue_growth_yoy`** - Growth metric
9. **`earnings_growth_yoy`** - Growth metric
10. **`fcf_to_net_income`** - Quality metric

### **✅ Lower Priority (Advanced Analysis):**
11. **`altman_z_score`** - Bankruptcy risk
12. **`inventory_turnover`** - Efficiency metric
13. **`receivables_turnover`** - Efficiency metric
14. **`fcf_growth_yoy`** - Growth metric
15. **`cash_conversion_cycle`** - Quality metric
16. **`graham_number`** - Intrinsic value

---

## 🚀 **Next Steps**

### **Immediate Actions:**
1. **Extend the calculator** to include the 16 missing ratios
2. **Add required data fields** to fundamental data structure
3. **Test accuracy** for new ratios against API data
4. **Update database** with complete ratio calculations

### **Implementation Plan:**
1. **Phase 1:** Add high-priority ratios (5 ratios)
2. **Phase 2:** Add medium-priority ratios (5 ratios)
3. **Phase 3:** Add lower-priority ratios (6 ratios)
4. **Phase 4:** Comprehensive testing and validation

**Current Status:** ✅ **40.7% Complete (11/27 ratios calculated)**
**Target:** 🎯 **100% Complete (27/27 ratios calculated)** 