import polars as pl
from binance.client import Client


class BinanceDirectDownloader:
    """
    Uses the python-binance library to fetch OHLCV data directly
    from Binance. This can be slower or faster than CCXT depending on
    rate limits and overhead.
    """

    def __init__(self, api_key=None, api_secret=None):
        self.client = Client(api_key, api_secret)

    def fetch_ohlcv(
        self, symbol="BTCUSDT", interval="1h", start_ms=None, end_ms=None
    ) -> pl.DataFrame:
        """Fetch OHLC data for a given symbol and interval.

        :param symbol: e.g. 'BTCUSDT'
        :param interval: e.g. '1m', '1h', '1d' (Binance format)
        :param start_ms: optional - start date timestamp in milliseconds
        :param end_ms: optional - end date timestamp in milliseconds
                 (default will fetch everything up to now)
        :return: Polars DataFrame [open_time, open, high, low, close,
             volume, close_time, ...].
        """
        raw_klines = self.client.get_historical_klines(
            symbol=symbol,
            interval=interval,
            start_str=None if not start_ms else start_ms,
            end_str=None if not end_ms else end_ms,
        )

        # raw_klines returns a list of lists like:
        # [
        #   [
        #       1499040000000,      // Open time
        #       "0.01634790",       // Open
        #       "0.80000000",       // High
        #       "0.01575800",       // Low
        #       "0.01577100",       // Close
        #       "148976.11427815",  // Volume
        #       1499644799999,      // Close time
        #       "2434.19055334",    // Quote asset volume
        #       308,                // Number of trades
        #       "1756.87402397",    // Taker buy base asset volume
        #       "28.46694368",      // Taker buy quote asset volume
        #       "17928899.62484339" // (Ignore)
        #   ]
        # ]

        if not raw_klines:
            return pl.DataFrame()

        df = pl.DataFrame(
            raw_klines,
            schema=[
                "open_time",
                "open",
                "high",
                "low",
                "close",
                "volume",
                "close_time",
                "quote_asset_volume",
                "trades",
                "taker_base_vol",
                "taker_quote_vol",
                "ignore",
            ],
            orient="row",
        )
        # Convert numeric columns appropriately
        df = df.with_columns(
            [
                pl.col("open_time").cast(pl.Datetime("ms")),  # Convert from ms
                pl.col("close_time").cast(pl.Datetime("ms")),
                pl.col("open").cast(pl.Float64),
                pl.col("high").cast(pl.Float64),
                pl.col("low").cast(pl.Float64),
                pl.col("close").cast(pl.Float64),
                pl.col("volume").cast(pl.Float64),
                pl.col("quote_asset_volume").cast(pl.Float64),
                pl.col("trades").cast(pl.Int64),
                pl.col("taker_base_vol").cast(pl.Float64),
                pl.col("taker_quote_vol").cast(pl.Float64),
            ]
        )

        return df
