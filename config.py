# config.py

# Binance Spot Test Network Credentials
BINANCE_API_KEY = 'npRsgGZsD8BLp3n3NSw4xIEzkdeElxs120bK29uVqy6oYAXuUPOTsz4g5z97SwfA'
BINANCE_SECRET_KEY = 'JvBW1htOTM5cMQ6Kbsp9qnGTmKDN3E13cbYPfAO5qU2z7ZNM11jyYzecYobbfFyX'

# Trading Parameters
SYMBOL = 'BTC/USDT'
FIRST_BUY_AMOUNT = 15.0     # Minimum > 10 USDT হতে হবে
TAKE_PROFIT_PCT = 0.1       # +1.5% লাভে সেল
DROP_TO_BUY_PCT = 0.2       # -2.0% ডাউনে মার্জিন কল
MAX_MARGIN_CALLS = 3        

DB_FILE = "trading_bot.db"