# snake_full_features.py
# All features integrated:
# 1 Speed increases with score
# 2 Game Over / Restart screen (R to restart, Q to quit)
# 3 Pause / Resume (P)
# 4 Wrap-around world
# 5 Better collision & smoother growth
# 6 Multiple food types (common, rare, bad)
# 7 High-score save to file
# 8 Sound effects (optional audio files: 'eat.wav', 'gameover.wav')
# 9 Keyboard + touch/swipe support
# 10 Polish UI (start menu, HUD, colors)

import pygame
import sys
import random
import os
from pathlib import Path

pygame.init()
pygame.mixer.init()  # may fail silently on some systems

# ----- constants -----
WIDTH, HEIGHT = 600, 440     # extra vertical space for HUD
BLOCK = 20
HUD_HEIGHT = 40               # top bar height for score/highscore
GAME_AREA_HEIGHT = HEIGHT - HUD_HEIGHT

# grid dims (precomputed)
COLS = WIDTH // BLOCK
ROWS = GAME_AREA_HEIGHT // BLOCK

FPS_BASE = 10  # starting fps

# colors
BG = (30, 30, 30)
GRID = (50, 50, 50)
FOOD_COLORS = {
    'common': (255, 0, 0),    # red
    'rare': (255, 215, 0),     # gold
    'bad': (0, 0, 255)        # blue (bad food - penalty)
}
SNAKE_HEAD = (0, 230, 0)
SNAKE_BODY = (0, 160, 0)
HUD_BG = (20, 20, 20)
HUD_TEXT = (220, 220, 220)
PAUSE_TEXT = (255, 255, 0)

# file for high score
HS_FILE = Path("highscore.txt")

# try to load optional sounds (place eat.wav and gameover.wav in same folder)
SOUND_EAT = None
SOUND_GAMEOVER = None
try:
    if Path("eat.wav").exists():
        SOUND_EAT = pygame.mixer.Sound("eat.wav")
    if Path("gameover.wav").exists():
        SOUND_GAMEOVER = pygame.mixer.Sound("gameover.wav")
except Exception:
    SOUND_EAT = None
    SOUND_GAMEOVER = None

# ----- pygame init -----
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake — All Features")
clock = pygame.time.Clock()
font = pygame.font.Font(None, 28)
font_big = pygame.font.Font(None, 44)

# --- game state globals (managed inside reset_game) ---
def load_highscore():
    try:
        if HS_FILE.exists():
            with HS_FILE.open("r") as f:
                return int(f.read().strip() or 0)
    except Exception:
        pass
    return 0

def save_highscore(score):
    try:
        with HS_FILE.open("w") as f:
            f.write(str(score))
    except Exception:
        pass

def reset_game():
    global snake_x, snake_y, vx, vy, started, paused
    global snake_length, snake_body, score, speed
    global food_x, food_y, food_type
    global highscore, wrap_enabled, game_state
    # snake in grid coords
    snake_x, snake_y = COLS // 2, ROWS // 2
    vx, vy = 0, 0
    started = False
    paused = False
    snake_length = 3
    # initial body: head then two behind
    snake_body = [(snake_x, snake_y), (snake_x - 1, snake_y), (snake_x - 2, snake_y)]
    score = 0
    speed = FPS_BASE
    # put food
    food_x, food_y, food_type = spawn_food()
    highscore = load_highscore()
    # wrap-around toggle (True means the snake wraps)
    wrap_enabled = True
    # game_state: 'menu', 'playing', 'gameover'
    game_state = 'menu'

def spawn_food():
    """Return (fx, fy, type) where type is 'common'|'rare'|'bad'"""
    # probability: common 75%, rare 15%, bad 10%
    r = random.random()
    if r < 0.75:
        kind = 'common'
    elif r < 0.90:
        kind = 'rare'
    else:
        kind = 'bad'
    while True:
        fx = random.randint(0, COLS - 1)
        fy = random.randint(0, ROWS - 1)
        if (fx, fy) not in snake_body:
            return fx, fy, kind

