# Database Schema Documentation

## Table: `chart_metadata`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| ticker | character varying | NO |  |
| last_update | character varying | YES |  |
| initial_load_completed | boolean | YES |  |
| alpha_calls_today | integer | YES |  |
| last_api_reset_date | character varying | YES |  |

## Table: `company_analysis`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('company_analysis_id_seq'::regclass) |
| ticker | character varying | NO |  |
| company_name | text | NO |  |
| industry | character varying | YES |  |
| sector | character varying | YES |  |
| description | text | YES |  |
| market_cap | numeric | YES |  |
| pe_ratio | numeric | YES |  |
| ps_ratio | numeric | YES |  |
| ev_ebitda | numeric | YES |  |
| roe | numeric | YES |  |
| revenue_growth | numeric | YES |  |
| gross_margin | numeric | YES |  |
| operating_margin | numeric | YES |  |
| net_margin | numeric | YES |  |
| debt_to_equity | numeric | YES |  |
| current_price | numeric | YES |  |
| fifty_two_week_low | numeric | YES |  |
| fifty_two_week_high | numeric | YES |  |
| target_price_low | numeric | YES |  |
| target_price_mean | numeric | YES |  |
| target_price_high | numeric | YES |  |
| analyst_rating | character varying | YES |  |
| market_position | text | YES |  |
| strengths | text | YES |  |
| weaknesses | text | YES |  |
| opportunities | text | YES |  |
| threats | text | YES |  |
| bull_case_price | numeric | YES |  |
| base_case_price | numeric | YES |  |
| bear_case_price | numeric | YES |  |
| investment_conclusion | text | YES |  |
| next_earnings_date | character varying | YES |  |
| last_updated | timestamp without time zone | YES |  |

## Table: `daily_charts`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('daily_charts_id_seq'::regclass) |
| ticker | character varying | NO |  |
| date | character varying | NO |  |
| open | numeric | YES |  |
| high | numeric | YES |  |
| low | numeric | YES |  |
| close | numeric | YES |  |
| volume | integer | YES |  |
| cci | numeric | YES |  |
| rsi | numeric | YES |  |
| obv | bigint | YES |  |
| vpt | numeric | YES |  |
| indicators_updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |
| rsi_14 | smallint | YES |  |
| cci_20 | smallint | YES |  |
| atr_14 | numeric | YES |  |
| ema_20 | numeric | YES |  |
| ema_50 | numeric | YES |  |
| ema_100 | numeric | YES |  |
| ema_200 | numeric | YES |  |
| macd_line | numeric | YES |  |
| macd_signal | numeric | YES |  |
| macd_histogram | numeric | YES |  |
| bb_upper | numeric | YES |  |
| bb_middle | numeric | YES |  |
| bb_lower | numeric | YES |  |
| vwap | numeric | YES |  |
| stoch_k | smallint | YES |  |
| stoch_d | smallint | YES |  |
| pivot_point | numeric | YES |  |
| resistance_1 | numeric | YES |  |
| resistance_2 | numeric | YES |  |
| resistance_3 | numeric | YES |  |
| support_1 | numeric | YES |  |
| support_2 | numeric | YES |  |
| support_3 | numeric | YES |  |
| swing_high_5d | numeric | YES |  |
| swing_low_5d | numeric | YES |  |
| swing_high_10d | numeric | YES |  |
| swing_low_10d | numeric | YES |  |
| swing_high_20d | numeric | YES |  |
| swing_low_20d | numeric | YES |  |
| week_high | numeric | YES |  |
| week_low | numeric | YES |  |
| month_high | numeric | YES |  |
| month_low | numeric | YES |  |
| nearest_support | numeric | YES |  |
| nearest_resistance | numeric | YES |  |
| support_strength | smallint | YES |  |
| resistance_strength | smallint | YES |  |

## Table: `db_version`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('db_version_id_seq'::regclass) |
| version | integer | NO |  |
| updated_at | character varying | NO |  |

## Table: `economic_indicators`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('economic_indicators_id_seq'::regclass) |
| indicator_code | character varying | NO |  |
| value | double precision | NO |  |
| date | date | NO |  |
| source | character varying | NO |  |

## Table: `macro_analysis`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('macro_analysis_id_seq'::regclass) |
| date | timestamp without time zone | YES |  |
| market_regime | character varying | NO |  |
| composite_score | double precision | NO |  |
| summary | text | NO |  |
| key_insights | json | NO |  |
| investment_implications | json | NO |  |
| raw_data | json | NO |  |

## Table: `macro_scores`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('macro_scores_id_seq'::regclass) |
| date | date | NO |  |
| total_score | double precision | NO |  |
| market_regime | character varying | NO |  |
| economic_growth_score | double precision | NO |  |
| inflation_fed_score | double precision | NO |  |
| yield_credit_score | double precision | NO |  |
| market_internals_score | double precision | NO |  |
| news_sentiment_score | double precision | NO |  |

