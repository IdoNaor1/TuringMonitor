"""
External Data Manager
Fetches weather, stock, and crypto data from external APIs
Runs in background thread to avoid blocking display updates
"""

import threading
import time
import requests
import logging


class ExternalDataManager:
    """Manages external API data fetching"""

    def __init__(self):
        self.data = {}  # Cached data
        self.lock = threading.Lock()
        self.fetch_thread = None
        self.running = False
        self.config = {
            'weather': {'enabled': False, 'api': 'wttr.in', 'location': 'New York', 'interval': 600},
            'stocks': {'enabled': False, 'tickers': [], 'api_key': '', 'interval': 60},
            'crypto': {'enabled': False, 'symbols': [], 'interval': 60}
        }
        self.last_fetch_times = {}

    def configure(self, config):
        """Update configuration"""
        with self.lock:
            if 'weather' in config:
                self.config['weather'].update(config['weather'])
            if 'stocks' in config:
                self.config['stocks'].update(config['stocks'])
            if 'crypto' in config:
                self.config['crypto'].update(config['crypto'])

    def start(self):
        """Start background fetch thread"""
        if self.running:
            return

        self.running = True
        self.fetch_thread = threading.Thread(target=self._fetch_loop, daemon=True)
        self.fetch_thread.start()

    def stop(self):
        """Stop background fetch thread"""
        self.running = False
        if self.fetch_thread:
            self.fetch_thread.join(timeout=5.0)

    def get_data(self):
        """Get cached data (never blocks)"""
        with self.lock:
            return self.data.copy()

    def _fetch_loop(self):
        """Main fetch loop (runs in background thread)"""
        while self.running:
            try:
                current_time = time.time()

                # Fetch weather if enabled and interval elapsed
                if self.config['weather']['enabled']:
                    interval = self.config['weather']['interval']
                    last_fetch = self.last_fetch_times.get('weather', 0)
                    if current_time - last_fetch >= interval:
                        self._fetch_weather()
                        self.last_fetch_times['weather'] = current_time

                # Fetch stocks if enabled
                if self.config['stocks']['enabled']:
                    interval = self.config['stocks']['interval']
                    last_fetch = self.last_fetch_times.get('stocks', 0)
                    if current_time - last_fetch >= interval:
                        self._fetch_stocks()
                        self.last_fetch_times['stocks'] = current_time

                # Fetch crypto if enabled
                if self.config['crypto']['enabled']:
                    interval = self.config['crypto']['interval']
                    last_fetch = self.last_fetch_times.get('crypto', 0)
                    if current_time - last_fetch >= interval:
                        self._fetch_crypto()
                        self.last_fetch_times['crypto'] = current_time

                time.sleep(5)  # Check every 5 seconds

            except Exception as e:
                logging.error(f"Error in fetch loop: {e}")
                time.sleep(10)  # Back off on error

    def _fetch_weather(self):
        """Fetch weather data from wttr.in"""
        try:
            location = self.config['weather']['location']
            url = f"https://wttr.in/{location}?format=j1"

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            current = data['current_condition'][0]

            with self.lock:
                self.data['weather_temp'] = current['temp_C']
                self.data['weather_temp_f'] = current['temp_F']
                self.data['weather_condition'] = current['weatherDesc'][0]['value']
                self.data['weather_humidity'] = current['humidity']
                self.data['weather_wind_speed'] = current['windspeedKmph']

            logging.info(f"Weather data fetched: {current['temp_C']}°C, {current['weatherDesc'][0]['value']}")

        except Exception as e:
            logging.error(f"Weather fetch error: {e}")
            # Keep existing cached values

    def _fetch_stocks(self):
        """Fetch stock prices using yfinance as fallback"""
        try:
            import yfinance as yf

            tickers = self.config['stocks']['tickers']
            if not tickers:
                return

            for ticker in tickers:
                try:
                    stock = yf.Ticker(ticker)
                    info = stock.info

                    with self.lock:
                        self.data[f'stock_{ticker}_price'] = info.get('currentPrice', info.get('regularMarketPrice', 0))
                        self.data[f'stock_{ticker}_change'] = info.get('regularMarketChange', 0)

                    logging.info(f"Stock {ticker} fetched: ${info.get('currentPrice', info.get('regularMarketPrice', 0))}")

                except Exception as e:
                    logging.error(f"Error fetching {ticker}: {e}")

        except ImportError:
            logging.warning("yfinance not installed - stock tracking unavailable")
            with self.lock:
                self.data['stock_error'] = 'yfinance not installed'

    def _fetch_crypto(self):
        """Fetch crypto prices from CoinGecko (no API key required)"""
        try:
            symbols = self.config['crypto']['symbols']
            if not symbols:
                return

            # CoinGecko uses lowercase IDs
            ids = ','.join([s.lower() for s in symbols])
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids}&vs_currencies=usd&include_24hr_change=true"

            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            with self.lock:
                for symbol in symbols:
                    symbol_lower = symbol.lower()
                    if symbol_lower in data:
                        self.data[f'crypto_{symbol}_price'] = data[symbol_lower]['usd']
                        self.data[f'crypto_{symbol}_change_24h'] = data[symbol_lower].get('usd_24h_change', 0)
                        logging.info(f"Crypto {symbol} fetched: ${data[symbol_lower]['usd']}")

        except Exception as e:
            logging.error(f"Crypto fetch error: {e}")


# For testing
if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)

    print("Testing ExternalDataManager...")

    manager = ExternalDataManager()

    # Test weather
    manager.configure({
        'weather': {
            'enabled': True,
            'location': 'London',
            'interval': 5  # 5 seconds for testing
        }
    })

    manager.start()

    print("Waiting 10 seconds for data to fetch...")
    time.sleep(10)

    data = manager.get_data()
    print(f"\nFetched data: {data}")

    manager.stop()
    print("\nExternalDataManager test complete!")
