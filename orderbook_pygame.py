"""
Order Book Simulator with Pygame Visualization
- Uses the enhanced order book matching engine
- Displays order book depth in real-time using pygame
- Bids = green bars, Asks = red bars
- Trades flash as yellow markers
"""

import random
import time
import pygame
from dataclasses import dataclass, field
from enum import Enum
import itertools
from collections import deque
import bisect

_seq = itertools.count(1)
def now_ts(): return next(_seq)

class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

class OrderType(Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"

@dataclass(order=True)
class Order:
    sort_index: tuple = field(init=False, repr=False)
    id: int = field(default_factory=lambda: next(_seq))
    side: Side = Side.BUY
    quantity: int = 0
    price: float = 0.0
    type: OrderType = OrderType.LIMIT
    timestamp: int = field(default_factory=now_ts)
    filled: int = 0

    def __post_init__(self):
        if self.side == Side.BUY:
            price_key = -self.price
        else:
            price_key = self.price
        self.sort_index = (price_key, self.timestamp)

    @property
    def remaining(self): return max(0, self.quantity - self.filled)
    def fill(self, qty): 
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
    def __init__(self, symbol="TEST"):
        self.symbol = symbol
        self.buys = {}
        self.sells = {}
        self.buy_prices = []
        self.sell_prices = []
        self.orders = {}
        self.trades = []

    def _add(self, order: Order):
        book = self.buys if order.side == Side.BUY else self.sells
        prices = self.buy_prices if order.side == Side.BUY else self.sell_prices
        if order.price not in book:
            book[order.price] = deque()
            bisect.insort(prices, order.price)
        book[order.price].append(order)
        self.orders[order.id] = order

    def _best_sell_prices(self): return self.sell_prices
    def _best_buy_prices(self): return sorted(self.buy_prices, reverse=True)

    def _match(self, incoming: Order):
        trades = []
        opp_book = self.sells if incoming.side == Side.BUY else self.buys
        opp_prices = self._best_sell_prices() if incoming.side == Side.BUY else self._best_buy_prices()

        for price in list(opp_prices):
            if incoming.remaining <= 0: break
            if incoming.side == Side.BUY and price > incoming.price: break
            if incoming.side == Side.SELL and price < incoming.price: break
            q = opp_book[price]
            i = 0
            while i < len(q) and incoming.remaining > 0:
                resting = q[i]
                if resting.remaining <= 0: 
                    i += 1
                    continue
                qty = min(incoming.remaining, resting.remaining)
                incoming.fill(qty)
                resting.fill(qty)
                t = Trade(
                    buy_order_id=incoming.id if incoming.side==Side.BUY else resting.id,
                    sell_order_id=resting.id if incoming.side==Side.BUY else incoming.id,
                    price=price, quantity=qty)
                trades.append(t)
                self.trades.append(t)
                if resting.remaining == 0:
                    q.remove(resting)
                    self.orders.pop(resting.id, None)
                else:
                    i += 1
            if not q:
                del opp_book[price]
                if incoming.side == Side.BUY: self.sell_prices.remove(price)
                else: self.buy_prices.remove(price)
        return trades

    def submit(self, order: Order):
        trades = self._match(order)
        if order.remaining > 0 and order.type == OrderType.LIMIT:
            self._add(order)
        return trades

    def snapshot(self, depth=10):
        bids = [(p, sum(o.remaining for o in self.buys[p])) for p in self._best_buy_prices()[:depth]]
        asks = [(p, sum(o.remaining for o in self.sells[p])) for p in self._best_sell_prices()[:depth]]
        return bids, asks

# ---------------- Pygame Visualizer ----------------

class Visualizer:
    def __init__(self, book: OrderBook, width=800, height=600):
        pygame.init()
        self.book = book
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Order Book Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Arial", 16)
        self.last_trades = []

    def draw(self):
        self.screen.fill((0,0,0))
        bids, asks = self.book.snapshot(depth=10)

        max_qty = 1
        if bids: max_qty = max(max_qty, max(q for _,q in bids))
        if asks: max_qty = max(max_qty, max(q for _,q in asks))

        # Draw bids (left side)
        for i,(p,q) in enumerate(bids):
            bar_w = int((q/max_qty) * (self.width//2 - 50))
            bar_h = 20
            x = self.width//2 - bar_w
            y = self.height - (i+1)*bar_h - 20
            pygame.draw.rect(self.screen,(0,200,0),(x,y,bar_w,bar_h))
            self.screen.blit(self.font.render(f"{p:.2f} | {q}",True,(255,255,255)),(x-100,y))

        # Draw asks (right side)
        for i,(p,q) in enumerate(asks):
            bar_w = int((q/max_qty) * (self.width//2 - 50))
            bar_h = 20
            x = self.width//2
            y = 20 + i*bar_h
            pygame.draw.rect(self.screen,(200,0,0),(x,y,bar_w,bar_h))
            self.screen.blit(self.font.render(f"{p:.2f} | {q}",True,(255,255,255)),(x+bar_w+5,y))

        # Draw last trades
        for i,t in enumerate(self.last_trades[-5:]):
            txt = f"TRADE {t.quantity}@{t.price:.2f}"
            self.screen.blit(self.font.render(txt,True,(255,255,0)),(10,10+i*18))

        pygame.display.flip()

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT: running=False
            # Simulate random order flow
            side = random.choice([Side.BUY,Side.SELL])
            price = round(random.uniform(90,110),2)
            qty = random.randint(1,50)
            o = Order(side=side,price=price,quantity=qty)
            trades = self.book.submit(o)
            if trades: self.last_trades.extend(trades)

            self.draw()
            self.clock.tick(2) # 2 updates per second
        pygame.quit()

if __name__=="__main__":
    book = OrderBook("DEMO")
    vis = Visualizer(book)
    vis.run()
