import tkinter as tk
from tkinter import ttk

class TernarySystem:
    def __init__(self, root):
        self.root = root
        self.root.title("Ternary Computing Unit v2.0")
        self.root.geometry("600x500")
        
        # State mapping
        self.val_to_char = {-1: 'i', 0: '0', 1: '1'}
        self.char_to_val = {'i': -1, '0': 0, '1': 1}
        self.colors = {-1: "#ff4d4d", 0: "#3d3d3d", 1: "#4dff4d"} # Red, Gray, Green

        self.setup_tabs()

    def setup_tabs(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(expand=True, fill="both")

        # Tab 1: Arithmetic
        self.calc_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.calc_frame, text="Arithmetic Unit")
        self.setup_calc_ui()

        # Tab 2: Logic Gates
        self.logic_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.logic_frame, text="Logic Gate Lab")
        self.setup_logic_ui()

    def setup_calc_ui(self):
        # ... (Similar to previous version but integrated into self.calc_frame)
        container = ttk.Frame(self.calc_frame, padding="20")
        container.pack()
        
        ttk.Label(container, text="A + B Calculator", font=("Arial", 14, "bold")).grid(row=0, columnspan=2, pady=10)
        
        self.ent_a = ttk.Entry(container, width=10); self.ent_a.grid(row=1, column=1)
        ttk.Label(container, text="Decimal A:").grid(row=1, column=0)
        
        self.ent_b = ttk.Entry(container, width=10); self.ent_b.grid(row=2, column=1)
        ttk.Label(container, text="Decimal B:").grid(row=2, column=0)

        ttk.Button(container, text="Compute", command=self.run_add).grid(row=3, columnspan=2, pady=10)

        self.calc_leds = []
        led_row = ttk.Frame(container)
        led_row.grid(row=4, columnspan=2)
        for i in range(8):
            l = tk.Frame(led_row, width=35, height=35, bg="#3d3d3d", relief="raised")
            l.pack(side="left", padx=2)
            self.calc_leds.append(l)

    def setup_logic_ui(self):
        # Logic Lab Controls
        lab = ttk.Frame(self.logic_frame, padding="20")
        lab.pack()

        ttk.Label(lab, text="Ternary Logic Gates", font=("Arial", 14, "bold")).pack(pady=10)

        # Input Selectors
        ctrl_frame = ttk.Frame(lab)
        ctrl_frame.pack(pady=10)

        self.in_a = tk.IntVar(value=0)
        self.in_b = tk.IntVar(value=0)

        for i, val in enumerate([-1, 0, 1]):
            ttk.Radiobutton(ctrl_frame, text=f"In A: {self.val_to_char[val]}", variable=self.in_a, value=val, command=self.update_logic).grid(row=i, column=0, padx=10)
            ttk.Radiobutton(ctrl_frame, text=f"In B: {self.val_to_char[val]}", variable=self.in_b, value=val, command=self.update_logic).grid(row=i, column=1, padx=10)

        # Output LEDs
        out_frame = ttk.Frame(lab)
        out_frame.pack(pady=20)

        self.gates = ["STI (NOT A)", "MIN (AND)", "MAX (OR)"]
        self.gate_leds = {}
        
        for i, g_name in enumerate(self.gates):
            f = ttk.Frame(out_frame)
            f.grid(row=0, column=i, padx=20)
            ttk.Label(f, text=g_name).pack()
            led = tk.Frame(f, width=50, height=50, bg="#3d3d3d", relief="sunken", borderwidth=3)
            led.pack()
            self.gate_leds[g_name] = led

    def update_logic(self):
        a, b = self.in_a.get(), self.in_b.get()
        
        # Gate Logic
        results = {
            "STI (NOT A)": -a,
            "MIN (AND)": min(a, b),
            "MAX (OR)": max(a, b)
        }

        for name, res in results.items():
            self.gate_leds[name].config(bg=self.colors[res])

    def run_add(self):
        # Logic from previous script to convert and light LEDs
        try:
            total = int(self.ent_a.get()) + int(self.ent_b.get())
            res_str = self.decimal_to_balanced(total).rjust(8, '0')[-8:]
            for i, char in enumerate(res_str):
                val = self.char_to_val[char]
                self.calc_leds[i].config(bg=self.colors[val])
        except: pass

    def decimal_to_balanced(self, n):
        if n == 0: return "0"
        res, temp_n = "", abs(n)
        while temp_n != 0:
            rem = temp_n % 3
            if rem == 2: res = "i" + res; temp_n = (temp_n // 3) + 1
            else: res = str(rem) + res; temp_n //= 3
        if n < 0: # Flip trits for negative
            res = res.replace('1', 'temp').replace('0', '0').replace('i', '1').replace('temp', 'i')
        return res

if __name__ == "__main__":
    root = tk.Tk()
    TernarySystem(root)
    root.mainloop()