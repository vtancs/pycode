import pygame
import math
import random
import sys

# Initialize Pygame and its font module
pygame.init()
pygame.font.init()

# --- Configuration & Constants ---
WIDTH, HEIGHT = 1024, 768
FPS = 60
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Text Lissajous Traffic Simulator")
CLOCK = pygame.time.Clock()

# Colors (Matrix / Retro Arcade theme)
COLOR_BG = (5, 10, 5)
COLOR_AXIS = (30, 80, 30)      # Dim green for the '.' grid
COLOR_UI = (0, 255, 0)         # Bright green for text readouts

# Load a monospace font to mimic the text screen
FONT_SIZE = 20
try:
    FONT = pygame.font.SysFont("Courier New", FONT_SIZE, bold=True)
except:
    FONT = pygame.font.Font(None, FONT_SIZE)

# Calculate grid spacing based on font size
CHAR_W, CHAR_H = FONT.size("A")
GRID_COLS = WIDTH // CHAR_W
GRID_ROWS = HEIGHT // CHAR_H

# Center of the screen in grid coordinates
CENTER_X = GRID_COLS // 2
CENTER_Y = GRID_ROWS // 2

# Lissajous Amplitudes (in grid units)
XA = int(CENTER_X * 0.85)
YA = int(CENTER_Y * 0.85)

# --- Global Simulation Variables ---
global_speed_multiplier = 1.0
is_paused = False

# Color Modes: 0 = Retro Green, 1 = Brown, 2 = White, 3 = Randomize
current_color_mode = 0
COLOR_MODE_NAMES = ["Retro Green", "Brown/Amber", "White/Silver", "Randomized"]

# --- Traffic Particle Class ---
class Vehicle:
    def __init__(self):
        # Frequencies from original code (FX% = 3, FY% = 5)
        self.fx = 3.0
        self.fy = 5.0
        
        # Randomize starting position along the curve
        self.t = random.uniform(0, 2 * math.pi)
        
        # Base speed unique to this vehicle
        self.base_speed = random.uniform(0.015, 0.035)
        
        # Initialize color based on current mode
        self.color = (0, 255, 0)
        self.update_color()
        
        # History trail for a motion blur effect
        self.trail = []
        self.max_trail = random.randint(4, 10)

    def update_color(self):
        """Sets vehicle color based on the current active global mode."""
        global current_color_mode
        if current_color_mode == 0:    # Retro Green
            # Variations of classic terminal green
            self.color = (random.randint(0, 50), random.randint(180, 255), random.randint(0, 50))
        elif current_color_mode == 1:  # Brown / Amber
            # Variations of warm vintage brown/orange/amber
            r = random.randint(180, 240)
            g = int(r * random.uniform(0.5, 0.65)) # Keeps it in the amber/brown range
            b = random.randint(10, 40)
            self.color = (r, g, b)
        elif current_color_mode == 2:  # White / Silver
            # Variations of bright monochrome white/light gray
            gray = random.randint(200, 255)
            self.color = (gray, gray, gray)
        elif current_color_mode == 3:  # Randomize
            # Full wild spectrum
            self.color = (
                random.randint(50, 255),
                random.randint(50, 255),
                random.randint(50, 255)
            )

    def update(self):
        if is_paused:
            return

        # Progress along the Lissajous path factoring in global speed modifier
        self.t += self.base_speed * global_speed_multiplier
        
        # Calculate X and Y positions
        raw_x = math.cos(self.fx * self.t)
        raw_y = math.sin(self.fy * self.t)
        
        # Map to grid coordinates
        grid_x = int(CENTER_X + XA * raw_x)
        grid_y = int(CENTER_Y + YA * raw_y)
        
        # Update trail
        if not self.trail or self.trail[-1] != (grid_x, grid_y):
            self.trail.append((grid_x, grid_y))
            if len(self.trail) > self.max_trail:
                self.trail.pop(0)

    def draw(self, surface):
        # Draw the tail/trail (fading out)
        for i, (gx, gy) in enumerate(self.trail[:-1]):
            alpha_factor = (i + 1) / len(self.trail)
            dim_color = tuple(int(c * alpha_factor * 0.4) for c in self.color)
            
            trail_surf = FONT.render("*", True, dim_color)
            surface.blit(trail_surf, (gx * CHAR_W, gy * CHAR_H))
            
        # Draw the lead "vehicle"
        if self.trail:
            gx, gy = self.trail[-1]
            lead_surf = FONT.render("*", True, self.color)
            surface.blit(lead_surf, (gx * CHAR_W, gy * CHAR_H))

# --- Setup Traffic Fleet ---
NUM_VEHICLES = 80
traffic_fleet = [Vehicle() for _ in range(NUM_VEHICLES)]

# --- Main Game Loop ---
running = True
while running:
    SCREEN.fill(COLOR_BG)
    
    # 1. Handle Events / Inputs
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            # ESC: Quit
            if event.key == pygame.K_ESCAPE:
                running = False
                
            # SPACE: Pause / Unpause
            elif event.key == pygame.K_SPACE:
                is_paused = not is_paused
                
            # UP ARROW: Increase speed
            elif event.key == pygame.K_UP:
                global_speed_multiplier += 0.25
                if global_speed_multiplier > 5.0:
                    global_speed_multiplier = 5.0
                    
            # DOWN ARROW: Decrease speed
            elif event.key == pygame.K_DOWN:
                global_speed_multiplier -= 0.25
                if global_speed_multiplier < 0.0:
                    global_speed_multiplier = 0.0
                    
            # C: Cycle through the 4 color modes
            elif event.key == pygame.K_c:
                current_color_mode = (current_color_mode + 1) % 4
                for vehicle in traffic_fleet:
                    vehicle.update_color()

    # 2. Draw Static Text Axes
    for cx in range(GRID_COLS):
        axis_surf = FONT.render(".", True, COLOR_AXIS)
        SCREEN.blit(axis_surf, (cx * CHAR_W, CENTER_Y * CHAR_H))
    for cy in range(GRID_ROWS):
        axis_surf = FONT.render(".", True, COLOR_AXIS)
        SCREEN.blit(axis_surf, (CENTER_X * CHAR_W, cy * CHAR_H))

    # 3. Update and Draw "Traffic"
    for vehicle in traffic_fleet:
        vehicle.update()
        vehicle.draw(SCREEN)

    # 4. Render On-Screen UI / Heads-Up Display
    status_text = "PAUSED" if is_paused else "RUNNING"
    speed_pct = int(global_speed_multiplier * 100)
    current_mode_name = COLOR_MODE_NAMES[current_color_mode]
    
    ui_string = f"STATUS: {status_text} | SPEED: {speed_pct}% | COLOR MODE: {current_mode_name}"
    controls_string = "[SPACE] Pause | [UP/DN] Speed | [C] Cycle Colors (4 Modes) | [ESC] Quit"
    
    ui_surface = FONT.render(ui_string, True, COLOR_UI)
    controls_surface = FONT.render(controls_string, True, COLOR_AXIS)
    
    # Render text overlay at top-left corner
    SCREEN.blit(ui_surface, (20, 20))
    SCREEN.blit(controls_surface, (20, 45))

    # 5. Flip Framebuffer
    pygame.display.flip()
    CLOCK.tick(FPS)

pygame.quit()
sys.exit()