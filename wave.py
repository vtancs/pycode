import pygame
import numpy as np

def safe_exp(x, max_val=80.0):
    """Prevents overflow/underflow in nested exponent calculations."""
    return np.exp(np.clip(x, -max_val, max_val))

def generate_sea_wave():
    width, height = 2000, 1200
    m = np.arange(1, width + 1, dtype=np.float64)
    n = np.arange(1, height + 1, dtype=np.float64)
    
    X_grid, Y_grid = np.meshgrid((m - 1400.0) / 1000.0, (801.0 - n) / 1000.0)
    x = X_grid
    y = Y_grid

    def F(val):
        term1 = 255.0 * safe_exp(-safe_exp(-1000.0 * val))
        exponent = safe_exp(-safe_exp(1000.0 * (val - 1.0)))
        return np.abs(term1 * (np.abs(val) ** exponent))

    def P_s(y, s):
        return y - (50.0 - s) / 700.0 + (1.0 / 50.0) * np.cos(7.0 * s)

    def Q_s(x, s):
        return x + 7.0 / 10.0 - (50.0 - s) / 75.0 + (1.0 / 50.0) * np.cos(5.0 * s)

    def K_s(x, y, s):
        ps = P_s(y, s)
        qs = Q_s(x, s)
        return np.arctan(1000.0 * ps / (1.0 + 1000.0 * np.abs(qs)))

    def N_vs(x, y, v, s):
        term_angle1 = (15.0 - 3.0 * v) * (10.0 ** (-s)) * (1.0 + 3.0 * np.cos(10.0 * s))
        cos_2s2_x = np.cos(2.0 * (s**2)) * x
        sin_2s2_y = np.sin(2.0 * (s**2)) * y
        term_angle2 = 6.0 * np.cos((420.0 - 84.0 * v) * (250.0 ** (-s)))
        cos_7s2_x = np.cos(7.0 * (s**2)) * x
        sin_7s2_y = np.sin(7.0 * (s**2)) * y
        cos_5s = np.cos(5.0 * s)

        arg_x = term_angle1 * (cos_2s2_x + sin_2s2_y) + term_angle2 * (cos_7s2_x + sin_7s2_y) + 2.0 * cos_5s
        arg_y = term_angle1 * (cos_2s2_x - sin_2s2_y) + term_angle2 * (cos_7s2_x + sin_7s2_y) + 2.0 * cos_5s

        return np.cos(arg_x) * np.cos(arg_y)

    def E_v(x, y, v):
        sum_ev = np.zeros_like(x)
        for s in range(1, 18):
            coeff = (3.0 + 57.0 * v) / 200.0
            base = (23.0 / 20.0 - v / 10.0) ** (-s)
            sum_ev += coeff * base * N_vs(x, y, v, s)
        return sum_ev

    E0 = E_v(x, y, 0)
    E1 = E_v(x, y, 1)

    def U_s(x, y, s):
        return P_s(y, s) - Q_s(x, s) / 2.0

    def V_s(x, y, s):
        return Q_s(x, s) + P_s(y, s) / 2.0

    def C_s(x, y, s):
        us = U_s(x, y, s)
        vs = V_s(x, y, s)
        term1 = (3.0 + s / 50.0) * (np.abs(us) ** (4.0 + (7.0 + s) / 300.0 * vs))
        term2 = ((90.0 + s) / 200.0) * (vs ** 2)
        return term1 + term2

    def R_v(x, y, v):
        exp_term = E0 if v == 0 else E1
        exponent = - (np.abs(y - 9.0/10.0 + (1.0/3.0)*(x - 1.0/2.0)**2) - 1.0/4.0 + (53.0/10.0)*exp_term)
        return safe_exp(-safe_exp(exponent))

    def J_s(x, y, s):
        cs = C_s(x, y, s)
        ks = K_s(x, y, s)
        us = U_s(x, y, s)
        ps = P_s(y, s)

        inner1 = (17.0 + 4.0 * np.cos(4.0 * s)) * ks + 2.0 * np.cos(16.0 * s)
        inner2 = (25.0 + 6.0 * np.cos(10.0 * s)) * ks + 2.0 * np.cos(19.0 * s)
        exponent1 = - (s + 0.5)**2 - np.abs(400.0 * cs + 2.0 * np.cos(inner1) + 2.0 * np.cos(inner2) - 560.0 + 8.0 * s) - 40.0
        
        term_A = safe_exp(-safe_exp(-5000.0 * (s + 0.5)**19)) * safe_exp(-safe_exp(exponent1))

        exponent2 = - (x + 8.0/5.0 - (1.0/2.0)*( (50.0 - s)/75.0 )**2 + ps * (50.0 - s)/50.0)
        term_B = 1.0 - safe_exp(-safe_exp(500.0 * exponent2)) * safe_exp(-safe_exp(500.0 * us))

        return term_A * term_B

    def T_s(x, y, s):
        ks = K_s(x, y, s)
        return np.cos((12.0 + 4.0 * np.cos(4.0 * s)) * ks + 2.0 * np.cos(6.0 * s))

    def W_s(x, y, s):
        ks = K_s(x, y, s)
        return np.cos((14.0 + 5.0 * np.cos(5.0 * s)) * ks + 2.0 * np.cos(16.0 * s))

    # Calculate L_v(x, y)
    def L_v(x, y, v):
        total_sum = np.zeros_like(x)
        for s in range(-9, 51):
            prod_u = np.ones_like(x)
            for u in range(-10, s):
                prod_u *= (1.0 - J_s(x, y, u))
                
            js = J_s(x, y, s)
            cs = C_s(x, y, s)
            ts = T_s(x, y, s)
            ws = W_s(x, y, s)

            mid_term = (9.0 / 20.0 + ((13.0 - 3.0 * (v - 1.0)**2) / 2000.0) * s + (1.0 / 10.0) * np.cos(s**2))
            cos1 = np.cos((127.0 + 30.0 * np.cos(s)) * cs)
            cos2 = np.cos((92.0 + 20.0 * np.cos(3.0 * s)) * cs)

            term = prod_u * js * (mid_term) * (1.0 + (2.0 / 5.0) * cos1 * ts * ws + (1.0 / 5.0) * cos2 * ws)
            total_sum += term

        return total_sum

    L0 = L_v(x, y, 0)
    L1 = L_v(x, y, 1)
    L2 = L_v(x, y, 2)

    R0 = R_v(x, y, 0)
    R1 = R_v(x, y, 1)

    prod_s = np.ones_like(x)
    for s in range(-9, 51):
        prod_s *= (1.0 - J_s(x, y, s))

    def H_v(L_v_val, v):
        part1 = (v**2 + v + 14.0) / 20.0 + ((3.0 * v**2 - 3.0 * v + 16.0) / 20.0) * (1.0 + y / 10.0) * prod_s
        part2 = (1.0 - R0) + R0 * (1.0 - (3.0 / 10.0) * R1 - (3.0 / 10.0) * E0) * (y / 10.0 + 91.0 / 100.0 + (1.0 / 30.0) * (x - 0.5)**2)
        return L_v_val * part1 * part2

    H0 = H_v(L0, 0)
    H1 = H_v(L1, 1)
    H2 = H_v(L2, 2)

    R_channel = F(H0)
    G_channel = F(H1)
    B_channel = F(H2)

    rgb_image = np.stack([R_channel, G_channel, B_channel], axis=-1)
    rgb_image = np.clip(rgb_image, 0, 255).astype(np.uint8)
    
    return np.transpose(rgb_image, (1, 0, 2))

def main():
    pygame.init()
    width, height = 2000, 1200
    screen = pygame.display.set_mode((width, height))
    pygame.display.set_caption("Sea Wave by Hamid Naderi Yeganeh")

    print("Rendering wave equations...")
    pixel_array = generate_sea_wave()
    surface = pygame.surfarray.make_surface(pixel_array)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        screen.blit(surface, (0, 0))
        pygame.display.flip()

    pygame.quit()

if __name__ == "__main__":
    main()