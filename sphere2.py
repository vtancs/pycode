import pygame
import math

# Constants
S = 600       # Size of window
R = 250       # Radius of sphere
N1 = 40       # Number of latitudes
DA1 = math.pi / N1 
N2 = 40       # Number of longitudes
DA2 = 2 * math.pi / N2
Nfrhor = 450  # Frames for horizontal rotation
Nfrver = 1100 # Frames for vertical rotation
COL = (0, 0, 0) # Color of lines (Black)

# Vector defining light source
XL, YL, ZL = 1, 1.2, 0.6

def gensurf():
    """Generates the shaded sphere surface to match the BASIC version's look."""
    himg = pygame.Surface((S, S)) # Standard surface, no global transparency
    n = math.sqrt(XL**2 + YL**2 + ZL**2)
    offset = S // 2
    
    # Fill background with black to match the display
    himg.fill((0, 0, 0))

    for x in range(-R + 1, R + 2):
        for z in range(-R + 1, R + 2): 
            dist = math.hypot(x, z) 
            if dist <= R + 1: 
                # Calculate depth (y coordinate)
                y = math.sqrt(max(0, (R + 1)**2 - x**2 - z**2)) 
                
                # Dot product for diffuse reflection
                d = (XL * x + YL * y + ZL * z) / (R * n)
                d = max(0, min(1, d)) # Clamp 0 to 1 
                # Primary Green Surface: _RGB32(0, 20 + 235 * d, 0)
                r, g, b = 0, int(20 + 235 * d), 0 
                
                # Specular Highlight Logic: If d > 0.96 Then PSet (x, z), _RGB32(255, 100 * d)
                # In the original, this PSet overwrites the green with a bright, 
                # slightly transparent white-ish layer.
                if d > 0.96: 
                    # This replicates the "washed out" green look in the original image
                    # by blending white (255) into the existing color.
                    highlight_val = int(100 * d) 
                    r = min(255, r + highlight_val)
                    g = min(255, g + highlight_val)
                    b = min(255, b + highlight_val)
                himg.set_at((x + offset, z + offset), (r, g, b))
    return himg

def main():
    pygame.init()
    screen = pygame.display.set_mode((S, S))
    pygame.display.set_caption("Rotating Sphere")
    clock = pygame.time.Clock()

    hsurf = gensurf()
    
    rothorz = 0.0
    rotvert = 0.0
    offset = S / 2

    # Arrays to store previous coordinates for latitude lines
    xp = [0.0] * (N1 + 2)
    zp = [0.0] * (N1 + 2)

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                running = False

        # Pre-calculate rotation trigonometry
        cos_rotvert = math.cos(rotvert)
        sin_rotvert = math.sin(rotvert)

        # Draw the cached background surface
        screen.blit(hsurf, (0, 0))

        # Main Loop through longitudes and latitudes
        # angle2 = longitude, angle1 = latitude
        for j in range(N2 + 1):
            angle2 = j * DA2
            first = True
            k1 = 0
            
            for i in range(N1 + 1):
                angle1 = i * DA1
                
                # Spherical to Cartesian
                y_orig = R * math.sin(angle1) * math.sin(angle2 + rothorz)
                z_orig = R * math.cos(angle1)
                x = R * math.sin(angle1) * math.cos(angle2 + rothorz)
                
                # Vertical rotation around X axis
                zr = cos_rotvert * z_orig - sin_rotvert * y_orig
                yr = sin_rotvert * z_orig + cos_rotvert * y_orig
                
                # Projection coordinates (shifted to screen center)
                screen_x = x + offset
                screen_z = zr + offset

                if yr >= 0: # Depth testing (is it on the front half?)
                    if not first:
                        # Draw longitude segment (Line to previous point in this loop)
                        pygame.draw.line(screen, COL, (prev_x, prev_z), (screen_x, screen_z))
                        
                        # Draw latitude segment (Line to point from previous longitude)
                        if j > 0:
                            pygame.draw.line(screen, COL, (xp[k1], zp[k1]), (screen_x, screen_z))
                    else:
                        first = False
                
                # Store current for next iteration
                prev_x, prev_z = screen_x, screen_z
                xp[k1] = screen_x
                zp[k1] = screen_z
                k1 += 1

        pygame.display.flip()
        
        # Update rotation angles
        rothorz += (2 * math.pi / Nfrhor)
        if rothorz >= 2 * math.pi: rothorz = 0
        
        rotvert += (2 * math.pi / Nfrver)
        if rotvert >= 2 * math.pi: rotvert = 0

        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()