import os
import time
import logging
from dotenv import load_dotenv
from binance.client import Client as BinanceClient
from bybit import bybit

# Load API keys from .env
load_dotenv()
BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
BINANCE_API_SECRET = os.getenv('BINANCE_API_SECRET')
BYBIT_API_KEY = os.getenv('BYBIT_API_KEY')
BYBIT_API_SECRET = os.getenv('BYBIT_API_SECRET')

# Setup logging
logging.basicConfig(level=logging.INFO)

# Binance & Bybit clients
binance_client = BinanceClient(BINANCE_API_KEY, BINANCE_API_SECRET)
bybit_client = bybit(test=False, api_key=BYBIT_API_KEY, api_secret=BYBIT_API_SECRET)

def get_binance_price(symbol):
    try:
        price = binance_client.get_symbol_ticker(symbol=symbol)
        return float(price['price'])
    except Exception as e:
        logging.error(f"Error fetching Binance price: {e}")
        return None

def get_bybit_price(symbol):
    try:
        ticker = bybit_client.Market.Market_symbolInfo(symbol=symbol).result()[0]
        return float(ticker['last_price'])
    except Exception as e:
        logging.error(f"Error fetching Bybit price: {e}")
        return None

def binance_trade(symbol, side, quantity, stop_loss=None, take_profit=None):
    try:
        order = binance_client.create_order(
            symbol=symbol,
            side=side,
            type='MARKET',
            quantity=quantity
        )
        logging.info(f"Binance {side} order executed: {order}")
        price = float(order['fills'][0]['price'])
        if stop_loss:
            logging.info(f"Set stop loss at {stop_loss}")
        if take_profit:
            logging.info(f"Set take profit at {take_profit}")
    except Exception as e:
        logging.error(f"Binance trade error: {e}")

def bybit_trade(symbol, side, quantity, stop_loss=None, take_profit=None):
    try:
        order = bybit_client.Order.Order_new(side=side, symbol=symbol, order_type="Market", qty=quantity, time_in_force="GoodTillCancel").result()[0]
        logging.info(f"Bybit {side} order executed: {order}")
        if stop_loss or take_profit:
            logging.info(f"Set SL/TP not implemented for spot")
    except Exception as e:
        logging.error(f"Bybit trade error: {e}")

def moving_average_strategy(prices, window=5):
    if len(prices) < window * 2:
        return None
    short_ma = sum(prices[-window:]) / window
    long_ma = sum(prices[-window*2:-window]) / window
    if short_ma > long_ma:
        return 'BUY'
    elif short_ma < long_ma:
        return 'SELL'
    else:
        return None

def main():
    symbol_binance = 'BTCUSDT'
    symbol_bybit = 'BTCUSDT'
    quantity = 0.001
    stop_loss_pct = 0.98
    take_profit_pct = 1.02
    prices_binance = []
    while True:
        price = get_binance_price(symbol_binance)
        if price:
            prices_binance.append(price)
            strategy_signal = moving_average_strategy(prices_binance)
            if strategy_signal:
                stop_loss = price * stop_loss_pct if strategy_signal == 'BUY' else price / stop_loss_pct
                take_profit = price * take_profit_pct if strategy_signal == 'BUY' else price / take_profit_pct
                binance_trade(
                    symbol_binance,
                    side=strategy_signal,
                    quantity=quantity,
                    stop_loss=stop_loss,
                    take_profit=take_profit
                )
        time.sleep(60)

if __name__ == "__main__":
    main()
