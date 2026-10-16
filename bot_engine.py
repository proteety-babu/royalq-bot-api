# bot_engine.py
import ccxt
import asyncio
import logging
import config
import database
import encryption

# --- লগিং (Logging) কনফিগারেশন ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.FileHandler("bot_activity.log", encoding="utf-8"), # ফাইলে সেভ হবে
        logging.StreamHandler() # টার্মিনালেও দেখাবে
    ]
)

# সুরক্ষিত চাবি ডিক্রিপ্ট করে ব্যবহার করার লজিক
enc_api = encryption.encrypt_data(config.BINANCE_API_KEY)
enc_secret = encryption.encrypt_data(config.BINANCE_SECRET_KEY)

exchange = ccxt.binance({
    'apiKey': encryption.decrypt_data(enc_api),
    'secret': encryption.decrypt_data(enc_secret),
    'enableRateLimit': True,
})
exchange.set_sandbox_mode(True) # Testnet Active

def get_live_price(symbol):
    try:
        ticker = exchange.fetch_ticker(symbol)
        return ticker['last']
    except Exception as e:
        logging.error(f"Price Fetch Error for {symbol}: {e}")
        return None

def execute_market_buy(symbol, usdt_amount):
    try:
        price = get_live_price(symbol)
        crypto_amount = usdt_amount / price
        crypto_amount = exchange.amount_to_precision(symbol, crypto_amount)
        
        logging.info(f"💰 Sending Market BUY Order: {crypto_amount} {symbol.split('/')[0]}")
        order = exchange.create_market_buy_order(symbol, crypto_amount)
        
        actual_filled_price = order.get('average', price)
        actual_filled_crypto = float(order.get('amount', crypto_amount))
        return actual_filled_price, actual_filled_crypto
    except Exception as e:
        logging.error(f"Buy Order Failed: {e}")
        return None, None

def execute_market_sell(symbol, crypto_amount):
    try:
        crypto_amount = exchange.amount_to_precision(symbol, crypto_amount)
        logging.info(f"🔻 Sending Market SELL Order: {crypto_amount} {symbol.split('/')[0]}")
        order = exchange.create_market_sell_order(symbol, crypto_amount)
        return order
    except Exception as e:
        logging.error(f"Sell Order Failed: {e}")
        return None

async def start_trading_engine(bot_control):
    logging.info("🤖 Trading Engine Started via API...")
    database.init_db()

    # এপিআই থেকে আসা সেটিংস বা ডিফল্ট সেটিংস
    settings = bot_control.get("settings", {})
    symbol = settings.get("symbol", config.SYMBOL)
    first_buy_amount = settings.get("first_buy_amount", config.FIRST_BUY_AMOUNT)
    take_profit_pct = settings.get("take_profit_pct", config.TAKE_PROFIT_PCT)
    drop_to_buy_pct = settings.get("drop_to_buy_pct", config.DROP_TO_BUY_PCT)
    max_margin_calls = settings.get("max_margin_calls", config.MAX_MARGIN_CALLS)

    pos = database.load_position(symbol)
    is_holding = pos['is_holding']
    avg_price = pos['average_price']
    total_crypto = pos['total_crypto']
    total_spent = pos['total_spent']
    margin_calls = pos['margin_calls']
    
    # ট্রেইলিং স্টপ লসের জন্য পিক প্রাইস
    peak_price = 0

    while bot_control.get("is_running", False):
        live_price = get_live_price(symbol)
        if not live_price:
            await asyncio.sleep(5)
            continue

        if not is_holding:
            logging.info(f"🟢 [Fresh Start] Buying First Call for {symbol} at: ${live_price}")
            buy_price, crypto_qty = execute_market_buy(symbol, first_buy_amount)
            if buy_price:
                is_holding = True
                avg_price = buy_price
                total_crypto = crypto_qty
                total_spent = first_buy_amount
                margin_calls = 0
                peak_price = 0 # রিসেট
                database.save_position(symbol, is_holding, avg_price, total_crypto, total_spent, margin_calls)
        else:
            
            if avg_price <= 0:
               is_holding = False
               continue

            price_change = ((live_price - avg_price) / avg_price) * 100
            
            # print এর বদলে logging.info ব্যবহার করা হলো এবং symbol যোগ করা হলো
            logging.info(f"📊 {symbol} | Live: ${live_price:.2f} | Avg: ${avg_price:.2f} | Change: {price_change:.2f}% | Calls: {margin_calls}")
            

            # --- ট্রেইলিং টেক প্রফিট লজিক ---
            if price_change >= take_profit_pct:
                if live_price > peak_price:
                    peak_price = live_price
                    logging.info(f"📈 New Peak Detected: ${peak_price:.2f}")

                # পিক থেকে ০.৫% নিচে নামলেই সেল
                trailing_drop_threshold = peak_price * (1 - 0.005) 
                
                if live_price <= trailing_drop_threshold:
                    logging.info(f"🚀 Trailing Profit Target Hit! Selling at ${live_price:.2f}...")
                    if execute_market_sell(symbol, total_crypto):
                        is_holding = False
                        peak_price = 0
                        database.save_position(symbol, False, 0, 0, 0, 0)
                        logging.info("✅ Cycle Completed with Trailing Stop!")
            
            # --- মার্জিন কল লজিক ---
            elif price_change <= -drop_to_buy_pct and margin_calls < max_margin_calls:
                margin_calls += 1
                logging.warning(f"⚠️ Market Down! Margin Call {margin_calls} Executing...")
                buy_price, crypto_qty = execute_market_buy(symbol, first_buy_amount)
                if buy_price:
                    total_crypto += crypto_qty
                    total_spent += first_buy_amount
                    avg_price = total_spent / total_crypto
                    database.save_position(symbol, is_holding, avg_price, total_crypto, total_spent, margin_calls)

        await asyncio.sleep(5)
    
    logging.info(f"🛑 Trading Engine Stopped for {symbol}.")