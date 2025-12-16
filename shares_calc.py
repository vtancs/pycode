# Number of shares and prices
shares1 = 1000
price1 = 15.04

shares2 = 1000
price2 = 13.66

# Total shares
total_shares = shares1 + shares2

# Total cost
total_cost = (shares1 * price1) + (shares2 * price2)

# Average cost per share
average_cost = total_cost / total_shares

print(f"Total shares: {total_shares}")
print(f"Total cost: ${total_cost:.2f}")
print(f"Average cost per share: ${average_cost:.2f}")
