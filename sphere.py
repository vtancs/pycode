import pygame
import math

# --- Configuration & Initialization ---
pygame.init()

# Constants derived from source
WIDTH, HEIGHT = 640, 400
R = 190
N1 = 12
N2 = 24
PI = math.pi
DA1 = PI / N1
DA2 = 2 * PI / N2
ASPX = (640 / 200) * (3 / 4) #

ROT2 = -PI / 4 #
ROT2COS = math.cos(ROT2)
ROT2SIN = math.sin(ROT2)

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("3D Sphere - Fast Rotation")
clock = pygame.time.Clock()
font = pygame.font.SysFont("Courier", 18)

def draw_sphere(rotation_offset):
    screen.fill((0, 0, 0)) # CLS
    
    # Text labels
    title = font.render("3D Sphere with hidden line removal", True, (0, 255, 0))
    screen.blit(title, (50, 20))
    quit_text = font.render("Press ESC to Quit", True, (200, 200, 200))
    screen.blit(quit_text, (50, 45))

    # Outer Circle boundary
    pygame.draw.circle(screen, (0, 255, 0), (320, 200), R, 1)

    last_meridian_points = [None] * (N1 + 1)

    for i2 in range(N2 + 1):
        A2 = i2 * DA2 #
        current_meridian_points = []
        
        for i1 in range(N1 + 1):
            A1 = i1 * DA1 #
            
            # Math logic from lines 150-190
            y = R * math.sin(A1) * math.sin(A2 + rotation_offset)
            z = R * math.cos(A1)
            x = R * math.sin(A1) * math.cos(A2 + rotation_offset)
            
            zr = (ROT2COS * z - ROT2SIN * y) / ASPX
            yr = ROT2SIN * z + ROT2COS * y
            
            screen_x = int(320 + x)
            screen_y = int(200 + zr)
            
            # Back-face culling logic
            is_visible = yr >= -R / 10
            
            if is_visible:
                # Vertical lines
                if i1 > 0 and prev_visible:
                    pygame.draw.line(screen, (0, 255, 0), (prev_x, prev_y), (screen_x, screen_y), 1)
                
                # Horizontal lines
                if last_meridian_points[i1] is not None:
                    old_x, old_y = last_meridian_points[i1]
                    pygame.draw.line(screen, (0, 255, 0), (old_x, old_y), (screen_x, screen_y), 1)

            current_meridian_points.append((screen_x, screen_y))
            prev_x, prev_y = screen_x, screen_y
            prev_visible = is_visible
            
        last_meridian_points = current_meridian_points

# --- Main Loop ---
running = True
angle_offset = 0

while running:
    # 1. Handle Keypresses (including ESC to Quit)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE: # Replaces InKey$ logic
                running = False

    # 2. Increase spinning speed
    # We now increment the angle continuously instead of in 4 chunky steps
    angle_offset += 0.05 
    
    # 3. Draw and Update
    draw_sphere(angle_offset)
    pygame.display.flip()
    
    # 4. Control Framerate (60 FPS for smooth motion)
    clock.tick(60) 

pygame.quit()