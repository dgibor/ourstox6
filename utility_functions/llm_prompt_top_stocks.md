
# LLM Prompt: Generate Structured CSV of Top U.S.-Listed Stocks by Industry

You are a financial analyst assistant. Your task is to create a structured CSV file with up to **1,500 U.S.-listed stocks** that are **popular with retail investors** over the **past 2 years**. These stocks should span **all GICS industries**, with more entries from popular industries (e.g., Software, Semiconductors) and fewer from narrow ones (e.g., Oil Equipment).

## 🎯 Selection Criteria

Only include stocks that meet **at least one** of the following:
- High **retail popularity** on platforms like Reddit, Twitter, or Robinhood
- Strong **growth potential**, stability, or consistent dividends
- High **trading volume** and **liquidity**
- Inclusion in major **ETFs** or high retail ownership

Focus on **U.S. exchanges only** (NASDAQ, NYSE, AMEX), but the company can be international.

---

## 📦 Output Format

Generate a `.csv` file with these **columns** (in order):

| Column Name         | Description                                                                 |
|---------------------|-----------------------------------------------------------------------------|
| `ticker`            | Stock symbol (uppercase)                                                    |
| `company_name`      | Full name of the company                                                    |
| `sector`            | GICS sector (e.g., Health Care, Energy)                                     |
| `industry`          | GICS industry (e.g., Biotechnology, Semiconductors)                         |
| `general_description` | What the company does (concise: ≤12 words)                               |
| `customers`         | Who the company sells to (e.g., Consumers, Enterprises, Hospitals)          |
| `products_services` | Key products or services (3–4 examples, comma-separated)                    |
| `hq_location`       | Headquarters city and state                                                 |
| `exchange`          | Where it's listed (NASDAQ, NYSE, AMEX)                                      |
| `country`           | Usually "USA" unless otherwise stated                                       |
| `logo_url`          | URL to transparent PNG logo (official preferred, fallback to public/logo DB)|

---

## 📌 Constraints

- Total stocks: ≤1500
- All text must be **UTF-8 encoded**, with **only standard ASCII characters** (replace smart quotes, dashes, etc.)
- Avoid duplicates
- Make sure each row is complete (no missing values)

---

## 📝 Example Row

```
AAPL,Apple Inc.,Information Technology,Consumer Electronics,Designs and sells consumer electronics,Global consumers and businesses,iPhone, Mac, iPad, App Store,Cupertino, California,NASDAQ,USA,https://logo.clearbit.com/apple.com
```

---

Once complete, return the full CSV. Ensure formatting consistency, accurate industry classification, and clean text output.
