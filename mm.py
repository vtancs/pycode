import pygame
import random

# --- Configuration & Colors ---
WIDTH, HEIGHT = 1000, 750
FPS = 60

BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

# Board Geometry
BOARD_X = 120
BOARD_WIDTH = 380

class MastermindGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Mastermind - Retro Edition")
        self.clock = pygame.time.Clock()
        
        # Fonts - Reduced the Logo size to 42 for a better fit
        self.font_small = pygame.font.SysFont("monospace", 18)
        self.font_main = pygame.font.SysFont("monospace", 24, bold=True)
        self.font_logo = pygame.font.SysFont("monospace", 42, bold=True)
        
        self.reset_game()

    def reset_game(self):
        self.secret_code = [random.randint(1, 6) for _ in range(4)]
        self.guesses = []  
        self.current_guess = [] 
        self.game_over = False
        self.won = False

    def draw_shape(self, shape_num, x, y, size=30, color=GREEN, thickness=2):
        rect = pygame.Rect(x, y, size, size)
        if shape_num == 1: # Square
            pygame.draw.rect(self.screen, color, rect, thickness)
        elif shape_num == 2: # Triangle
            pts = [(x + size//2, y), (x, y + size), (x + size, y + size)]
            pygame.draw.polygon(self.screen, color, pts, thickness)
        elif shape_num == 3: # Right Triangle
            pts = [(x, y), (x + size, y + size//2), (x, y + size)]
            pygame.draw.polygon(self.screen, color, pts, thickness)
        elif shape_num == 4: # Diamond
            pts = [(x + size//2, y), (x + size, y + size//2), (x + size//2, y + size), (x, y + size//2)]
            pygame.draw.polygon(self.screen, color, pts, thickness)
        elif shape_num == 5: # Inverted Triangle
            pts = [(x, y), (x + size, y), (x + size//2, y + size)]
            pygame.draw.polygon(self.screen, color, pts, thickness)
        elif shape_num == 6: # Left Triangle
            pts = [(x + size, y), (x, y + size//2), (x + size, y + size)]
            pygame.draw.polygon(self.screen, color, pts, thickness)

    def draw_ui(self):
        self.screen.fill(BLACK)
        
        # --- 1. Main Game Board ---
        pygame.draw.rect(self.screen, GREEN, (BOARD_X, 40, BOARD_WIDTH, 600), 3)
        
        # CENTERED LOGO LOGIC
        title_surf = self.font_logo.render("Mastermind", True, GREEN)
        # Calculate center: (Board Start + Board Width/2) - (Text Width/2)
        title_x = BOARD_X + (BOARD_WIDTH // 2) - (title_surf.get_width() // 2)
        self.screen.blit(title_surf, (title_x, 65))
        
        pygame.draw.line(self.screen, GREEN, (BOARD_X, 130), (BOARD_X + BOARD_WIDTH, 130), 2)
        pygame.draw.line(self.screen, GREEN, (310, 130), (310, 640), 2)
        pygame.draw.line(self.screen, GREEN, (BOARD_X, 175), (BOARD_X + BOARD_WIDTH, 175), 2)
        
        self.screen.blit(self.font_main.render("GUESS", True, GREEN), (180, 140))
        self.screen.blit(self.font_main.render("SCORE", True, GREEN), (370, 140))

        # --- 2. Draw Past Guesses (Green) ---
        for idx, (g_list, (c, x)) in enumerate(self.guesses):
            y_pos = 185 + (idx * 45)
            self.screen.blit(self.font_main.render("".join(map(str, g_list)), True, GREEN), (30, y_pos))
            for i, s in enumerate(g_list):
                self.draw_shape(s, 135 + (i * 40), y_pos)
            
            score_x = 320
            for _ in range(c):
                self.screen.blit(self.font_main.render("✓", True, GREEN), (score_x, y_pos))
                score_x += 30
            for _ in range(x):
                self.screen.blit(self.font_main.render("X", True, GREEN), (score_x, y_pos))
                score_x += 30

        # --- 3. Current Active Input + BLINKING CURSOR ---
        if not self.game_over:
            current_y = 185 + (len(self.guesses) * 45)
            typed_str = "".join(map(str, self.current_guess))
            self.screen.blit(self.font_main.render(typed_str, True, RED), (30, current_y))
            
            cursor_x = 30 + (len(self.current_guess) * 15)
            if pygame.time.get_ticks() % 1000 < 500:
                pygame.draw.rect(self.screen, RED, (cursor_x, current_y + 4, 14, 22))

            for i, shape_val in enumerate(self.current_guess):
                self.draw_shape(shape_val, 135 + (i * 40), current_y, color=RED, thickness=4)

        # --- 4. Sidebar Instructions ---
        instr_x = 550
        instr_text = ["INSTRUCTIONS:", "", "Type 1-6 to choose shapes", "Press RETURN to submit", "Press BACKSPACE to undo"]
        for i, line in enumerate(instr_text):
            surf = self.font_small.render(line, True, GREEN)
            self.screen.blit(surf, (instr_x, 40 + (i * 22)))

        # --- 5. Shape Legend ---
        legend_y = 540
        self.screen.blit(self.font_main.render("SIX SHAPES in this game:", True, GREEN), (instr_x, legend_y))
        for i in range(1, 7):
            lx = instr_x + ((i-1) * 65)
            self.draw_shape(i, lx, legend_y + 40, size=35, color=GREEN, thickness=2)
            self.screen.blit(self.font_main.render(str(i), True, GREEN), (lx + 12, legend_y + 85))

        if self.game_over:
            msg = "SUCCESS!" if self.won else f"CODE WAS: {''.join(map(str, self.secret_code))}"
            self.screen.blit(self.font_main.render(msg, True, RED), (130, 660))
            self.screen.blit(self.font_main.render("Another Game? (Y or N)", True, GREEN), (30, 710))

    def get_score(self, guess):
        code_copy = list(self.secret_code)
        guess_copy = list(guess)
        checks = sum(1 for i in range(4) if guess_copy[i] == code_copy[i])
        for i in range(3, -1, -1):
            if guess[i] == self.secret_code[i]:
                code_copy.pop(i)
                guess_copy.pop(i)
        xs = 0
        for val in guess_copy:
            if val in code_copy:
                xs += 1
                code_copy.remove(val)
        return checks, xs

    def run(self):
        running = True
        while running:
            self.draw_ui()
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN:
                    if not self.game_over:
                        if event.unicode in "123456" and len(self.current_guess) < 4:
                            self.current_guess.append(int(event.unicode))
                        elif event.key == pygame.K_RETURN and len(self.current_guess) == 4:
                            score = self.get_score(self.current_guess)
                            self.guesses.append((list(self.current_guess), score))
                            if score[0] == 4:
                                self.game_over, self.won = True, True
                            elif len(self.guesses) >= 10:
                                self.game_over = True
                            self.current_guess = []
                        elif event.key == pygame.K_BACKSPACE:
                            if self.current_guess: self.current_guess.pop()
                    else:
                        if event.key == pygame.K_y: self.reset_game()
                        elif event.key == pygame.K_n: running = False
            
            pygame.display.flip()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == "__main__":
    MastermindGame().run()