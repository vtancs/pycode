"""
Order Book Visualizer (Grid UI, Aggregated Levels, Percentage Bar)

Features:
- Aggregates orders by price level and shows top N levels for bids and asks (depth table).
- Top percentage bar showing Bid vs Ask ratio (based on summed visible depth).
- Grid-style order book similar to the attached screenshot: Bid rows on left (green), Ask rows on right (red).
- Manual order placement with B/S keys (console input), toggle random flow with R, ESC to exit.
- Random simulation enabled by default.
"""

import pygame
import random
import bisect
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
import itertools

_seq = itertools.count(1)
def now_ts(): return next(_seq)

# ---- Order/matching engine (simple aggregated-level engine) ----
class Side(Enum):
    BUY = "BUY"
    SELL = "SELL"

@dataclass
class Order:
    id: int = field(default_factory=lambda: next(_seq))
    side: Side = Side.BUY
    price: float = 0.0
    quantity: int = 0
    filled: int = 0
    timestamp: int = field(default_factory=now_ts)

    @property
    def remaining(self):
        return max(0, self.quantity - self.filled)

class Trade:
    def __init__(self, buy_id, sell_id, price, qty):
        self.buy_id = buy_id
        self.sell_id = sell_id
        self.price = price
        self.qty = qty

class OrderBook:
    def __init__(self):
        # price -> deque of orders (time priority)
        self.buys = {}   # price -> deque
        self.sells = {}
        self.buy_prices = []   # descending maintained separately
        self.sell_prices = []  # ascending
        self.orders = {}
        self.trades = []

    def _add_level(self, price_list, price, descending=False):
        # insert price into sorted list (keep uniq)
        if price in price_list: return
        if descending:
            # maintain descending by inserting position for -price
            idx = bisect.bisect_left([-p for p in price_list], -price)
            price_list.insert(idx, price)
        else:
            bisect.insort_left(price_list, price)

    def add_limit(self, order: Order):
        book = self.buys if order.side == Side.BUY else self.sells
        prices = self.buy_prices if order.side == Side.BUY else self.sell_prices
        if order.price not in book:
            book[order.price] = deque()
            self._add_level(prices, order.price, descending=(order.side==Side.BUY))
        book[order.price].append(order)
        self.orders[order.id] = order
        return self.match(order)  # attempt match immediately

    def match(self, incoming: Order):
        """Match incoming order against opposite book using price-time priority at aggregated levels."""
        trades = []
        if incoming.side == Side.BUY:
            # match against lowest asks first (ascending sell_prices)
            for price in list(self.sell_prices):
                if incoming.remaining <= 0: break
                if price > incoming.price: break  # limit check
                q = self.sells[price]
                while q and incoming.remaining > 0:
                    resting = q[0]
                    qty = min(incoming.remaining, resting.remaining)
                    incoming.filled += qty
                    resting.filled += qty
                    trades.append(Trade(incoming.id, resting.id, price, qty))
                    self.trades.append((price, qty))
                    if resting.remaining == 0:
                        q.popleft()
                        self.orders.pop(resting.id, None)
                if not q:
                    del self.sells[price]
                    self.sell_prices.remove(price)
        else:
            # SELL incoming: match against highest buys first
            for price in list(self.buy_prices):
                if incoming.remaining <= 0: break
                if price < incoming.price: break
                q = self.buys[price]
                while q and incoming.remaining > 0:
                    resting = q[0]
                    qty = min(incoming.remaining, resting.remaining)
                    incoming.filled += qty
                    resting.filled += qty
                    trades.append(Trade(resting.id, incoming.id, price, qty))
                    self.trades.append((price, qty))
                    if resting.remaining == 0:
                        q.popleft()
                        self.orders.pop(resting.id, None)
                if not q:
                    del self.buys[price]
                    self.buy_prices.remove(price)
        # If incoming still has remaining and is a limit order, add rest to book
        if incoming.remaining > 0:
            # For buys we add remaining at incoming.price etc.
            book = self.buys if incoming.side==Side.BUY else self.sells
            prices = self.buy_prices if incoming.side==Side.BUY else self.sell_prices
            if incoming.price not in book:
                book[incoming.price] = deque()
                self._add_level(prices, incoming.price, descending=(incoming.side==Side.BUY))
            book[incoming.price].append(incoming)
            self.orders[incoming.id] = incoming
        return trades

    def aggregate_levels(self, depth=5):
        """Return aggregated (price, total_qty, num_orders) for bids and asks."""
        bids = []
        asks = []
        for p in sorted(self.buy_prices, reverse=True)[:depth]:
            total = sum(o.remaining for o in self.buys.get(p, []))
            count = len(self.buys.get(p, []))
            bids.append((p, total, count))
        for p in sorted(self.sell_prices)[:depth]:
            total = sum(o.remaining for o in self.sells.get(p, []))
            count = len(self.sells.get(p, []))
            asks.append((p, total, count))
        return bids, asks

    def best(self):
        bid = max(self.buy_prices) if self.buy_prices else None
        ask = min(self.sell_prices) if self.sell_prices else None
        return bid, ask