## Table: `market_data`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('market_data_id_seq'::regclass) |
| date | character varying | NO |  |
| data | json | NO |  |
| summary | text | YES |  |
| timestamp | character varying | NO |  |
| created_at | character varying | NO |  |

## Table: `market_regimes`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('market_regimes_id_seq'::regclass) |
| start_date | date | NO |  |
| end_date | date | YES |  |
| regime_type | character varying | NO |  |
| avg_score | double precision | NO |  |

## Table: `news_sentiment`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('news_sentiment_id_seq'::regclass) |
| date | date | NO |  |
| title | character varying | NO |  |
| description | character varying | YES |  |
| source | character varying | NO |  |
| sentiment_score | double precision | NO |  |
| url | character varying | YES |  |

## Table: `portfolio`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('portfolio_id_seq'::regclass) |
| user_id | integer | NO |  |
| ticker | character varying | NO |  |
| company_name | character varying | YES |  |
| trade_date | character varying | YES |  |
| quantity | numeric | NO |  |
| trade_price | numeric | NO |  |
| date_added | timestamp without time zone | YES |  |
| date_modified | timestamp without time zone | YES |  |

## Table: `roles`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('roles_id_seq'::regclass) |
| name | character varying | YES |  |
| description | character varying | YES |  |

## Table: `roles_users`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| user_id | integer | NO |  |
| role_id | integer | NO |  |

## Table: `sectors`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('sectors_id_seq'::regclass) |
| ticker | character varying | NO |  |
| sector_name | character varying | NO |  |
| sector_category | character varying | NO |  |
| etf_name | character varying | NO |  |
| date | date | NO |  |
| open | numeric | YES |  |
| high | numeric | YES |  |
| low | numeric | YES |  |
| close | numeric | NO |  |
| volume | bigint | YES |  |
| rsi_14 | smallint | YES |  |
| cci_20 | smallint | YES |  |
| stoch_k | smallint | YES |  |
| stoch_d | smallint | YES |  |
| ema_20 | numeric | YES |  |
| ema_50 | numeric | YES |  |
| ema_100 | numeric | YES |  |
| ema_200 | numeric | YES |  |
| macd_line | numeric | YES |  |
| macd_signal | numeric | YES |  |
| macd_histogram | numeric | YES |  |
| bb_upper | numeric | YES |  |
| bb_middle | numeric | YES |  |
| bb_lower | numeric | YES |  |
| vwap | numeric | YES |  |
| obv | bigint | YES |  |
| vpt | numeric | YES |  |
| atr_14 | numeric | YES |  |
| pivot_point | numeric | YES |  |
| resistance_1 | numeric | YES |  |
| resistance_2 | numeric | YES |  |
| resistance_3 | numeric | YES |  |
| support_1 | numeric | YES |  |
| support_2 | numeric | YES |  |
| support_3 | numeric | YES |  |
| swing_high_5d | numeric | YES |  |
| swing_low_5d | numeric | YES |  |
| swing_high_10d | numeric | YES |  |
| swing_low_10d | numeric | YES |  |
| swing_high_20d | numeric | YES |  |
| swing_low_20d | numeric | YES |  |
| week_high | numeric | YES |  |
| week_low | numeric | YES |  |
| month_high | numeric | YES |  |
| month_low | numeric | YES |  |
| nearest_support | numeric | YES |  |
| nearest_resistance | numeric | YES |  |
| support_strength | smallint | YES |  |
| resistance_strength | smallint | YES |  |
| created_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |
| updated_at | timestamp without time zone | YES | CURRENT_TIMESTAMP |

## Table: `stocks`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('stocks_id_seq'::regclass) |
| ticker | character varying | NO |  |
| company_name | text | NO |  |
| exchange | character varying | YES |  |
| sector | character varying | YES |  |
| industry | character varying | YES |  |
| country | character varying | YES |  |
| logo_url | text | YES |  |
| last_updated | timestamp without time zone | YES |  |

## Table: `tickers`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('tickers_id_seq'::regclass) |
| ticker | character varying | NO |  |
| company_name | text | YES |  |
| last_updated | timestamp without time zone | YES |  |

## Table: `top_stocks`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('top_stocks_id_seq'::regclass) |
| ticker | character varying | NO |  |
| company_name | text | NO |  |
| sector | character varying | NO |  |
| industry | character varying | YES |  |
| market_cap | numeric | YES |  |
| pe_ratio | numeric | YES |  |
| current_price | numeric | YES |  |
| last_updated | timestamp without time zone | YES |  |

## Table: `users`

| Column Name | Data Type | Is Nullable | Default |
|-------------|-----------|------------|---------|
| id | integer | NO | nextval('users_id_seq'::regclass) |
| fs_uniquifier | character varying | NO |  |
| email | character varying | NO |  |
| password | character varying | NO |  |
| active | boolean | YES |  |
| confirmed_at | timestamp without time zone | YES |  |
| first_name | character varying | YES |  |
| last_name | character varying | YES |  |
| created_at | timestamp without time zone | YES |  |
| updated_at | timestamp without time zone | YES |  |

