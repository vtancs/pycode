# Initialize totals
total_shares = 0
total_cost = 0

# Ask how many purchases
num_purchases = int(input("Enter number of purchases: "))

for i in range(1, num_purchases + 1):
    shares = float(input(f"Enter number of shares for purchase {i}: "))
    price = float(input(f"Enter price per share for purchase {i}: "))
    
    total_shares += shares
    total_cost += shares * price

# Calculate average cost per share
average_cost = total_cost / total_shares

print("\n--- Summary ---")
print(f"Total shares: {total_shares}")
print(f"Total cost: ${total_cost:.2f}")
print(f"Average cost per share: ${average_cost:.2f}")
