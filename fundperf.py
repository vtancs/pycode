def calculate_fund_fees():
    print("=== Fund Performance Fee Calculator ===\n")

    # --- User Inputs ---
    investment = float(input("Enter investor's capital (e.g., 1000000): "))
    total_return_pct = float(input("Enter total fund return (%) (e.g., 12): ")) / 100
    hurdle_rate = float(input("Enter hurdle rate (%) (e.g., 6): ")) / 100
    perf_fee_rate = float(input("Enter performance fee rate (%) (e.g., 15): ")) / 100

    # --- Step 1: Below Hurdle ---
    if total_return_pct <= hurdle_rate:
        investor_profit = investment * total_return_pct
        manager_fee = 0
        print("\nFund did not exceed hurdle rate.")
    
    # --- Step 2: Catch-up Phase (fund slightly above hurdle) ---
    elif total_return_pct <= hurdle_rate * (1 + perf_fee_rate):
        # Catch-up until manager's total share equals fee rate of total profits
        total_profit = investment * total_return_pct
        manager_target = total_profit * perf_fee_rate
        investor_profit = total_profit - manager_target
        manager_fee = manager_target
        print("\nFund in catch-up phase.")

    # --- Step 3: Beyond Catch-up (normal split 85/15) ---
    else:
        total_profit = investment * total_return_pct
        # Manager gets 15% of profits above the hurdle
        profit_above_hurdle = total_profit - investment * hurdle_rate
        manager_fee = profit_above_hurdle * perf_fee_rate
        investor_profit = total_profit - manager_fee
        print("\nFund exceeded hurdle and catch-up thresholds.")

    # --- Output ---
    investor_total = investment + investor_profit
    manager_total = manager_fee

    print("\n=== Results ===")
    print(f"Investor Profit: SGD {investor_profit:,.2f}")
    print(f"Manager Performance Fee: SGD {manager_fee:,.2f}")
    print(f"Investor Total Value: SGD {investor_total:,.2f}")
    print(f"Total Fund Return: {total_return_pct*100:.2f}%")
    print(f"Effective Manager Fee (% of profit): {manager_fee / (investment * total_return_pct) * 100:.2f}%")

# Run the calculator
if __name__ == "__main__":
    calculate_fund_fees()
