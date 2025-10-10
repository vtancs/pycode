import pandas as pd


def calculate_apr_from_monthly(P, A, n, tol=1e-8, max_iter=1000):
    """
    Calculate Annual Percentage Rate (APR) using monthly payment formula.

    :param P: Loan principal
    :param A: Monthly payment
    :param n: Number of monthly payments
    :param tol: Convergence tolerance
    :param max_iter: Max iterations
    :return: Monthly interest rate and Annual Percentage Rate (APR) in %
    """
    # Handle zero-interest case directly
    if abs(A * n - P) < tol:
        return 0.0, 0.0

    low, high = 0.0, 1.0  # search between 0% and 100% monthly interest
    r = 0.0

    for _ in range(max_iter):
        r = (low + high) / 2
        denom = ((1 + r) ** n - 1)
        if denom == 0:
            denom = 1e-12
        estimated_payment = P * r * (1 + r) ** n / denom

        if abs(estimated_payment - A) < tol:
            break
        if estimated_payment > A:
            high = r
        else:
            low = r

    apr = r * 12 * 100
    return r, apr


def generate_amortization_schedule(P, A, r, n):
    """
    Generate amortization schedule for a loan.

    :param P: Loan principal
    :param A: Monthly payment
    :param r: Monthly interest rate
    :param n: Number of payments
    :return: List of dictionaries with payment details
    """
    schedule = []
    balance = P

    for month in range(1, n + 1):
        interest = balance * r
        principal = A - interest
        balance -= principal
        balance = max(balance, 0)
        schedule.append({
            "Month": month,
            "Payment": round(A, 2),
            "Interest": round(interest, 2),
            "Principal": round(principal, 2),
            "Remaining Balance": round(balance, 2)
        })
    return schedule


def display_schedule(schedule):
    print("\nAmortization Schedule")
    print("-" * 70)
    print(f"{'Month':<6}{'Payment':>12}{'Interest':>12}{'Principal':>12}{'Balance':>15}")
    print("-" * 70)
    for row in schedule:
        print(f"{row['Month']:<6}{row['Payment']:>12.2f}{row['Interest']:>12.2f}{row['Principal']:>12.2f}{row['Remaining Balance']:>15.2f}")


def export_schedule(schedule, filename_base="loan_schedule"):
    """
    Export amortization schedule to Excel and CSV.

    :param schedule: List of dicts
    :param filename_base: Base filename (without extension)
    """
    df = pd.DataFrame(schedule)
    excel_file = f"{filename_base}.xlsx"
    csv_file = f"{filename_base}.csv"

    df.to_excel(excel_file, index=False, engine="openpyxl")
    df.to_csv(csv_file, index=False)

    print(f"\n✅ Schedule exported to:\n  - {excel_file}\n  - {csv_file}")


# Main program
if __name__ == "__main__":
    P = float(input("Enter the loan amount (principal): "))
    A = float(input("Enter the monthly payment: "))
    n = int(input("Enter the number of monthly payments: "))

    monthly_rate, apr = calculate_apr_from_monthly(P, A, n)
    print(f"\nThe Annual Percentage Rate (APR) is: {apr:.2f}%")

    schedule = generate_amortization_schedule(P, A, monthly_rate, n)
    display_schedule(schedule)
    export_schedule(schedule)
