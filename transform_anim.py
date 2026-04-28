import pygame
import math
import random

# Constants from original logic
UU = 80       
K, M = 0.866, 0.866
N, S = 0.5, -0.5

# Visual Style
BLACK = (0, 0, 0)
BORDER_PADDING = 30 

def project(x, y, z):
    """Isometric Projection Math"""
    c = x * K + y * M
    d = x * N + y * S - z
    return c, d

def run_simulation():
    pygame.init()
    
    # Window size (896x504)
    WIDTH, HEIGHT = 896, 504
    screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)
    pygame.display.set_caption("Spring Coil - [Space] Change Color, [Esc] Quit")
    
    clock = pygame.time.Clock()
    
    # State variables
    running = True
    frame = 0
    wire_color = (51, 255, 51) # Starting Retro Green
    
    while running:
        W, H = screen.get_size()
        screen.fill(BLACK)
        
        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                
                if event.key == pygame.K_SPACE:
                    # Generate a random bright color
                    wire_color = (random.randint(50, 255), 
                                  random.randint(50, 255), 
                                  random.randint(50, 255))
        
        # Base scale 
        full_fit_scale = (H - (BORDER_PADDING * 2)) / 160
        scale = full_fit_scale * 0.25 
        
        for j in range(3):
            # Staggered Sine Wave for Spring Motion
            offset_stretch = 1.5 + math.sin((frame + j * 20) * 0.05) * 1.0
            
            v_off = (W / 4) * (j + 1)
            u_off = H / 2 
            
            for i in range(0, 111, 10):
                z_dyn = i * offset_stretch
                w_dyn = i * offset_stretch
                
                x, y = 0, 0
                c, d = project(x, y, z_dyn)
                
                data = [
                    (0, UU, w_dyn),
                    (UU, UU, None), 
                    (UU, 0, None),
                    (0, 0, None)
                ]
                
                curr_c, curr_d = c, d
                
                for dx, dy, dz in data:
                    target_z = z_dyn if dz is None else dz
                    x, y, z_dyn = dx, dy, target_z
                    
                    next_c, next_d = project(x, y, z_dyn)
                    
                    # Centering adjustments with dynamic Z
                    start_pos = (
                        v_off + (curr_c - UU * 0.866) * scale, 
                        u_off - (curr_d + (UU * 0.4 * offset_stretch)) * scale
                    )
                    end_pos = (
                        v_off + (next_c - UU * 0.866) * scale, 
                        u_off - (next_d + (UU * 0.4 * offset_stretch)) * scale
                    )
                    
                    pygame.draw.line(screen, wire_color, start_pos, end_pos, 1)
                    curr_c, curr_d = next_c, next_d

        pygame.display.flip()
        frame += 1
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    run_simulation()