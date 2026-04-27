import pygame
import math

# Constants from original logic
UU = 80       
K, M = 0.866, 0.866
N, S = 0.5, -0.5

# Visual Style
RETRO_GREEN = (51, 255, 51)
BLACK = (0, 0, 0)
BORDER_PADDING = 30 

def project(x, y, z):
    """Isometric Projection Math"""
    c = x * K + y * M
    d = x * N + y * S - z
    return c, d

def run_simulation():
    pygame.init()
    
    # --- PHYSICAL WINDOW REDUCTION ---
    # Reducing 1280x720 by 30%
    # 1280 * 0.7 = 896
    # 720 * 0.7 = 504
    WIDTH, HEIGHT = 896, 504
    
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Retro Wireframe - 30% Smaller Window")
    
    clock = pygame.time.Clock()
    
    running = True
    while running:
        W, H = screen.get_size()
        screen.fill(BLACK)
        
        # Calculate scale based on the current window height
        # Keeping the 75% reduction logic from the previous step
        full_fit_scale = (H - (BORDER_PADDING * 2)) / 160
        scale = full_fit_scale * 0.25 
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Distribute 3 cubes across the smaller window
        for j in range(3):
            v_off = (W / 4) * (j + 1)
            u_off = H / 2 
            
            for i in range(0, 111, 10):
                z, x, y, w = i, 0, 0, i
                c, d = project(x, y, z)
                
                data = [
                    (0, UU, w),
                    (UU, UU, None), 
                    (UU, 0, None),
                    (0, 0, None)
                ]
                
                curr_c, curr_d = c, d
                
                for dx, dy, dz in data:
                    target_z = z if dz is None else dz
                    x, y, z = dx, dy, target_z
                    
                    next_c, next_d = project(x, y, z)
                    
                    # Screen Space Mapping
                    start_pos = (
                        v_off + (curr_c - UU * 0.866) * scale, 
                        u_off - (curr_d + UU * 0.4) * scale
                    )
                    end_pos = (
                        v_off + (next_c - UU * 0.866) * scale, 
                        u_off - (next_d + UU * 0.4) * scale
                    )
                    
                    pygame.draw.line(screen, RETRO_GREEN, start_pos, end_pos, 1)
                    curr_c, curr_d = next_c, next_d

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()