# ---- Pygame UI ----
class OrderBookUI:
    def __init__(self, book: OrderBook, width=900, height=600, depth=6):
        pygame.init()
        self.book = book
        self.width = width
        self.height = height
        self.depth = depth
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Order Book - Grid UI")
        self.font_small = pygame.font.SysFont("Arial", 14)
        self.font_med = pygame.font.SysFont("Arial", 16, bold=True)
        self.clock = pygame.time.Clock()
        self.random_flow = True
        self.last_trades = []  # recent trades list of (price, qty)
        self.bg_color = (18,18,20)
        self.panel_color = (30,32,36)
        self.running = True

    def draw_percentage_bar(self, bids_total, asks_total):
        # top area: a horizontal bar showing bid vs ask ratio (left = bid green, right = ask red)
        bar_w = self.width - 40
        bar_h = 28
        x = 20
        y = 12
        total = max(1, bids_total + asks_total)
        bid_frac = bids_total / total
        bid_w = int(bar_w * bid_frac)
        ask_w = bar_w - bid_w
        # background panel
        pygame.draw.rect(self.screen, (25,26,30), (x-2, y-2, bar_w+4, bar_h+4), border_radius=6)
        # draw bid segment
        pygame.draw.rect(self.screen, (24,160,80), (x, y, bid_w, bar_h), border_radius=6)
        # draw ask segment
        pygame.draw.rect(self.screen, (200,60,60), (x+bid_w, y, ask_w, bar_h), border_radius=6)
        # draw percentage text
        bid_pct = int(bid_frac*100)
        ask_pct = 100 - bid_pct
        txt = f"Bid {bid_pct}%    Ask {ask_pct}%"
        surf = self.font_med.render(txt, True, (230,230,230))
        self.screen.blit(surf, (x + bar_w//2 - surf.get_width()//2, y + bar_h//2 - surf.get_height()//2))

    def draw_grid(self, bids, asks):
        # left column for bids, right column for asks
        margin_x = 20
        top_y = 70
        row_h = 44
        col_w = (self.width - 2*margin_x) // 2 - 10
        max_qty = 1
        for (_,q,_) in bids+asks:
            if q > max_qty: max_qty = q

        # header labels
        self.screen.blit(self.font_med.render("Bid", True, (200,255,200)), (margin_x, top_y - 34))
        self.screen.blit(self.font_med.render("Ask", True, (255,200,200)), (self.width - margin_x - 40, top_y - 34))

        for i in range(self.depth):
            y = top_y + i*row_h
            # background box for each side
            pygame.draw.rect(self.screen, self.panel_color, (margin_x, y, col_w, row_h-8), border_radius=6)
            pygame.draw.rect(self.screen, self.panel_color, (self.width - margin_x - col_w, y, col_w, row_h-8), border_radius=6)

            # draw bid row if present
            if i < len(bids):
                p, q, cnt = bids[i]
                # background intensity based on quantity proportion
                ratio = min(1.0, q / max_qty)
                band_w = int(ratio * (col_w - 24))
                band_rect = (margin_x+8, y+8, band_w, row_h-24)
                pygame.draw.rect(self.screen, (12,110,55), band_rect, border_radius=4)
                # texts
                price_s = self.font_med.render(f"{p:.2f}", True, (230,230,230))
                qty_s = self.font_med.render(f"{q}", True, (230,230,230))
                cnt_s = self.font_small.render(f"{cnt}", True, (190,190,190))
                self.screen.blit(price_s, (margin_x+12, y+8))
                self.screen.blit(qty_s, (margin_x+col_w - qty_s.get_width() - 12, y+8))
                self.screen.blit(cnt_s, (margin_x+col_w - qty_s.get_width() - 44, y+10))

            # draw ask row if present
            if i < len(asks):
                p, q, cnt = asks[i]
                ratio = min(1.0, q / max_qty)
                band_w = int(ratio * (col_w - 24))
                band_rect = (self.width - margin_x - 8 - band_w, y+8, band_w, row_h-24)
                pygame.draw.rect(self.screen, (150,30,30), band_rect, border_radius=4)
                price_s = self.font_med.render(f"{p:.2f}", True, (230,230,230))
                qty_s = self.font_med.render(f"{q}", True, (230,230,230))
                cnt_s = self.font_small.render(f"{cnt}", True, (190,190,190))
                self.screen.blit(price_s, (self.width - margin_x - col_w + 12, y+8))
                self.screen.blit(qty_s, (self.width - margin_x - qty_s.get_width() - 12, y+8))
                self.screen.blit(cnt_s, (self.width - margin_x - qty_s.get_width() - 44, y+10))

        # draw mid spread box with best bid/ask
        bid, ask = self.book.best()
        mid_x = self.width//2 - 60
        mid_y = top_y + self.depth*row_h//2 - 20
        pygame.draw.rect(self.screen, (40,40,44), (mid_x, mid_y, 120, 48), border_radius=8)
        if bid is not None and ask is not None:
            spread = ask - bid
            txt1 = self.font_small.render(f"Bid {bid:.2f}", True, (180,255,180))
            txt2 = self.font_small.render(f"Ask {ask:.2f}", True, (255,200,200))
            txt3 = self.font_small.render(f"Spread {spread:.2f}", True, (220,220,220))
            self.screen.blit(txt1, (mid_x+8, mid_y+6))
            self.screen.blit(txt2, (mid_x+8, mid_y+24))
            self.screen.blit(txt3, (mid_x+8, mid_y+36))

    def draw_trades_panel(self):
        # small panel on bottom-left showing recent trades
        x = 20
        y = self.height - 140
        w = 340
        h = 120
        pygame.draw.rect(self.screen, (22,24,28), (x, y, w, h), border_radius=8)
        self.screen.blit(self.font_med.render("Recent Trades", True, (230,230,0)), (x+8, y+6))
        for i, (price, qty) in enumerate(self.last_trades[-8:]):
            t = self.font_small.render(f"{qty} @ {price:.2f}", True, (220,220,220))
            self.screen.blit(t, (x+10, y+32 + i*14))

    def step_random_order(self):
        side = random.choice([Side.BUY, Side.SELL])
        # price around center 100 with small ticks
        price = round(random.uniform(99.0, 101.0), 2)
        qty = random.choice([50,100,200,300,500,1000])
        o = Order(side=side, price=price, quantity=qty)
        trades = self.book.add_limit(o)
        for tr in trades:
            self.last_trades.append((tr.price, tr.qty))
        if len(self.last_trades) > 300: self.last_trades = self.last_trades[-300:]

    def run(self):
        tick = 0
        while self.running:
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.running = False
                elif ev.type == pygame.KEYDOWN:
                    if ev.key == pygame.K_ESCAPE:
                        self.running = False
                    elif ev.key == pygame.K_r:
                        self.random_flow = not self.random_flow
                    elif ev.key == pygame.K_b:
                        # manual BUY
                        try:
                            price = float(input("BUY price: "))
                            qty = int(input("BUY qty: "))
                        except Exception as e:
                            print("Invalid input, using random defaults.")
                            price = round(random.uniform(99.0,101.0),2)
                            qty = random.choice([100,200,500])
                        o = Order(side=Side.BUY, price=price, quantity=qty)
                        trades = self.book.add_limit(o)
                        for tr in trades:
                            self.last_trades.append((tr.price, tr.qty))
                    elif ev.key == pygame.K_s:
                        # manual SELL
                        try:
                            price = float(input("SELL price: "))
                            qty = int(input("SELL qty: "))
                        except:
                            print("Invalid input, using random defaults.")
                            price = round(random.uniform(99.0,101.0),2)
                            qty = random.choice([100,200,500])
                        o = Order(side=Side.SELL, price=price, quantity=qty)
                        trades = self.book.add_limit(o)
                        for tr in trades:
                            self.last_trades.append((tr.price, tr.qty))

            if self.random_flow and (tick % 3 == 0):
                # occasional random action
                self.step_random_order()

            # draw background
            self.screen.fill((18,18,20))
            # aggregate levels
            bids, asks = self.book.aggregate_levels(depth=self.depth)
            bids_total = sum(q for (_,q,_) in bids)
            asks_total = sum(q for (_,q,_) in asks)
            # draw percent bar
            self.draw_percentage_bar(bids_total, asks_total)
            # draw grid of levels
            self.draw_grid(bids, asks)
            # trades panel
            self.draw_trades_panel()

            pygame.display.flip()
            self.clock.tick(20)
            tick += 1
        pygame.quit()

if __name__=="__main__":
    # seed demo book
    ob = OrderBook()
    # seed sells (asks)
    for i in range(101, 106):
        price = float(i)
        for _ in range(random.randint(1,3)):
            o = Order(side=Side.SELL, price=price, quantity=random.choice([100,200,300,500]))
            ob.add_limit(o)
    # seed buys (bids)
    for i in range(96, 101):
        price = float(i)
        for _ in range(random.randint(1,3)):
            o = Order(side=Side.BUY, price=price, quantity=random.choice([100,200,300,500]))
            ob.add_limit(o)

    ui = OrderBookUI(ob, width=900, height=600, depth=6)
    ui.run()
