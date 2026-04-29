import pygame
import math
import time
import random
import sys

# --- Configuration ---
pygame.init()
WIDTH, HEIGHT = 1200, 900 
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Mosaic Kaleidoscope")
clock = pygame.time.Clock()

# Initialize Font for UI
# Use 'None' for default system font, or a specific .ttf file
font = pygame.font.SysFont("Arial", 24, bold=True)

# --- Load/Create Texture ---
try:
    pic = pygame.image.load("butterflies.jpg").convert_alpha()
    pic = pygame.transform.scale(pic, (800, 800))
except:
    pic = pygame.Surface((800, 800))
    for x in range(800):
        c = (int(20 + 200 * (x/800)), int(100 * (1 - x/800)), 150)
        pygame.draw.line(pic, c, (x, 0), (x, 800))

# --- Constants ---
WEDGE_ANGLE = 60
WEDGE_RADIUS = 700 
NUM_TILES_R = 25
NUM_TILES_T = 12
GROUT_COLOR = (10, 10, 15)
GROUT_THICKNESS = 1

class MosaicWedge:
    def __init__(self, size_r, angle):
        self.size_r = size_r
        self.angle = angle
        self.base_surf = pygame.Surface((size_r * 2, size_r * 2), pygame.SRCALPHA)
        self.tiles = self._generate_tessellation()

    def _generate_tessellation(self):
        tiles = []
        cx, cy = self.size_r, self.size_r
        dr = self.size_r / NUM_TILES_R
        for r_step in range(NUM_TILES_R):
            r_inner = r_step * dr
            r_outer = (r_step + 1) * dr
            theta_count = int(NUM_TILES_T * (r_outer / self.size_r) * 1.8) + 1
            effective_da = self.angle / theta_count
            for t_step in range(theta_count):
                t1 = math.radians(t_step * effective_da - self.angle/2)
                t2 = math.radians((t_step + 1) * effective_da - self.angle/2)
                p1 = (cx + r_inner * math.cos(t1), cy + r_inner * math.sin(t1))
                p2 = (cx + r_outer * math.cos(t1), cy + r_outer * math.sin(t1))
                p3 = (cx + r_outer * math.cos(t2), cy + r_outer * math.sin(t2))
                p4 = (cx + r_inner * math.cos(t2), cy + r_inner * math.sin(t2))
                tiles.append([p1, p2, p3, p4])
        return tiles

    def update_mosaic(self, texture_surface, movement_offset):
        self.base_surf.fill((0, 0, 0, 0))
        sw, sh = texture_surface.get_width(), texture_surface.get_height()
        for poly in self.tiles:
            avg_x = sum(p[0] for p in poly) / 4
            avg_y = sum(p[1] for p in poly) / 4
            tx = int((avg_x / (self.size_r*2)) * sw + math.sin(movement_offset)*60) % (sw-1)
            ty = int((avg_y / (self.size_r*2)) * sh + math.cos(movement_offset)*60) % (sh-1)
            color = texture_surface.get_at((tx, ty))
            pygame.draw.polygon(self.base_surf, color, poly)
            pygame.draw.polygon(self.base_surf, GROUT_COLOR, poly, GROUT_THICKNESS)

        mask = pygame.Surface((self.size_r * 2, self.size_r * 2), pygame.SRCALPHA)
        cx, cy = self.size_r, self.size_r
        overlap = 0.6 
        p1 = (cx + self.size_r * math.cos(math.radians(-30 - overlap)), 
              cy + self.size_r * math.sin(math.radians(-30 - overlap)))
        p2 = (cx + self.size_r * math.cos(math.radians(30 + overlap)), 
              cy + self.size_r * math.sin(math.radians(30 + overlap)))
        pygame.draw.polygon(mask, (255, 255, 255, 255), [(cx, cy), p1, p2])
        target = self.base_surf.copy()
        target.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        return target

def draw_ui(surf, speed):
    """Renders the speed indicator in the top right corner."""
    margin = 20
    bar_width = 150
    bar_height = 20
    
    # 1. Render Text
    text_surf = font.render(f"SPEED: {speed:.1f}x", True, (255, 255, 255))
    text_rect = text_surf.get_rect(topright=(WIDTH - margin, margin))
    
    # Draw a subtle dark background for the UI area
    bg_rect = pygame.Rect(WIDTH - bar_width - margin - 10, margin - 5, bar_width + 20, 60)
    pygame.draw.rect(surf, (0, 0, 0, 150), bg_rect, border_radius=5)
    
    # 2. Draw Speed Bar Background
    bar_bg_rect = pygame.Rect(WIDTH - bar_width - margin, margin + 35, bar_width, bar_height)
    pygame.draw.rect(surf, (50, 50, 50), bar_bg_rect)
    
    # 3. Draw Speed Bar Fill (Green/Cyan)
    # Clamp speed visually for the bar (0.0 to 3.0 range)
    fill_width = int((min(speed, 3.0) / 3.0) * bar_width)
    bar_fill_rect = pygame.Rect(WIDTH - bar_width - margin, margin + 35, fill_width, bar_height)
    pygame.draw.rect(surf, (0, 200, 255), bar_fill_rect)
    
    surf.blit(text_surf, text_rect)

# --- Main Variables ---
mosaic = MosaicWedge(WEDGE_RADIUS, WEDGE_ANGLE)
movement_accumulator = 0.0
speed_factor = 1.0 
running = True

while running:
    dt = clock.tick(30) / 1000.0 
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            if event.key == pygame.K_UP:
                speed_factor += 0.2
            if event.key == pygame.K_DOWN:
                speed_factor = max(0.0, speed_factor - 0.2)

    movement_accumulator += dt * speed_factor
    screen.fill((5, 5, 10))
    
    wedge = mosaic.update_mosaic(pic, movement_accumulator)
    flipped_wedge = pygame.transform.flip(wedge, False, True)

    spin = 15 * math.sin(movement_accumulator * 0.5)

    for i in range(6):
        angle = i * 60 + spin
        rot_a = pygame.transform.rotate(wedge, angle)
        rect_a = rot_a.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(rot_a, rect_a)
        
        rot_b = pygame.transform.rotate(flipped_wedge, angle)
        rect_b = rot_b.get_rect(center=(WIDTH//2, HEIGHT//2))
        screen.blit(rot_b, rect_b)

    # Render the UI on top
    draw_ui(screen, speed_factor)

    pygame.display.flip()

pygame.quit()
sys.exit()