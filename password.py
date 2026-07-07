import subprocess

# Retrieve the list of saved Wi-Fi profiles
profiles = subprocess.check_output(
    "netsh wlan show profiles", shell=True
).decode()

# Parse the network names from the command output
names = [
    line.split(":")[1].strip()
    for line in profiles.split("\n")
    if "All User Profile" in line
]

# Display the Wi-Fi networks in a numbered list
for i, n in enumerate(names, 1):
    print(f"[{i}] {n}")

# Get the user's choice
ch = int(input("\nChoose WiFi number: "))
wifi = names[ch - 1]

# Retrieve and print the details (including the password) for the chosen network
result = subprocess.check_output(
    f'netsh wlan show profile "{wifi}" key=clear', shell=True
).decode()

print("\n" + result)