def play_sound(sound):
    try:
        if sound:
            sound.play()
    except Exception:
        pass

def game_over_screen():
    """Blocking-ish: sets game_state back to 'playing' (after reset) or quits."""
    global game_state, running, highscore
    # show overlay and wait for R or Q
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    reset_game()
                    game_state = 'playing'
                    return
                elif event.key == pygame.K_q:
                    running = False
                    return

        # render overlay
        screen.fill((0, 0, 0))
        over = font_big.render("GAME OVER", True, (255, 60, 60))
        sc = font.render(f"Score: {score}", True, HUD_TEXT)
        hs = font.render(f"High Score: {highscore}", True, HUD_TEXT)
        info = font.render("Press R to Restart or Q to Quit", True, HUD_TEXT)

        screen.blit(over, (WIDTH//2 - over.get_width()//2, HEIGHT//3 - 40))
        screen.blit(sc, (WIDTH//2 - sc.get_width()//2, HEIGHT//3 + 10))
        screen.blit(hs, (WIDTH//2 - hs.get_width()//2, HEIGHT//3 + 40))
        screen.blit(info, (WIDTH//2 - info.get_width()//2, HEIGHT//3 + 80))
        pygame.display.flip()
        clock.tick(10)

# touch / swipe support helpers
touch_start_pos = None
def handle_swipe(pos_start, pos_end):
    """Convert swipe vector to a direction (vx, vy) with no reverse allowed."""
    global vx, vy, started
    dx = pos_end[0] - pos_start[0]
    dy = pos_end[1] - pos_start[1]
    # ignore small movements
    if abs(dx) < 20 and abs(dy) < 20:
        return
    # choose the dominant direction
    if abs(dx) > abs(dy):
        # horizontal swipe
        if dx > 0 and vx == 0:   # right
            vx, vy = 1, 0
            started = True
        elif dx < 0 and vx == 0: # left
            vx, vy = -1, 0
            started = True
    else:
        if dy > 0 and vy == 0:   # down
            vx, vy = 0, 1
            started = True
        elif dy < 0 and vy == 0: # up
            vx, vy = 0, -1
            started = True

# initial setup
reset_game()
running = True

# small helper to draw HUD
def draw_hud():
    # top bar
    pygame.draw.rect(screen, HUD_BG, (0, 0, WIDTH, HUD_HEIGHT))
    score_txt = font.render(f"Score: {score}", True, HUD_TEXT)
    screen.blit(score_txt, (8, 8))
    hs_txt = font.render(f"High: {highscore}", True, HUD_TEXT)
    screen.blit(hs_txt, (WIDTH - hs_txt.get_width() - 8, 8))
    speed_txt = font.render(f"Speed: {speed}", True, HUD_TEXT)
    screen.blit(speed_txt, (WIDTH//2 - speed_txt.get_width()//2, 8))
    wrap_txt = font.render(f"Wrap: {'On' if wrap_enabled else 'Off'} (Press W to toggle)", True, HUD_TEXT)
    screen.blit(wrap_txt, (8, HUD_HEIGHT - wrap_txt.get_height() - 4))

# main loop
while running:
    # --- event handling ---
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # touch/mouse handling for swipe (basic)
        if event.type == pygame.MOUSEBUTTONDOWN:
            # only consider swipes inside the game area (below HUD)
            sx, sy = event.pos
            if sy > HUD_HEIGHT:
                touch_start_pos = event.pos
            else:
                touch_start_pos = None

        if event.type == pygame.MOUSEBUTTONUP:
            if touch_start_pos:
                handle_swipe(touch_start_pos, event.pos)
            touch_start_pos = None

        if event.type == pygame.KEYDOWN:
            # Global keys
            if game_state == 'menu':
                # Enter to start, or arrow keys to set initial dir
                if event.key == pygame.K_RETURN:
                    game_state = 'playing'
                elif event.key == pygame.K_LEFT:
                    vx, vy = -1, 0; started = True; game_state = 'playing'
                elif event.key == pygame.K_RIGHT:
                    vx, vy = 1, 0; started = True; game_state = 'playing'
                elif event.key == pygame.K_UP:
                    vx, vy = 0, -1; started = True; game_state = 'playing'
                elif event.key == pygame.K_DOWN:
                    vx, vy = 0, 1; started = True; game_state = 'playing'
            elif game_state == 'playing':
                # Movement keys (prevent direct reverse)
                if event.key == pygame.K_LEFT and vx == 0:
                    vx, vy = -1, 0; started = True
                elif event.key == pygame.K_RIGHT and vx == 0:
                    vx, vy = 1, 0; started = True
                elif event.key == pygame.K_UP and vy == 0:
                    vx, vy = 0, -1; started = True
                elif event.key == pygame.K_DOWN and vy == 0:
                    vx, vy = 0, 1; started = True
                elif event.key == pygame.K_p:
                    paused = not paused
                elif event.key == pygame.K_w:
                    wrap_enabled = not wrap_enabled
                elif event.key == pygame.K_s:
                    # quick save highscore
                    if score > highscore:
                        highscore = score
                        save_highscore(highscore)
            elif game_state == 'gameover':
                # handled by game_over_screen
                pass

            # Universal: quit / restart (useful)
            if event.key == pygame.K_q:
                running = False
            if event.key == pygame.K_r:
                reset_game()
                game_state = 'playing'

    # Menu screen
    if game_state == 'menu':
        # draw background & menu
        screen.fill(BG)
        title = font_big.render("SNAKE — All Features Demo", True, (200, 200, 255))
        instr = font.render("Arrows to move | P=Pause | R=Restart | W=Toggle Wrap | Enter to Start", True, HUD_TEXT)
        screen.blit(title, (WIDTH//2 - title.get_width()//2, HEIGHT//3 - 20))
        screen.blit(instr, (WIDTH//2 - instr.get_width()//2, HEIGHT//3 + 30))
        # show last highscore
        hs = font.render(f"High Score: {highscore}", True, HUD_TEXT)
        screen.blit(hs, (WIDTH//2 - hs.get_width()//2, HEIGHT//3 + 80))
        pygame.display.flip()
        clock.tick(30)
        continue

    # If paused: show pause overlay and skip game updates
    if paused:
        # draw current scene under pause overlay
        screen.fill(BG)
        # grid and snake/food drawing for paused snapshot
        for x in range(0, WIDTH, BLOCK):
            pygame.draw.line(screen, GRID, (x, HUD_HEIGHT), (x, HEIGHT))
        for y in range(HUD_HEIGHT, HEIGHT, BLOCK):
            pygame.draw.line(screen, GRID, (0, y), (WIDTH, y))
        # draw food and snake
        pygame.draw.rect(screen, FOOD_COLORS[food_type], (food_x * BLOCK, HUD_HEIGHT + food_y * BLOCK, BLOCK, BLOCK))
        for i, (sx, sy) in enumerate(snake_body):
            color = SNAKE_HEAD if i == 0 else SNAKE_BODY
            pygame.draw.rect(screen, color, (sx * BLOCK, HUD_HEIGHT + sy * BLOCK, BLOCK, BLOCK))
        draw_hud()
        pause_txt = font_big.render("PAUSED", True, PAUSE_TEXT)
        sub = font.render("Press P to resume", True, PAUSE_TEXT)
        screen.blit(pause_txt, (WIDTH//2 - pause_txt.get_width()//2, HEIGHT//2 - 20))
        screen.blit(sub, (WIDTH//2 - sub.get_width()//2, HEIGHT//2 + 20))
        pygame.display.flip()
        clock.tick(10)
        continue

    # --- game updates (playing state) ---
    if started:
        # Move head one grid step
        snake_x += vx
        snake_y += vy

        # WRAP or WALL behaviour
        if wrap_enabled:
            snake_x = snake_x % COLS
            snake_y = snake_y % ROWS
        else:
            # if hitting wall -> game over
            if snake_x < 0 or snake_x >= COLS or snake_y < 0 or snake_y >= ROWS:
                # score -> highscore check
                if score > highscore:
                    highscore = score
                    save_highscore(highscore)
                play_sound(SOUND_GAMEOVER)
                game_state = 'gameover'
                game_over_screen()
                continue

        # insert new head
        snake_body.insert(0, (snake_x, snake_y))

        # self-collision: head colliding with body (except allow overlapping the tail if it will move)
        # better check: if head in body[1:snake_length] -> immediate death
        if (snake_x, snake_y) in snake_body[1:]:
            if score > highscore:
                highscore = score
                save_highscore(highscore)
            play_sound(SOUND_GAMEOVER)
            game_state = 'gameover'
            game_over_screen()
            continue

        # food collision
        if snake_x == food_x and snake_y == food_y:
            # effect by food type
            if food_type == 'common':
                score += 1
                snake_length += 1  # grow by 1
                # small speed bump every 2 common foods
            elif food_type == 'rare':
                score += 3
                snake_length += 2
                # bonus speed
            elif food_type == 'bad':
                # penalty: lose one segment if possible and decrement score
                score = max(0, score - 1)
                snake_length = max(1, snake_length - 1)

            # play munch
            play_sound(SOUND_EAT)

            # dynamic speed rule: for every 3 points, +1 fps; rare foods bump more
            # You can tweak the rule below as desired:
            speed = FPS_BASE + score // 3

            # spawn new food not overlapping the snake
            food_x, food_y, food_type = spawn_food()
        else:
            # trim tail until length matches snake_length (smooth growth)
            while len(snake_body) > snake_length:
                snake_body.pop()

    # drawing
    screen.fill(BG)

    # draw HUD
    draw_hud()

    # draw grid in game area
    for x in range(0, WIDTH, BLOCK):
        pygame.draw.line(screen, GRID, (x, HUD_HEIGHT), (x, HEIGHT))
    for y in range(HUD_HEIGHT, HEIGHT, BLOCK):
        pygame.draw.line(screen, GRID, (0, y), (WIDTH, y))

    # draw food (note: draw in game area offset by HUD_HEIGHT)
    fx_pix = food_x * BLOCK
    fy_pix = HUD_HEIGHT + food_y * BLOCK
    pygame.draw.rect(screen, FOOD_COLORS[food_type], (fx_pix, fy_pix, BLOCK, BLOCK))

    # draw snake
    for i, (sx, sy) in enumerate(snake_body):
        color = SNAKE_HEAD if i == 0 else SNAKE_BODY
        pygame.draw.rect(screen, color, (sx * BLOCK, HUD_HEIGHT + sy * BLOCK, BLOCK, BLOCK))

    # small UI extras
    # draw a thin divider under HUD
    pygame.draw.line(screen, (60, 60, 60), (0, HUD_HEIGHT), (WIDTH, HUD_HEIGHT), 2)

    # draw current hint
    if not started:
        hint = "Press arrow key to start"
    else:
        hint = f"Dir:({vx},{vy}) Len:{snake_length}"
    hint_txt = font.render(hint, True, HUD_TEXT)
    screen.blit(hint_txt, (WIDTH//2 - hint_txt.get_width()//2, HUD_HEIGHT - hint_txt.get_height() - 6))

    # flip & tick
    pygame.display.flip()
    clock.tick(speed if speed > 0 else 1)

# cleanup & save highscore when quitting
if score > load_highscore():
    save_highscore(score)

pygame.quit()
sys.exit()