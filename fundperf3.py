import matplotlib.pyplot as plt
import pandas as pd

def calculate_fees(investment, total_return_pct, hurdle_rate, perf_fee_rate, mgmt_fee_rate):
    """
    Calculate investor and manager results given all fee parameters.
    Returns a dictionary of results.
    """
    total_return = total_return_pct / 100
    hurdle = hurdle_rate / 100
    perf_fee = perf_fee_rate / 100
    mgmt_fee = mgmt_fee_rate / 100

    # Step 1: Management fee
    mgmt_fee_amount = investment * mgmt_fee
    gross_profit = investment * total_return
    net_profit_before_perf = gross_profit - mgmt_fee_amount

    # Step 2: Apply performance fee logic
    if total_return <= hurdle:
        # Below hurdle
        manager_perf_fee = 0
        investor_profit = net_profit_before_perf
        phase = "Below Hurdle"
    elif total_return <= hurdle * (1 + perf_fee):
        # Catch-up phase
        total_profit = net_profit_before_perf
        manager_perf_fee = total_profit * perf_fee
        investor_profit = total_profit - manager_perf_fee
        phase = "Catch-up Phase"
    else:
        # Above catch-up
        total_profit = net_profit_before_perf
        profit_above_hurdle = total_profit - (investment * hurdle)
        manager_perf_fee = profit_above_hurdle * perf_fee
        investor_profit = total_profit - manager_perf_fee
        phase = "Above Hurdle + Catch-up"

    # Step 3: Results
    investor_total = investment + investor_profit
    total_fees = mgmt_fee_amount + manager_perf_fee
    eff_fee_pct = (total_fees / gross_profit * 100) if gross_profit > 0 else 0

    # Waterfall data
    waterfall = [
        {"Stage": "Initial Capital", "Amount (SGD)": investment},
        {"Stage": "Gross Return", "Amount (SGD)": investment + gross_profit},
        {"Stage": "Less: Management Fee", "Amount (SGD)": -mgmt_fee_amount},
        {"Stage": "Less: Performance Fee", "Amount (SGD)": -manager_perf_fee},
        {"Stage": "Investor Final Value", "Amount (SGD)": investor_total},
    ]

    return {
        "Return %": total_return_pct,
        "Phase": phase,
        "Mgmt Fee (SGD)": round(mgmt_fee_amount, 2),
        "Perf Fee (SGD)": round(manager_perf_fee, 2),
        "Total Fees (SGD)": round(total_fees, 2),
        "Investor Profit (SGD)": round(investor_profit, 2),
        "Investor Total (SGD)": round(investor_total, 2),
        "Effective Fee %": round(eff_fee_pct, 2),
        "Waterfall": waterfall
    }


def compare_scenarios():
    investment = float(input("Enter investor's capital (e.g. 1000000): "))
    hurdle_rate = float(input("Enter hurdle rate (%) (e.g. 6): "))
    perf_fee = float(input("Enter performance fee rate (%) (e.g. 15): "))
    mgmt_fee = float(input("Enter annual management fee (%) (e.g. 2): "))
    returns = input("Enter return scenarios separated by commas (e.g. 5,8,12,15): ")
    returns = [float(x.strip()) for x in returns.split(",")]

    results = [calculate_fees(investment, r, hurdle_rate, perf_fee, mgmt_fee) for r in returns]
    df_summary = pd.DataFrame([{k: v for k, v in r.items() if k != "Waterfall"} for r in results])

    print("\n=== Scenario Summary ===")
    print(df_summary.to_string(index=False))

    # Export to Excel with waterfall
    export_choice = input("\nExport results with waterfall breakdown to Excel? (y/n): ").strip().lower()
    if export_choice == "y":
        filename = input("Enter Excel file name (without extension): ").strip() + ".xlsx"
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            df_summary.to_excel(writer, index=False, sheet_name="Summary")

            # Add waterfall sheets per scenario
            for r in results:
                sheet_name = f"{r['Return %']}%"
                df_wf = pd.DataFrame(r["Waterfall"])
                df_wf.to_excel(writer, index=False, sheet_name=sheet_name)

        print(f"\n✅ Exported successfully to {filename}")
        print("Sheets included: Summary + one for each return scenario.")

    # Optional visualization
    show_chart = input("\nWould you like to see a chart of results? (y/n): ").strip().lower()
    if show_chart == "y":
        plt.figure(figsize=(8, 5))
        plt.plot(df_summary["Return %"], df_summary["Investor Profit (SGD)"], label="Investor Profit (net)", linewidth=2)
        plt.plot(df_summary["Return %"], df_summary["Perf Fee (SGD)"], label="Performance Fee", linewidth=2)
        plt.plot(df_summary["Return %"], df_summary["Mgmt Fee (SGD)"], label="Management Fee", linewidth=2)
        plt.axvline(hurdle_rate, color="gray", linestyle="--", label=f"Hurdle {hurdle_rate}%")
        plt.title("Investor & Manager Outcomes by Fund Return")
        plt.xlabel("Total Fund Return (%)")
        plt.ylabel("Amount (SGD)")
        plt.legend()
        plt.grid(True, linestyle="--", alpha=0.7)
        plt.tight_layout()
        plt.show()


def main():
    print("=== Fund Fee Analysis Tool (with Excel Waterfall Export) ===\n")

    while True:
        print("\nMenu Options:")
        print("1. Compare multiple return scenarios and export")
        print("2. Exit")

        choice = input("\nEnter your choice (1/2): ").strip()

        if choice == "1":
            compare_scenarios()
        elif choice == "2":
            print("\nGoodbye!")
            break
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()
