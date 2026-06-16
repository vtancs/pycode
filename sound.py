import pygame
import numpy as np
import sounddevice as sd

# ------------------------------------
# Configuration
# ------------------------------------
WIDTH = 1024
HEIGHT = 768

NUM_BARS = 80
MID_Y = 400
BAR_WIDTH = 10
MAX_HEIGHT = 200

SAMPLE_RATE = 44100
BLOCK_SIZE = 1024

# ------------------------------------
# Audio state
# ------------------------------------
current_db = -60.0


def audio_callback(indata, frames, time, status):
    global current_db

    if status:
        print(status)

    samples = indata[:, 0]

    rms = np.sqrt(np.mean(samples * samples))

    if rms > 1e-10:
        current_db = 20.0 * np.log10(rms)
    else:
        current_db = -60.0


# ------------------------------------
# Pygame setup
# ------------------------------------
pygame.init()

screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Microphone Loudness Visualizer")

clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 28)

# History buffer
bars = [0] * NUM_BARS

# ------------------------------------
# Start microphone
# ------------------------------------
stream = sd.InputStream(
    samplerate=SAMPLE_RATE,
    blocksize=BLOCK_SIZE,
    channels=1,
    callback=audio_callback,
)

stream.start()

# ------------------------------------
# Main loop
# ------------------------------------
running = True

try:
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()
        if keys[pygame.K_ESCAPE]:
            running = False

        # -----------------------------
        # Convert dBFS -> bar height
        # -----------------------------
        db_clamped = max(-60.0, min(0.0, current_db))

        height = int(
            ((db_clamped + 60.0) / 60.0)
            * MAX_HEIGHT
        )

        bars.pop(0)
        bars.append(height)

        # -----------------------------
        # Drawing
        # -----------------------------
        screen.fill((0, 0, 0))

        # Baseline
        pygame.draw.line(
            screen,
            (255, 255, 255),
            (0, MID_Y),
            (WIDTH, MID_Y),
            1,
        )

        for i, h in enumerate(bars):

            x = i * (BAR_WIDTH + 2)
            y = MID_Y - h

            green = max(0, min(255, int(255 - h / 2)))
            blue = max(0, min(255, int(100 + h / 2)))

            color = (0, green, blue)

            pygame.draw.rect(
                screen,
                color,
                pygame.Rect(
                    int(x),
                    int(y),
                    BAR_WIDTH,
                    max(1, int(h)),
                ),
            )

        # Text
        text = font.render(
            f"Mic Level: {current_db:.1f} dBFS",
            True,
            (255, 255, 255),
        )

        screen.blit(text, (10, 10))

        pygame.display.flip()
        clock.tick(60)

finally:
    stream.stop()
    stream.close()
    pygame.quit()