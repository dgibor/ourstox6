# Batch CSV Import Scripts

This directory contains scripts for importing and managing stock data from batch CSV files into the stocks table.

## Overview

The batch import workflow processes four CSV files (`batch1.csv` to `batch4.csv`) containing comprehensive stock information and imports them into the database while maintaining data integrity and quality.

## Scripts

### 1. `update_stocks_schema.py`
**Purpose**: Updates the stocks table schema to accommodate all columns from batch CSV files.

**What it does**:
- Adds missing columns: `market_cap_b`, `description`, `business_model`, `products_services`, `main_customers`, `markets`, `moat`, `peer_a`, `peer_b`, `peer_c`
- Ensures unique constraint on ticker column
- Preserves existing data and columns

**Usage**:
```bash
python update_stocks_schema.py
```

### 2. `upload_batch_csvs.py`
**Purpose**: Uploads all four batch CSV files to the stocks table.

**What it does**:
- Processes `batch1.csv`, `batch2.csv`, `batch3.csv`, `batch4.csv`
- Inserts new records or updates existing ones based on ticker
- Handles data cleaning and validation
- Provides detailed upload statistics

**Usage**:
```bash
python upload_batch_csvs.py
```

### 3. `remove_duplicates.py`
**Purpose**: Removes duplicate records from the stocks table.

**What it does**:
- Identifies duplicate tickers
- Keeps the most complete record (based on data completeness score)
- Keeps the most recent record if completeness is equal
- Provides detailed removal statistics

**Usage**:
```bash
python remove_duplicates.py
```

### 4. `check_stocks_table.py`
**Purpose**: Verifies the stocks table has all information from batch files and provides data quality report.

**What it does**:
- Analyzes data completeness for all columns
- Shows sector and industry distribution
- Displays market cap distribution
- Identifies records with complete vs. incomplete batch data
- Provides sample records for verification

**Usage**:
```bash
python check_stocks_table.py
```

### 5. `find_missing_tickers.py`
**Purpose**: Finds tickers present in the stocks table but not covered by batch files.

**What it does**:
- Compares database tickers with batch file tickers
- Generates CSV file with missing ticker details
- Provides completeness analysis for missing tickers
- Shows sector and market cap distribution of missing tickers

**Usage**:
```bash
python find_missing_tickers.py
```

### 6. `run_batch_import_workflow.py`
**Purpose**: Main workflow script that runs all tasks in sequence.

**What it does**:
- Executes all scripts in the correct order
- Provides comprehensive error handling
- Generates summary report
- Tracks workflow progress and results

**Usage**:
```bash
python run_batch_import_workflow.py
```

## Batch CSV File Structure

All batch CSV files have the same structure with these columns:

| Column | Description | Data Type |
|--------|-------------|-----------|
| Ticker | Stock ticker symbol | VARCHAR(10) |
| Company Name | Full company name | TEXT |
| Industry | Industry classification | VARCHAR(100) |
| Sector | Sector classification | VARCHAR(50) |
| Market Cap (B) | Market capitalization in billions | NUMERIC(10,2) |
| Description | Company description | TEXT |
| Business_Model | Business model type | VARCHAR(100) |
| Products_Services | Products and services offered | TEXT |
| Main_Customers | Primary customer segments | TEXT |
| Markets | Geographic markets served | TEXT |
| Moat | Competitive advantages | TEXT |
| Peer A | Primary peer company | VARCHAR(10) |
| Peer B | Secondary peer company | VARCHAR(10) |
| Peer C | Tertiary peer company | VARCHAR(10) |

## Database Schema Changes

The scripts will add these columns to the existing stocks table:

```sql
ALTER TABLE stocks ADD COLUMN market_cap_b numeric(10,2);
ALTER TABLE stocks ADD COLUMN description text;
ALTER TABLE stocks ADD COLUMN business_model character varying(100);
ALTER TABLE stocks ADD COLUMN products_services text;
ALTER TABLE stocks ADD COLUMN main_customers text;
ALTER TABLE stocks ADD COLUMN markets text;
ALTER TABLE stocks ADD COLUMN moat text;
ALTER TABLE stocks ADD COLUMN peer_a character varying(10);
ALTER TABLE stocks ADD COLUMN peer_b character varying(10);
ALTER TABLE stocks ADD COLUMN peer_c character varying(10);
```

## Workflow Steps

1. **Schema Update**: Add missing columns to stocks table
2. **Data Upload**: Import all batch CSV files
3. **Duplicate Removal**: Clean up any duplicate records
4. **Data Verification**: Verify data quality and completeness
5. **Missing Analysis**: Identify tickers not covered by batch files

## Output Files

- `missing_tickers_from_batch_files.csv`: List of tickers in database but not in batch files

## Error Handling

- All scripts include comprehensive error handling
- Database transactions are used to ensure data integrity
- Detailed error messages and logging
- Graceful handling of missing files or data issues

## Prerequisites

- Python 3.7+
- Required packages: `psycopg2`, `pandas`, `python-dotenv`
- Database connection configured in `.env` file
- Batch CSV files in `pre_filled_stocks/` directory

## Environment Variables

Ensure these are set in your `.env` file:

```
DB_HOST=your_host
DB_PORT=your_port
DB_NAME=your_database
DB_USER=your_username
DB_PASSWORD=your_password
```

## Running the Complete Workflow

To run all tasks in sequence:

```bash
python run_batch_import_workflow.py
```

This will:
1. Update the database schema
2. Upload all batch files
3. Remove duplicates
4. Verify data quality
5. Generate missing tickers report
6. Provide a comprehensive summary

## Troubleshooting

### Common Issues

1. **Database Connection Errors**
   - Verify `.env` file configuration
   - Check database server status
   - Ensure correct credentials

2. **Missing CSV Files**
   - Verify batch files exist in `pre_filled_stocks/` directory
   - Check file permissions

3. **Schema Update Errors**
   - Ensure database user has ALTER TABLE permissions
   - Check for existing columns that might conflict

4. **Duplicate Removal Issues**
   - Review the duplicate detection logic
   - Check for case sensitivity issues with tickers

### Debug Mode

Add debug logging by modifying the scripts to include more verbose output:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Data Quality Metrics

The scripts provide several data quality metrics:

- **Completeness Score**: 0-6 based on filled batch data fields
- **Sector Distribution**: Breakdown by industry sectors
- **Market Cap Distribution**: Categorization by company size
- **Duplicate Detection**: Identification of duplicate records
- **Missing Data Analysis**: Fields with incomplete information

## Performance Considerations

- Large datasets are processed in batches
- Database indexes are used for efficient queries
- Memory usage is optimized for large CSV files
- Transaction management ensures data consistency

## Support

For issues or questions:
1. Check the console output for error messages
2. Review the generated CSV files for data issues
3. Verify database connectivity and permissions
4. Check file paths and permissions for CSV files 