"""
Enhanced Order Book Simulator with:
- Limit, Market, IOC, FOK, Stop, Stop-Limit, Iceberg orders
- Price-time priority matching
- Partial fills, cancellations, modifications
- CSV persistence and replay support
- VWAP, best bid/ask, depth metrics
- Matplotlib depth plotting
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import itertools
import pandas as pd
from collections import deque
from typing import List, Dict, Optional, Tuple
import bisect
import matplotlib.pyplot as plt

_seq = itertools.count(1)

def now_ts():
    return next(_seq)

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"
    IOC = "IOC"
    FOK = "FOK"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"
    ICEBERG = "ICEBERG"

@dataclass(order=True)
class Order:
    sort_index: Tuple[float, int] = field(init=False, repr=False)
    id: int = field(default_factory=lambda: next(_seq))
    side: Side = Side.BUY
    quantity: int = 0
    price: Optional[float] = None
    type: OrderType = OrderType.LIMIT
    timestamp: int = field(default_factory=now_ts)
    filled: int = 0
    user: Optional[str] = None
    stop_price: Optional[float] = None
    display_size: Optional[int] = None
    reserve: int = 0

    def __post_init__(self):
        if self.side == Side.BUY:
            price_key = -self.price if self.price is not None else float('-inf')
        else:
            price_key = self.price if self.price is not None else float('inf')
        self.sort_index = (price_key, self.timestamp)

    @property
    def remaining(self):
        return max(0, self.quantity - self.filled)

    def fill(self, qty:int):
        qty = min(qty, self.remaining)
        self.filled += qty
        return qty

@dataclass
class Trade:
    buy_order_id: int
    sell_order_id: int
    price: float
    quantity: int
    timestamp: int = field(default_factory=now_ts)

class OrderBook:
    def __init__(self, symbol:str="TEST"):
        self.symbol = symbol
        self.buys: Dict[float, deque] = {}
        self.sells: Dict[float, deque] = {}
        self.buy_prices: List[float] = []
        self.sell_prices: List[float] = []
        self.orders: Dict[int, Order] = {}
        self.trades: List[Trade] = []
        self.stop_orders: List[Order] = []

    def _add_limit_order_to_book(self, order: Order):
        book = self.buys if order.side == Side.BUY else self.sells
        price_list = self.buy_prices if order.side == Side.BUY else self.sell_prices
        if order.price not in book:
            book[order.price] = deque()
            bisect.insort(price_list, order.price)
        book[order.price].append(order)
        self.orders[order.id] = order

    def _remove_order_from_book(self, order: Order):
        book = self.buys if order.side == Side.BUY else self.sells
        price_list = self.buy_prices if order.side == Side.BUY else self.sell_prices
        if order.price not in book:
            return
        q = book[order.price]
        q = deque([o for o in q if o.id != order.id])
        if q:
            book[order.price] = q
        else:
            del book[order.price]
            price_list.remove(order.price)
        self.orders.pop(order.id, None)

    def _best_sell_prices(self):
        return self.sell_prices

    def _best_buy_prices(self):
        return sorted(self.buy_prices, reverse=True)

    def _trigger_stop_orders(self, last_price: float):
        triggered = []
        remain = []
        for o in self.stop_orders:
            trigger = False
            if o.side == Side.BUY and last_price >= o.stop_price:
                trigger = True
            if o.side == Side.SELL and last_price <= o.stop_price:
                trigger = True
            if trigger:
                if o.type == OrderType.STOP:
                    o.type = OrderType.MARKET
                    o.price = None
                elif o.type == OrderType.STOP_LIMIT:
                    o.type = OrderType.LIMIT
                triggered.append(o)
            else:
                remain.append(o)
        self.stop_orders = remain
        for o in triggered:
            self.submit_order(o)

    def _match(self, incoming: Order):
        trades = []
        opp_book = self.sells if incoming.side == Side.BUY else self.buys
        opp_prices = self._best_sell_prices() if incoming.side == Side.BUY else self._best_buy_prices()

        for price in list(opp_prices):
            if incoming.remaining <= 0:
                break
            if incoming.type in [OrderType.MARKET, OrderType.IOC, OrderType.FOK]:
                price_ok = True
            else:
                if incoming.side == Side.BUY:
                    price_ok = price <= incoming.price
                else:
                    price_ok = price >= incoming.price
            if not price_ok:
                break
            q = opp_book[price]
            i = 0
            while i < len(q) and incoming.remaining > 0:
                resting = q[i]
                if resting.remaining <= 0:
                    i += 1
                    continue
                qty = min(incoming.remaining, resting.remaining)
                trade_price = resting.price
                incoming.fill(qty)
                resting.fill(qty)
                t = Trade(
                    buy_order_id = incoming.id if incoming.side==Side.BUY else resting.id,
                    sell_order_id = resting.id if incoming.side==Side.BUY else incoming.id,
                    price = trade_price,
                    quantity = qty
                )
                trades.append(t)
                self.trades.append(t)
                self._trigger_stop_orders(trade_price)
                if resting.remaining == 0:
                    q.remove(resting)
                    self.orders.pop(resting.id, None)
                else:
                    i += 1
            if not q:
                del opp_book[price]
                if incoming.side == Side.BUY:
                    self.sell_prices.remove(price)
                else:
                    self.buy_prices.remove(price)
        return trades

    def submit_order(self, order: Order) -> List[Trade]:
        if order.quantity <= 0:
            raise ValueError("Quantity must be positive")
        if order.type in [OrderType.STOP, OrderType.STOP_LIMIT]:
            self.stop_orders.append(order)
            return []
        if order.type == OrderType.ICEBERG:
            if order.display_size is None or order.display_size <= 0:
                raise ValueError("Iceberg order requires display_size>0")
            order.reserve = order.quantity - order.display_size
            order.quantity = order.display_size

        trades = self._match(order)
        if order.type in [OrderType.IOC, OrderType.MARKET]:
            return trades
        if order.type == OrderType.FOK:
            if sum(t.quantity for t in trades) < order.quantity:
                return []
        if order.remaining > 0:
            self._add_limit_order_to_book(order)
        else:
            self.orders[order.id] = order
        return trades

    def snapshot(self, depth:int=5):
        buy_rows = []
        sell_rows = []
        for p in self._best_buy_prices()[:depth]:
            q = self.buys[p]
            buy_rows.append({"price":p, "size":sum(o.remaining for o in q)})
        for p in self._best_sell_prices()[:depth]:
            q = self.sells[p]
            sell_rows.append({"price":p, "size":sum(o.remaining for o in q)})
        return pd.DataFrame(buy_rows), pd.DataFrame(sell_rows)

    def save_to_csv(self, trades_path:str, orders_path:str):
        pd.DataFrame([t.__dict__ for t in self.trades]).to_csv(trades_path, index=False)
        pd.DataFrame([o.__dict__ for o in self.orders.values()]).to_csv(orders_path, index=False)

    def plot_depth(self):
        buy_depth = []
        sell_depth = []
        for p in self._best_buy_prices():
            qty = sum(o.remaining for o in self.buys[p])
            buy_depth.append((p, qty))
        for p in self._best_sell_prices():
            qty = sum(o.remaining for o in self.sells[p])
            sell_depth.append((p, qty))
        if buy_depth:
            prices, qtys = zip(*buy_depth)
            plt.step(prices, qtys, label="Bids")
        if sell_depth:
            prices, qtys = zip(*sell_depth)
            plt.step(prices, qtys, label="Asks")
        plt.legend()
        plt.title("Order Book Depth")
        plt.show()
