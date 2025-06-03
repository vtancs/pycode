import math

# Constants
EFFICIENCY = 0.9                         # Discharge coefficient
DIAMETER_M = 0.00635                     # Hose diameter in meters
AREA = math.pi / 4 * DIAMETER_M ** 2     # Cross-sectional area of hose
P0_PSI = 800
P0_PA = P0_PSI * 6894.76                # Upstream pressure in Pascals
T0_K = 25 + 273.15                      # Room temperature in Kelvin
GAMMA = 1.3                             # Heat capacity ratio for CO2
R = 188.9                               # Specific gas constant for CO2
CO2_CYLINDER_KG = 23
CYLINDER_COST = 40                      # SGD
FREEZE_TIME_MIN = 20
TOP_UP_INTERVAL_MIN = 15
TOP_UP_AMOUNT_KG = 4.4

def calculate_mass_flow_rate():
    first_part = EFFICIENCY * AREA * P0_PA
    second_part = math.sqrt(GAMMA / (R * T0_K))
    third_part = ((2 / (GAMMA + 1)) ** ((GAMMA + 1) / (GAMMA - 1))) ** 0.5
    mass_flow_rate = first_part * second_part * third_part
    return mass_flow_rate  # in Kg/s

def calculate_total_usage_and_cost():
    mass_flow_rate_kg_s = calculate_mass_flow_rate()
    mass_flow_rate_kg_min = mass_flow_rate_kg_s * 60

    print(f"\nMass flow rate per hose: {mass_flow_rate_kg_min:.2f} Kg/min")

    total_hoses = 2
    total_mass_flow = mass_flow_rate_kg_min * total_hoses

    # Initial injection
    initial_usage = total_mass_flow * FREEZE_TIME_MIN

    # Top-up injections every 15 minutes
    top_up_count = 0
    remaining_co2 = CO2_CYLINDER_KG * 2 - initial_usage
    while remaining_co2 >= TOP_UP_AMOUNT_KG:
        remaining_co2 -= TOP_UP_AMOUNT_KG
        top_up_count += 1

    total_duration_min = FREEZE_TIME_MIN + top_up_count * TOP_UP_INTERVAL_MIN
    total_cost = (2 * CYLINDER_COST)
    
    print(f"Initial CO₂ used: {initial_usage:.2f} Kg")
    print(f"Top-ups possible: {top_up_count}")
    print(f"Total freezing time: {total_duration_min} minutes")
    print(f"Total CO₂ used: {initial_usage + top_up_count * TOP_UP_AMOUNT_KG:.2f} Kg")
    print(f"Total CO₂ cost: SGD {total_cost}")
    print(f"Estimated water saved: 3500L")

if __name__ == "__main__":
    print("Pipe Freezing Cost Calculator")
    calculate_total_usage_and_cost()
