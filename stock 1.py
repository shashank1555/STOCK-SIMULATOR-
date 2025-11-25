import random
import time

try:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle
except:
    plt = None
    Rectangle = None

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

INITIAL = {
    "APPLE": 150.00,
    "GOOGLE": 2800.00,
    "AMAZON": 3400.00,
    "TESLA": 700.00
}

stocks = INITIAL.copy()
old_prices = INITIAL.copy()

price_history = {s: [] for s in stocks}
ohlc_history = {s: [] for s in stocks}

balance = 10000.0
portfolio = {}

pending_boosts = {}
last_prediction_dir = {}

TICK_SIGMA = 0.004

# ============================
# PRELOAD REALISTIC HISTORY
# ============================
def preload_history():
    for s, base in INITIAL.items():
        last = base * 0.97
        for _ in range(10):
            pct = random.normalvariate(0, TICK_SIGMA)
            close = round(last * (1 + pct), 2)
            high = round(max(last, close) * (1 + random.uniform(0.001, 0.004)), 2)
            low = round(min(last, close) * (1 - random.uniform(0.001, 0.004)), 2)

            ohlc_history[s].append((last, high, low, close))
            price_history[s].append(close)
            last = close

        stocks[s] = last
        old_prices[s] = last

preload_history()

# ============================
# PREDICTION SYSTEM
# ============================
def predict(stock):
    h = price_history[stock]
    if len(h) < 4:
        last_prediction_dir[stock] = "NEUTRAL"
        return h[-1]

    d1 = h[-1] - h[-2]
    d2 = h[-2] - h[-3]
    d3 = h[-3] - h[-4]

    avg = (d1 + d2 + d3) / 3
    predicted = round(h[-1] + avg, 2)

    if predicted > h[-1]:
        last_prediction_dir[stock] = "UP"
    elif predicted < h[-1]:
        last_prediction_dir[stock] = "DOWN"
    else:
        last_prediction_dir[stock] = "NEUTRAL"

    return predicted

# ============================
# MARKET UPDATE (NO INSIDER TIP)
# ============================
def update_market():
    for s in stocks:
        open_price = stocks[s]
        price = open_price
        high = open_price
        low = open_price

        bias = 0
        direction = last_prediction_dir.get(s, "NEUTRAL")

        if direction == "UP" and random.random() < 0.8:
            bias = random.uniform(0.002, 0.01)

        elif direction == "DOWN" and random.random() < 0.8:
            bias = -random.uniform(0.002, 0.01)

        for _ in range(10):
            pct = random.normalvariate(0, TICK_SIGMA) + bias
            price = round(price * (1 + pct), 2)
            high = max(high, price)
            low = min(low, price)

        price += pending_boosts.pop(s, 0)
        price = round(price, 2)

        ohlc_history[s].append((open_price, high, low, price))
        price_history[s].append(price)
        old_prices[s] = open_price
        stocks[s] = price

# ============================
# SHOW MARKET
# ============================
def show_market():
    update_market()
    print("\n--- MARKET ---")
    for s in stocks:
        now = stocks[s]
        prev = old_prices[s]
        pct = ((now - prev) / prev) * 100 if prev else 0

        col = GREEN if pct > 0 else RED if pct < 0 else RESET
        sign = "+" if pct > 0 else ""
        print(f"{YELLOW}{s}{RESET}: ${now}  {col}({sign}{round(pct, 2)}%){RESET}")

# ============================
# BUY
# ============================
def buy():
    global balance

    s = input("Stock: ").upper()
    if s not in stocks:
        print("Invalid stock.")
        return

    q = input("Qty: ")
    if not q.isdigit():
        print("Invalid.")
        return

    q = int(q)
    cost = q * stocks[s]

    if cost > balance:
        print("Not enough balance.")
        return

    balance -= cost

    if s in portfolio:
        old_qty = portfolio[s]["qty"]
        old_price = portfolio[s]["buy"]

        new_avg = ((old_qty * old_price) + (q * stocks[s])) / (old_qty + q)
        portfolio[s]["qty"] += q
        portfolio[s]["buy"] = round(new_avg, 2)
    else:
        portfolio[s] = {"qty": q, "buy": stocks[s]}

    pred = predict(s)
    if pred > stocks[s]:
        print(GREEN + f"Prediction: {s} likely to rise next cycle." + RESET)
        pending_boosts[s] = pending_boosts.get(s, 0) + random.randint(8, 16)

    elif pred < stocks[s]:
        print(RED + f"Prediction: {s} may fall slightly next cycle." + RESET)

    else:
        print(YELLOW + f"Prediction: {s} expected to stay stable." + RESET)

    print(GREEN + f"Bought {q} of {s}" + RESET)

# ============================
# SELL
# ============================
def sell():
    global balance
    if not portfolio:
        print("No holdings.")
        return

    s = input("Stock: ").upper()
    if s not in portfolio:
        print("Not owned.")
        return

    q = input("Qty: ")
    if not q.isdigit():
        print("Invalid.")
        return

    q = int(q)
    if q > portfolio[s]["qty"]:
        print("Not enough shares.")
        return

    amount = q * stocks[s]
    balance += amount
    portfolio[s]["qty"] -= q

    if portfolio[s]["qty"] == 0:
        del portfolio[s]

    print(GREEN + f"Sold {q} of {s}" + RESET)

# ============================
# PORTFOLIO
# ============================
def show_portfolio():
    print("\n--- PORTFOLIO ---")
    print(f"Balance: ${round(balance, 2)}\n")

    if not portfolio:
        print("No holdings.")
        return

    for s, d in portfolio.items():
        qty = d["qty"]
        buy = d["buy"]
        now = stocks[s]

        invested = qty * buy
        curr = qty * now
        prof = curr - invested

        col = GREEN if prof >= 0 else RED

        print(f"{s}: {qty} shares")
        print(f" Buy: {buy}")
        print(f" Current: {now}")
        print(col + f" P/L: {round(prof, 2)}" + RESET)
        print()

# ============================
# CANDLECHART
# ============================
def plot_candle(s):
    if plt is None:
        print("Install matplotlib.")
        return

    data = ohlc_history[s][-40:]
    xs = list(range(len(data)))

    fig, ax = plt.subplots(figsize=(10, 5))

    for i, (o, h, l, c) in enumerate(data):
        col = "#4caf50" if c >= o else "#f44336"
        ax.vlines(i, l, h, color="black")
        ax.add_patch(Rectangle((i - 0.3, min(o, c)), 0.6, abs(c - o),
                               facecolor=col, edgecolor="black"))

    ax.set_title(f"{s} Candlestick Chart")
    ax.grid(True)
    plt.show()

# ============================
# MAIN LOOP
# ============================
def main():
    while True:
        print("\n1. View Market")
        print("2. Buy")
        print("3. Sell")
        print("4. Portfolio")
        print("5. Candlestick Chart")
        print("6. Exit")

        ch = input("Choice: ")

        if ch == "1":
            show_market()
        elif ch == "2":
            buy()
        elif ch == "3":
            sell()
        elif ch == "4":
            show_portfolio()
        elif ch == "5":
            s = input("Stock: ").upper()
            if s in stocks:
                plot_candle(s)
        elif ch == "6":
            print("Exiting...")
            break
        else:
            print("Invalid choice.")

main()
