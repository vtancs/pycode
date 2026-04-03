import pygame
import os
import sys
import array
from datetime import datetime

# --- System Setup ---
pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=1)

info_object = pygame.display.Info()
SCREEN_WIDTH = info_object.current_w
SCREEN_HEIGHT = info_object.current_h

# Retro Color Palette
BG_COLOR = (5, 5, 12)
TEXT_COLOR = (120, 255, 255)
CLOCK_COLOR = (200, 200, 200)
BORDER_COLOR = (50, 255, 50)
BORDER_GLOW = (0, 150, 0, 100)
SCANLINE_COLOR = (0, 0, 0, 95)
LED_ON = (255, 0, 0)
LED_OFF = (60, 0, 0)

class WOPRTerminal:
    def __init__(self, target_file):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.RESIZABLE)
        pygame.display.set_caption("W.O.P.R. STRATEGIC COMMAND")
        
        self.target_file = target_file
        
        # 8 Point Font Scale
        self.font_sizes = [10, 12, 14, 18, 20, 22, 24, 28]
        self.font_index = 4  
        self.load_fonts()

        self.clock = pygame.time.Clock()
        self.speed_level = 15 
        
        # Audio State
        self.sound_enabled = True
        self.click_sound = self.generate_click_sound()
        
        # Text State
        self.content = self.load_data()
        self.displayed_lines = [""]
        self.char_index = 0
        self.last_char_time = pygame.time.get_ticks()
        
        # Cursor State
        self.cursor_visible = True
        self.last_cursor_blink = pygame.time.get_ticks()
        self.running = True

    def generate_click_sound(self):
        """Generates a short procedural mechanical click sound."""
        duration = 0.01  # seconds
        frequency = 800  # Hz
        sample_rate = 22050
        n_samples = int(duration * sample_rate)
        buf = array.array('h', [0] * n_samples)
        for i in range(n_samples):
            # Sine wave with quick decay
            t = float(i) / sample_rate
            value = 16384 * (1.0 - float(i)/n_samples) * (1 if (i // 10) % 2 == 0 else -1)
            buf[i] = int(value)
        return pygame.mixer.Sound(buf)

    def load_fonts(self):
        size = self.font_sizes[self.font_index]
        font_path = "Fixedsys.ttf"
        if os.path.exists(font_path):
            self.font = pygame.font.Font(font_path, size)
            self.small_font = pygame.font.Font(font_path, 18)
        else:
            self.font = pygame.font.SysFont("monospace", size, bold=True)
            self.small_font = pygame.font.SysFont("monospace", 18, bold=True)
        self.line_height = int(size * 1.3)

    def load_data(self):
        if os.path.exists(self.target_file):
            try:
                with open(self.target_file, "r", encoding="utf-8") as f:
                    return f.read().upper()
            except Exception as e:
                return f"SYSTEM ERROR: ACCESS DENIED\n{str(e).upper()}"
        return f"GREETINGS PROFESSOR FALKEN.\n\nERROR: {self.target_file.upper()} NOT FOUND."

    def get_delay(self):
        if self.speed_level >= 30: return 0
        return 600 * (0.83 ** self.speed_level)

    def draw_neon_border(self):
        glow_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, BORDER_GLOW, (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT), 12)
        self.screen.blit(glow_surf, (0, 0))
        pygame.draw.rect(self.screen, BORDER_COLOR, (3, 3, SCREEN_WIDTH-6, SCREEN_HEIGHT-6), 4)
        
    def draw_led_bar(self):
        num_leds = 30
        led_w, led_h, gap = 25, 10, 4
        x_pos = SCREEN_WIDTH - 50 - 10
        start_y = SCREEN_HEIGHT - 80 - 10
        for i in range(num_leds):
            y_pos = start_y - (i * (led_h + gap))
            is_active = (i + 1) <= self.speed_level
            color = LED_ON if is_active else LED_OFF
            pygame.draw.rect(self.screen, color, (x_pos, y_pos, led_w, led_h))
            if is_active:
                pygame.draw.rect(self.screen, (255, 150, 150), (x_pos, y_pos, led_w, led_h), 1)
        label = self.small_font.render("PROC SPEED", True, CLOCK_COLOR)
        self.screen.blit(label, (x_pos - 70, start_y + 20))
        val_surf = self.small_font.render(f"{self.speed_level:02}", True, LED_ON if self.speed_level == 30 else (255, 255, 255))
        self.screen.blit(val_surf, (x_pos + 4, start_y - (num_leds * (led_h + gap)) - 25))

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: self.running = False
                elif event.key == pygame.K_UP: self.speed_level = min(30, self.speed_level + 1)
                elif event.key == pygame.K_DOWN: self.speed_level = max(1, self.speed_level - 1)
                elif event.key == pygame.K_LEFTBRACKET: 
                    self.font_index = max(0, self.font_index - 1)
                    self.load_fonts()
                elif event.key == pygame.K_RIGHTBRACKET: 
                    self.font_index = min(len(self.font_sizes) - 1, self.font_index + 1)
                    self.load_fonts()
                elif event.key == pygame.K_q:
                    self.sound_enabled = not self.sound_enabled

    def update(self):
        now = pygame.time.get_ticks()
        delay = self.get_delay()
        if now - self.last_cursor_blink > 500:
            self.cursor_visible = not self.cursor_visible
            self.last_cursor_blink = now

        chars_this_frame = 100 if delay == 0 else (int(16 / max(1, delay)) if delay < 16 else 1)
        sound_played = False

        for _ in range(chars_this_frame):
            if self.char_index < len(self.content):
                if delay < 16 or (now - self.last_char_time > delay):
                    char = self.content[self.char_index]
                    if char == '\n':
                        self.displayed_lines.append("")
                    else:
                        self.displayed_lines[-1] += char
                    self.char_index += 1
                    self.last_char_time = now
                    self.cursor_visible = True
                    if self.sound_enabled and not sound_played and not char.isspace():
                        self.click_sound.play()
                        sound_played = True # Avoid audio saturation in bursts
                else: break
            else: break

    def draw(self):
        self.screen.fill(BG_COLOR)
        self.draw_neon_border()
        
        now_dt = datetime.now()
        time_str = now_dt.strftime("%b %d %Y  %H:%M:%S").upper()
        snd_status = "ON" if self.sound_enabled else "OFF"
        info_str = f"DB: {self.target_file.upper()} | FONT: {self.font_sizes[self.font_index]}PT | SOUND {snd_status}"
        
        time_surf = self.small_font.render(time_str, True, CLOCK_COLOR)
        info_surf = self.small_font.render(info_str, True, TEXT_COLOR)
        self.screen.blit(info_surf, (60, 40))
        self.screen.blit(time_surf, (SCREEN_WIDTH - time_surf.get_width() - 110, 40))

        margin_left, start_y = 60, 110
        max_visible = (SCREEN_HEIGHT - start_y - 80) // self.line_height
        visible_lines = self.displayed_lines[-max_visible:]
        
        for i, line in enumerate(visible_lines):
            y_pos = start_y + (i * self.line_height)
            line_surf = self.font.render(line, True, TEXT_COLOR)
            self.screen.blit(line_surf, (margin_left, y_pos))
            if i == len(visible_lines) - 1 and self.cursor_visible:
                c_x = margin_left + line_surf.get_width() + 2
                c_w, c_h = self.font_sizes[self.font_index] // 2 + 4, self.line_height // 2
                pygame.draw.rect(self.screen, TEXT_COLOR, (c_x, y_pos + (self.line_height // 2) - 4, c_w, c_h))

        self.draw_led_bar()
        # Scanlines last
        for y in range(0, SCREEN_HEIGHT, 4):
            s = pygame.Surface((SCREEN_WIDTH, 2), pygame.SRCALPHA)
            s.fill(SCANLINE_COLOR)
            self.screen.blit(s, (0, y))
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(60)
        pygame.quit()

if __name__ == "__main__":
    cli_file = sys.argv[1] if len(sys.argv) > 1 else "data.txt"
    WOPRTerminal(cli_file).run()