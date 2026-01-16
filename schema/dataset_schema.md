# Dataset Schema — Phase 1

## OHLCV (1-minute bars)
**File pattern:** `ohlcv_<exchange>_<symbol>_<timeframe>.parquet`

| Column     | Type        | Description |
|-----------|-------------|-------------|
| ts        | int64       | Unix epoch in milliseconds (UTC) |
| dt_utc    | string/ISO  | UTC timestamp ISO-8601 |
| open      | float64     | Open price |
| high      | float64     | High price |
| low       | float64     | Low price |
| close     | float64     | Close price |
| volume    | float64     | Traded volume (as provided by exchange) |

## Trades
**File pattern:** `trades_<exchange>_<symbol>.parquet`

| Column     | Type        | Description |
|-----------|-------------|-------------|
| ts        | int64       | Unix epoch in milliseconds (UTC) |
| dt_utc    | string/ISO  | UTC timestamp ISO-8601 |
| price     | float64     | Trade price |
| amount    | float64     | Trade size (if available) |
| side      | string      | buy/sell (if available) |
| trade_id  | string/int  | Exchange trade id (if available) |

## Notes
- Column availability may vary by exchange/API response.
- All timestamps must be treated as UTC.