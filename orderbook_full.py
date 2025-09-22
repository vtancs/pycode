
import pygame
import sys
import random
import csv
import time
from collections import defaultdict, deque

# =============================
# Order Book Engine
# =============================

class OrderBook:
    def __init__(self, depth_levels=50, log_file="orderbook_log.csv"):
        self.bids = defaultdict(int)  # price -> qty
        self.asks = defaultdict(int)
        self.trades = deque(maxlen=10)
        self.depth_levels = depth_levels
        self.event_id = 0
        self.log_file = log_file
        self._init_csv()

    def _init_csv(self):
        headers = ["event_id", "timestamp", "event_type", "side", "price", "qty"]
        for i in range(1, self.depth_levels+1):
            headers += [f"Bid{i}_Price", f"Bid{i}_Qty", f"Ask{i}_Price", f"Ask{i}_Qty"]
        with open(self.log_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(headers)

    def _log_trade(self, side, price, qty):
        self.event_id += 1
        row = [self.event_id, time.time(), "TRADE", side, price, qty]
        row += ["" for _ in range(self.depth_levels*4)]
        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def _log_snapshot(self):
        self.event_id += 1
        row = [self.event_id, time.time(), "SNAPSHOT", "", "", ""]
        bids_sorted = sorted(self.bids.items(), key=lambda x: -x[0])[:self.depth_levels]
        asks_sorted = sorted(self.asks.items(), key=lambda x: x[0])[:self.depth_levels]
        for i in range(self.depth_levels):
            if i < len(bids_sorted):
                row += [bids_sorted[i][0], bids_sorted[i][1]]
            else:
                row += ["", ""]
            if i < len(asks_sorted):
                row += [asks_sorted[i][0], asks_sorted[i][1]]
            else:
                row += ["", ""]
        with open(self.log_file, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(row)

    def add_order(self, side, price, qty):
        trades = []
        if side == "BUY":
            while qty > 0 and self.asks and min(self.asks.keys()) <= price:
                best_ask = min(self.asks.keys())
                ask_qty = self.asks[best_ask]
                trade_qty = min(qty, ask_qty)
                qty -= trade_qty
                self.asks[best_ask] -= trade_qty
                if self.asks[best_ask] == 0:
                    del self.asks[best_ask]
                trades.append(("BUY", best_ask, trade_qty))
                self.trades.appendleft((time.time(), "BUY", best_ask, trade_qty))
                self._log_trade("BUY", best_ask, trade_qty)
        else:  # SELL
            while qty > 0 and self.bids and max(self.bids.keys()) >= price:
                best_bid = max(self.bids.keys())
                bid_qty = self.bids[best_bid]
                trade_qty = min(qty, bid_qty)
                qty -= trade_qty
                self.bids[best_bid] -= trade_qty
                if self.bids[best_bid] == 0:
                    del self.bids[best_bid]
                trades.append(("SELL", best_bid, trade_qty))
                self.trades.appendleft((time.time(), "SELL", best_bid, trade_qty))
                self._log_trade("SELL", best_bid, trade_qty)
        if qty > 0:
            if side == "BUY":
                self.bids[price] += qty
            else:
                self.asks[price] += qty
        self._log_snapshot()
        return trades

    def get_depth(self):
        bids_sorted = sorted(self.bids.items(), key=lambda x: -x[0])[:self.depth_levels]
        asks_sorted = sorted(self.asks.items(), key=lambda x: x[0])[:self.depth_levels]
        return bids_sorted, asks_sorted

    def best_bid(self):
        return max(self.bids.keys()) if self.bids else None

    def best_ask(self):
        return min(self.asks.keys()) if self.asks else None

# =============================
# Pygame Visualizer
# =============================

class Visualizer:
    def __init__(self, book: OrderBook):
        pygame.init()
        self.book = book
        self.width, self.height = 800, 600
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Order Book Simulator")
        self.font = pygame.font.SysFont("consolas", 18)
        self.clock = pygame.time.Clock()
        self.flash_rows = {}  # price -> flash time
        self.running = True
        self.random_mode = True

    def draw(self):
        self.screen.fill((20, 20, 20))
        bids, asks = self.book.get_depth()
        mid_x = self.width // 2

        # Draw order book levels
        row_h = 20
        for i in range(max(len(bids), len(asks))):
            y = 50 + i * row_h
            if i < len(bids):
                price, qty = bids[i]
                flash = self.flash_rows.get(price, 0)
                color = (0, 255, 0) if flash <= 0 else (255, 255, 0)
                pygame.draw.rect(self.screen, (0, 80, 0), (mid_x-200, y, 200, row_h))
                text = self.font.render(f"{price:>5} | {qty:<5}", True, color)
                self.screen.blit(text, (mid_x-200, y))
            if i < len(asks):
                price, qty = asks[i]
                flash = self.flash_rows.get(price, 0)
                color = (255, 0, 0) if flash <= 0 else (255, 255, 0)
                pygame.draw.rect(self.screen, (80, 0, 0), (mid_x, y, 200, row_h))
                text = self.font.render(f"{price:>5} | {qty:<5}", True, color)
                self.screen.blit(text, (mid_x, y))

        # Draw trades panel
        y = self.height - 200
        self.screen.blit(self.font.render("Recent Trades:", True, (255, 255, 255)), (20, y))
        for i, trade in enumerate(list(self.book.trades)[:8]):
            t, side, price, qty = trade
            color = (0, 255, 0) if side == "BUY" else (255, 0, 0)
            text = self.font.render(f"{side} {qty}@{price}", True, color)
            self.screen.blit(text, (20, y + 20 + i*20))

        # Draw bid/ask % bar bottom-right
        total_bid = sum(q for _, q in bids)
        total_ask = sum(q for _, q in asks)
        total = total_bid + total_ask
        if total > 0:
            bid_pct = total_bid / total
            ask_pct = total_ask / total
            bar_w, bar_h = 200, 20
            x, y = self.width - bar_w - 20, self.height - bar_h - 20
            pygame.draw.rect(self.screen, (0, 255, 0), (x, y, int(bar_w*bid_pct), bar_h))
            pygame.draw.rect(self.screen, (255, 0, 0), (x+int(bar_w*bid_pct), y, int(bar_w*ask_pct), bar_h))
            text = self.font.render(f"Bids {int(bid_pct*100)}% / Asks {int(ask_pct*100)}%", True, (255, 255, 255))
            self.screen.blit(text, (x, y-20))

        pygame.display.flip()

    def run(self):
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        self.running = False
                    elif event.key == pygame.K_r:
                        self.random_mode = not self.random_mode
                    elif event.key == pygame.K_b:
                        try:
                            price = int(input("Buy price: "))
                            qty = int(input("Buy qty: "))
                            trades = self.book.add_order("BUY", price, qty)
                            for _, p, _ in trades:
                                self.flash_rows[p] = 30
                        except:
                            pass
                    elif event.key == pygame.K_s:
                        try:
                            price = int(input("Sell price: "))
                            qty = int(input("Sell qty: "))
                            trades = self.book.add_order("SELL", price, qty)
                            for _, p, _ in trades:
                                self.flash_rows[p] = 30
                        except:
                            pass
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    row = (y - 50) // 20
                    bids, asks = self.book.get_depth()
                    if x < self.width//2 and row < len(bids):  # left side = BUY
                        price = bids[row][0]
                        trades = self.book.add_order("BUY", price, random.randint(1, 5))
                        for _, p, _ in trades:
                            self.flash_rows[p] = 30
                    elif x > self.width//2 and row < len(asks):  # right side = SELL
                        price = asks[row][0]
                        trades = self.book.add_order("SELL", price, random.randint(1, 5))
                        for _, p, _ in trades:
                            self.flash_rows[p] = 30

            # Flash decay
            for p in list(self.flash_rows.keys()):
                self.flash_rows[p] -= 1
                if self.flash_rows[p] <= 0:
                    del self.flash_rows[p]

            if self.random_mode and random.random() < 0.2:
                side = random.choice(["BUY", "SELL"])
                price = random.randint(90, 110)
                qty = random.randint(1, 5)
                trades = self.book.add_order(side, price, qty)
                for _, p, _ in trades:
                    self.flash_rows[p] = 30

            self.draw()
            self.clock.tick(10)

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    book = OrderBook(depth_levels=50)
    vis = Visualizer(book)
    vis.run()
