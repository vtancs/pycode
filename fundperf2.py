import matplotlib.pyplot as plt

def calculate_fees(investment, total_return_pct, hurdle_rate, perf_fee_rate, mgmt_fee_rate):
    """
    Calculate investor and manager results given all fee parameters.
    Returns a dictionary of results.
    """
    total_return = total_return_pct / 100
    hurdle = hurdle_rate / 100
    perf_fee = perf_fee_rate / 100
    mgmt_fee = mgmt_fee_rate / 100

    # Step 1: Deduct management fee first (reduces net performance)
    mgmt_fee_amount = investment * mgmt_fee
    gross_profit = investment * total_return
    net_profit_before_perf = gross_profit - mgmt_fee_amount

    # Step 2: Apply performance fee logic
    if total_return <= hurdle:
        # Below hurdle
        investor_profit = net_profit_before_perf
        manager_perf_fee = 0
        phase = "Below Hurdle"
    elif total_return <= hurdle * (1 + perf_fee):
        # Catch-up phase
        total_profit = net_profit_before_perf
        manager_target = total_profit * perf_fee
        investor_profit = total_profit - manager_target
        manager_perf_fee = manager_target
        phase = "Catch-up Phase"
    else:
        # Above catch-up
        total_profit = net_profit_before_perf
        profit_above_hurdle = total_profit - (investment * hurdle)
        manager_perf_fee = profit_above_hurdle * perf_fee
        investor_profit = total_profit - manager_perf_fee
        phase = "Above Hurdle + Catch-up"

    # Step 3: Summarize results
    investor_total = investment + investor_profit
    total_fees = mgmt_fee_amount + manager_perf_fee
    eff_fee_pct = (total_fees / gross_profit * 100) if gross_profit > 0 else 0

    return {
        "phase": phase,
        "investor_profit": investor_profit,
        "manager_perf_fee": manager_perf_fee,
        "mgmt_fee": mgmt_fee_amount,
        "investor_total": investor_total,
        "total_fees": total_fees,
        "eff_fee_pct": eff_fee_pct,
        "total_return_pct": total_return_pct
    }


def show_results(result):
    """Display results clearly."""
    print(f"\n--- {result['phase']} ---")
    print(f"Total Fund Return: {result['total_return_pct']:.2f}%")
    print(f"Management Fee: SGD {result['mgmt_fee']:,.2f}")
    print(f"Performance Fee: SGD {result['manager_perf_fee']:,.2f}")
    print(f"Total Fees: SGD {result['total_fees']:,.2f}")
    print(f"Investor Profit (net): SGD {result['investor_profit']:,.2f}")
    print(f"Investor Total Value: SGD {result['investor_total']:,.2f}")
    print(f"Effective Fee (% of profit): {result['eff_fee_pct']:.2f}%\n")


def single_scenario():
    investment = float(input("Enter investor's capital (e.g. 1000000): "))
    total_return = float(input("Enter total fund return (%) (e.g. 12): "))
    hurdle_rate = float(input("Enter hurdle rate (%) (e.g. 6): "))
    perf_fee = float(input("Enter performance fee rate (%) (e.g. 15): "))
    mgmt_fee = float(input("Enter annual management fee (%) (e.g. 2): "))

    result = calculate_fees(investment, total_return, hurdle_rate, perf_fee, mgmt_fee)
    show_results(result)


def compare_scenarios():
    investment = float(input("Enter investor's capital (e.g. 1000000): "))
    hurdle_rate = float(input("Enter hurdle rate (%) (e.g. 6): "))
    perf_fee = float(input("Enter performance fee rate (%) (e.g. 15): "))
    mgmt_fee = float(input("Enter annual management fee (%) (e.g. 2): "))
    returns = input("Enter return scenarios separated by commas (e.g. 5,8,12,15): ")
    returns = [float(x.strip()) for x in returns.split(",")]

    investor_profits, manager_perf_fees, mgmt_fees = [], [], []

    print("\n=== Scenario Comparison ===")
    print(f"{'Return %':>10} | {'Phase':>22} | {'Mgmt Fee (SGD)':>15} | {'Perf Fee (SGD)':>15} | {'Investor Profit (SGD)':>22} | {'Eff. Fee %':>10}")
    print("-" * 105)

    for r in returns:
        res = calculate_fees(investment, r, hurdle_rate, perf_fee, mgmt_fee)
        investor_profits.append(res["investor_profit"])
        manager_perf_fees.append(res["manager_perf_fee"])
        mgmt_fees.append(res["mgmt_fee"])
        print(f"{r:10.2f} | {res['phase']:>22} | {res['mgmt_fee']:>15,.2f} | {res['manager_perf_fee']:>15,.2f} | {res['investor_profit']:>22,.2f} | {res['eff_fee_pct']:>10.2f}")

    # Optional visualization
    show_chart = input("\nWould you like to see a chart of results? (y/n): ").strip().lower()
    if show_chart == "y":
        plt.figure(figsize=(8, 5))
        plt.plot(returns, investor_profits, label="Investor Profit (net)", linewidth=2)
        plt.plot(returns, manager_perf_fees, label="Performance Fee", linewidth=2)
        plt.plot(returns, mgmt_fees, label="Management Fee", linewidth=2)
        plt.axvline(hurdle_rate, color="gray", linestyle="--", label=f"Hurdle {hurdle_rate}%")
        plt.title("Investor & Manager Outcomes by Fund Return")
        plt.xlabel("Total Fund Return (%)")
        plt.ylabel("Amount (SGD)")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()


def main():
    print("=== Fund Fee Analysis Tool (with Management Fee) ===\n")

    while True:
        print("\nMenu Options:")
        print("1. Calculate single scenario")
        print("2. Compare multiple return scenarios")
        print("3. Exit")

        choice = input("\nEnter your choice (1/2/3): ").strip()

        if choice == "1":
            single_scenario()
        elif choice == "2":
            compare_scenarios()
        elif choice == "3":
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()
