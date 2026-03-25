class TernaryComputer:
    def __init__(self):
        # Maps for balanced ternary values
        self.val_to_char = {-1: 'i', 0: '0', 1: '1'}
        self.char_to_val = {'i': -1, '0': 0, '1': 1}

    def decimal_to_balanced(self, n):
        """Converts a decimal integer to a balanced ternary string."""
        if n == 0: return "0"
        res = ""
        while n != 0:
            remainder = n % 3
            if remainder == 2:
                res = "i" + res
                n = (n // 3) + 1
            elif remainder == 1:
                res = "1" + res
                n //= 3
            else:
                res = "0" + res
                n //= 3
        return res

    def trit_add(self, a, b, carry_in):
        """Simulates a Full Trit Adder logic."""
        s_sum = a + b + carry_in
        
        # Logic to determine the sum trit and the carry trit
        if s_sum > 1:
            return s_sum - 3, 1
        elif s_sum < -1:
            return s_sum + 3, -1
        else:
            return s_sum, 0

    def add_ternary(self, term1, term2):
        """Adds two balanced ternary strings."""
        # Pad strings to equal length
        max_len = max(len(term1), len(term2))
        t1 = term1.rjust(max_len, '0')
        t2 = term2.rjust(max_len, '0')
        
        result = ""
        carry = 0
        
        # Add from right to left
        for i in range(max_len - 1, -1, -1):
            v1 = self.char_to_val[t1[i]]
            v2 = self.char_to_val[t2[i]]
            
            res_val, carry = self.trit_add(v1, v2, carry)
            result = self.val_to_char[res_val] + result
            
        if carry != 0:
            result = self.val_to_char[carry] + result
            
        return result

# --- Execution ---
cpu = TernaryComputer()

# Example: 5 + 8
# 5 in balanced ternary is 1ii (9 - 3 - 1)
# 8 in balanced ternary is 10i (9 + 0 - 1)
a_dec, b_dec = 5, 8
a_tern = cpu.decimal_to_balanced(a_dec)
b_tern = cpu.decimal_to_balanced(b_dec)

sum_tern = cpu.add_ternary(a_tern, b_tern)

print(f"Decimal: {a_dec} + {b_dec} = {a_dec + b_dec}")
print(f"Ternary: {a_tern} + {b_tern} = {sum_tern}")