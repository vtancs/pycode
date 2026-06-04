import pygame
import random
import sys

# Initialize Pygame
pygame.init()
pygame.font.init()

# Setup screen and clock
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("2D Particle System")
clock = pygame.time.Clock()

font = pygame.font.SysFont("Arial", 20)

# Global variables
fountainX = WIDTH // 2
fountainY = HEIGHT // 2
gravity = 0.15 

# NEW: Track how many particles spawn automatically every frame
spawn_rate = 1 

# Particle collection
particles = []

class Particle:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.life = 0

def SpawnParticle():
    p = Particle()
    p.x = fountainX
    p.y = fountainY
    p.vx = random.uniform(-1.0, 1.0) * 2.0
    p.vy = -random.uniform(4.0, 7.0)
    p.life = random.randint(40, 80)
    particles.append(p)

def UpdateParticles():
    for p in reversed(particles):
        p.vy = p.vy + gravity
        p.x = p.x + p.vx
        p.y = p.y + p.vy
        p.life = p.life - 1
        
        if p.life <= 0 or p.y > 600:
            particles.remove(p)

def DrawParticles():
    color = (100, 150, 255)
    for p in particles:
        pygame.draw.rect(screen, color, (int(p.x), int(p.y), 2, 2))

def DrawHUD():
    white = (255, 255, 255)
    count_text = font.render(f"Particles: {len(particles)}", True, white)
    rate_text = font.render(f"Spawn Rate: {spawn_rate} per frame", True, (0, 255, 0))
    exit_text = font.render("Press ESC to exit", True, white)
    controls_text = font.render("Up/Down Arrows: Adjust spawn rate by 5", True, (150, 150, 150))
    
    screen.blit(count_text, (20, 20))
    screen.blit(rate_text, (20, 45))
    screen.blit(exit_text, (20, 70))
    screen.blit(controls_text, (20, 95))

# Main game loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
                
            # Increase the permanent spawn rate by 5
            elif event.key == pygame.K_UP:
                spawn_rate += 5
                    
            # Decrease the permanent spawn rate by 5 (but don't let it go below 0)
            elif event.key == pygame.K_DOWN:
                spawn_rate = max(0, spawn_rate - 5)

    # Background clear
    screen.fill((0, 0, 0))

    # FIXED: Spawn the current rate amount of particles every single frame
    for _ in range(spawn_rate):
        SpawnParticle()

    # Core updates and drawing
    UpdateParticles()
    DrawParticles()
    DrawHUD()

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()