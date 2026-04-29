import pygame
import math
import time

# --- Setup ---
pygame.init()
WIDTH, HEIGHT = 1280, 1024
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Slow Kaleidoscope")
clock = pygame.time.Clock()

# Load texture
try:
    pic = pygame.image.load("butterflies.jpg").convert_alpha()
    pic = pygame.transform.scale(pic, (640, 640))
except:
    # Creating a placeholder texture with patterns if image is missing
    pic = pygame.Surface((640, 640))
    pic.fill((30, 30, 50))
    for i in range(0, 640, 40):
        pygame.draw.line(pic, (200, 100, 0), (i, 0), (640-i, 640), 2)
        pygame.draw.circle(pic, (100, 200, 255), (i, 320), 20, 2)

def get_wedge(source_pic):
    """Clips the texture into a 60-degree slice to prevent overlap."""
    size = source_pic.get_width()
    wedge_surf = pygame.Surface((size, size), pygame.SRCALPHA)
    
    center = (size // 2, size // 2)
    # 60 degree slice points
    p1 = (size // 2 + size * math.cos(math.radians(-30)), 
          size // 2 + size * math.sin(math.radians(-30)))
    p2 = (size // 2 + size * math.cos(math.radians(30)), 
          size // 2 + size * math.sin(math.radians(30)))
    
    pygame.draw.polygon(wedge_surf, (255, 255, 255, 255), [center, p1, p2])
    
    target = source_pic.copy()
    target.blit(wedge_surf, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
    return target

running = True
start_time = time.time()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # --- THE SLOW DOWN ---
    # We reduced the multiplier from 10.0 to 1.5 to chill out the motion
    elapsed_time = (time.time() - start_time) * 1.5 
    
    # Matching the BBC BASIC logic: 2 * PI * SIN(TIME/800)
    # We use a smaller denominator to keep the 'sway' gentle
    a_rad = 2 * math.pi * math.sin(elapsed_time / 4.0) 
    angle_deg = math.degrees(a_rad)

    screen.fill((0, 0, 0))

    # Create the base wedge slice
    # This rotates the source image slowly inside the "viewfinder"
    rotated_pic = pygame.transform.rotate(pic, angle_deg * 0.5) 
    rect = rotated_pic.get_rect(center=(320, 320))
    
    temp_canvas = pygame.Surface((640, 640), pygame.SRCALPHA)
    temp_canvas.blit(rotated_pic, rect)
    
    wedge = get_wedge(temp_canvas)

    # Draw the 6 slices
    for i in range(6):
        rot_angle = i * 60
        
        # Primary slice
        img = pygame.transform.rotate(wedge, rot_angle)
        rect = img.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(img, rect)
        
        # Mirrored slice
        flipped_wedge = pygame.transform.flip(wedge, True, False)
        # Shift the mirrored slice by 30 degrees to close the gap
        img_m = pygame.transform.rotate(flipped_wedge, rot_angle + 30)
        rect_m = img_m.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(img_m, rect_m)

    pygame.display.flip()
    clock.tick(60) # Limits CPU usage

pygame.quit()