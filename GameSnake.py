import math
import random
import os
import pygame

pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)

# ─── Constants ───────────────────────────────────────────────────────────────
CELL = 20
GRID_SIZE = 30
WIDTH = CELL * GRID_SIZE
HEIGHT = CELL * GRID_SIZE
START_PLAYER_MOVE_MS = 180
MIN_PLAYER_MOVE_MS = 65
PLAYER_SPEEDUP_EVERY_POINTS = 5
PLAYER_SPEEDUP_MS = 4
NPC_MOVE_MS = 180
SCORE_PER_LEVEL = 15
OBSTACLES_PER_LEVEL = 15
HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "highscore.txt")
HUD_SAFE_CELLS = {(x, y) for x in range(12) for y in range(3)}

# Power-up types
PU_SPEED   = "speed"
PU_FREEZE  = "freeze"
PU_DOUBLE  = "double"
PU_BONUS   = "bonus"

POWERUP_COLORS = {
    PU_SPEED:  (60,  210, 255),
    PU_FREEZE: (120, 190, 255),
    PU_DOUBLE: (255, 200,  40),
    PU_BONUS:  (255, 100, 255),
}
POWERUP_LABELS = {
    PU_SPEED:  "SPD",
    PU_FREEZE: "FRZ",
    PU_DOUBLE: "x2 ",
    PU_BONUS:  "+++",
}
POWERUP_DURATION_MS = 6000
POWERUP_SPAWN_CHANCE = 0.20
BONUS_FOOD_DURATION_MS = 5000

# ─── Display ─────────────────────────────────────────────────────────────────
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PIXEL SNAKE // ARCADE 1995")
clock = pygame.time.Clock()

# Font retro — coba muat Press Start 2P, fallback ke Courier New
def _load_retro_font(size):
    try:
        import urllib.request, tempfile, os as _os
        font_path = _os.path.join(_os.path.dirname(__file__), "PressStart2P.ttf")
        if not _os.path.exists(font_path):
            url = "https://github.com/google/fonts/raw/main/ofl/pressstart2p/PressStart2P-Regular.ttf"
            urllib.request.urlretrieve(url, font_path)
        return pygame.font.Font(font_path, size)
    except Exception:
        return pygame.font.SysFont("Courier New", size, bold=True)

hud_font    = _load_retro_font(10)
title_font  = _load_retro_font(28)
mid_font    = _load_retro_font(14)
prompt_font = _load_retro_font(10)
small_font  = _load_retro_font(8)

# ─── Level color themes (phosphor CRT palette) ───────────────────────────────
LEVEL_THEMES = [
    {"phosphor": (0, 14, 4),  "grid": (0, 38, 14),  "border": (60, 255, 100), "inner": (20, 100, 40), "brick": (40, 160, 70)},
    {"phosphor": (0, 4,  18), "grid": (0, 18, 50),  "border": (60, 140, 255), "inner": (20, 50, 140), "brick": (40, 80, 200)},
    {"phosphor": (18, 0, 0),  "grid": (50, 8,  8),  "border": (255, 70, 70),  "inner": (120, 20, 20), "brick": (180, 50, 50)},
    {"phosphor": (12, 0, 18), "grid": (40, 8,  60), "border": (200, 70, 255), "inner": (80, 20, 120), "brick": (140, 50, 200)},
    {"phosphor": (14, 12, 0), "grid": (50, 42, 0),  "border": (255, 220, 40), "inner": (120, 90, 10), "brick": (200, 160, 30)},
]

BRICK_W = CELL       # bata selebar 1 cell
BRICK_H = CELL // 2  # tinggi bata setengah cell

def get_theme(level):
    return LEVEL_THEMES[(level - 1) % len(LEVEL_THEMES)]

def _draw_brick(surf, bx, by, color, shadow):
    """Gambar satu blok bata pixel-art di koordinat piksel (bx, by)."""
    pygame.draw.rect(surf, color,  (bx, by, BRICK_W - 1, BRICK_H - 1))
    pygame.draw.rect(surf, shadow, (bx + 2, by + BRICK_H - 3, BRICK_W - 3, 2))  # bayangan bawah
    pygame.draw.rect(surf, (min(color[0]+60,255), min(color[1]+60,255), min(color[2]+60,255)),
                     (bx + 1, by + 1, BRICK_W - 4, 2))  # highlight atas

def make_background(level):
    theme = get_theme(level)
    bg = pygame.Surface((WIDTH, HEIGHT))
    # Lantai phosphor CRT
    bg.fill(theme["phosphor"])

    # Checkerboard lantai — 2 warna gelap bergantian
    c1 = theme["phosphor"]
    c2 = tuple(min(v + 8, 255) for v in c1)
    for gx in range(1, GRID_SIZE - 1):
        for gy in range(3, GRID_SIZE - 1):  # skip HUD row & border
            col = c1 if (gx + gy) % 2 == 0 else c2
            pygame.draw.rect(bg, col, (gx * CELL + 1, gy * CELL + 1, CELL - 1, CELL - 1))

    # Grid tipis phosphor
    for x in range(0, WIDTH + 1, CELL):
        pygame.draw.line(bg, theme["grid"], (x, 0), (x, HEIGHT))
    for y in range(0, HEIGHT + 1, CELL):
        pygame.draw.line(bg, theme["grid"], (0, y), (WIDTH, y))

    # Dinding bata di tepi arena (baris/kolom 0 dan GRID_SIZE-1)
    bc  = theme["brick"]
    bsh = tuple(max(v - 40, 0) for v in bc)
    # Atas & bawah
    for gx in range(GRID_SIZE):
        _draw_brick(bg, gx * CELL, 0, bc, bsh)
        _draw_brick(bg, gx * CELL, (GRID_SIZE - 1) * CELL, bc, bsh)
    # Kiri & kanan
    for gy in range(1, GRID_SIZE - 1):
        _draw_brick(bg, 0, gy * CELL, bc, bsh)
        _draw_brick(bg, (GRID_SIZE - 1) * CELL, gy * CELL, bc, bsh)

    # Inner border glow
    pygame.draw.rect(bg, theme["border"], (CELL, CELL, WIDTH - 2*CELL, HEIGHT - 2*CELL), 2)
    pygame.draw.rect(bg, theme["inner"],  (CELL + 4, CELL + 4, WIDTH - 2*CELL - 8, HEIGHT - 2*CELL - 8), 1)
    return bg

# Scanlines lebih rapat (tiap 2px) dan lebih gelap — efek CRT kuat
scanlines = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
for _y in range(0, HEIGHT, 2):
    pygame.draw.line(scanlines, (0, 0, 0, 55), (0, _y), (WIDTH, _y))
# ─── Sound synthesis helpers ──────────────────────────────────────────────────
def make_beep(freq=440, duration_ms=80, volume=0.4, wave="square"):
    sample_rate = 44100
    n = int(sample_rate * duration_ms / 1000)
    buf = bytearray(n * 4)
    for i in range(n):
        t = i / sample_rate
        if wave == "square":
            val = 1 if math.sin(2 * math.pi * freq * t) >= 0 else -1
        elif wave == "sine":
            val = math.sin(2 * math.pi * freq * t)
        else:
            val = (2 * ((freq * t) % 1) - 1)
        sample = int(val * 32767 * volume)
        sample = max(-32768, min(32767, sample))
        buf[i*4]   = sample & 0xFF
        buf[i*4+1] = (sample >> 8) & 0xFF
        buf[i*4+2] = sample & 0xFF
        buf[i*4+3] = (sample >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))

def make_chord(freqs, duration_ms=150, volume=0.3):
    sample_rate = 44100
    n = int(sample_rate * duration_ms / 1000)
    buf = bytearray(n * 4)
    for i in range(n):
        t = i / sample_rate
        fade = 1.0 - (i / n) * 0.6
        val = sum(math.sin(2 * math.pi * f * t) for f in freqs) / len(freqs)
        sample = int(val * 32767 * volume * fade)
        sample = max(-32768, min(32767, sample))
        buf[i*4]   = sample & 0xFF
        buf[i*4+1] = (sample >> 8) & 0xFF
        buf[i*4+2] = sample & 0xFF
        buf[i*4+3] = (sample >> 8) & 0xFF
    return pygame.mixer.Sound(buffer=bytes(buf))

snd_eat       = make_beep(660, 60,  0.35, "square")
snd_powerup   = make_chord([523, 659, 784], 200, 0.4)
snd_gameover  = make_chord([220, 165, 110], 400, 0.5)
snd_levelup   = make_chord([523, 659, 784, 1047], 300, 0.4)
snd_bonus_eat = make_chord([880, 1047, 1319], 150, 0.4)

# ─── High score ───────────────────────────────────────────────────────────────
def load_high_score():
    try:
        with open(HIGH_SCORE_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return 0

def save_high_score(hs):
    try:
        with open(HIGH_SCORE_FILE, "w") as f:
            f.write(str(hs))
    except Exception:
        pass

high_score = load_high_score()

# ─── CRT noise grain ────────────────────────────────────────────────────────
_noise_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)

def draw_crt_noise(intensity=18):
    """Taburi noise piksel acak tipis — efek TV analog."""
    _noise_surf.fill((0, 0, 0, 0))
    for _ in range(WIDTH * HEIGHT // 120):
        nx = random.randint(0, WIDTH - 1)
        ny = random.randint(0, HEIGHT - 1)
        a  = random.randint(10, intensity)
        _noise_surf.set_at((nx, ny), (255, 255, 255, a))
    screen.blit(_noise_surf, (0, 0))

# ─── Marquee text ─────────────────────────────────────────────────────────────
MARQUEE_TEXT = (
    "  *** PIXEL SNAKE // ARCADE 1995 ***   "
    "INSERT COIN   HIGH SCORE   WASD TO MOVE   "
    "AVOID WALLS & NPC   GRAB POWER-UPS   "
    "GOOD LUCK PLAYER ONE!   "
)
marquee_x    = float(WIDTH)
MARQUEE_Y    = HEIGHT - 16
MARQUEE_SPD  = 1.5  # piksel per frame

def update_draw_marquee():
    global marquee_x
    surf = small_font.render(MARQUEE_TEXT * 2, True, (80, 255, 120))
    screen.blit(surf, (int(marquee_x), MARQUEE_Y))
    marquee_x -= MARQUEE_SPD
    if marquee_x < -surf.get_width() // 2:
        marquee_x = float(WIDTH)

# ─── Drawing helpers ──────────────────────────────────────────────────────────
# Palet terbatas bergaya Game Boy (4 gradasi) per snake
PALETTE_PLAYER = [(255, 220, 80), (200, 170, 40), (140, 110, 20), (80, 60, 8)]
PALETTE_NPC1   = [(255, 130, 60), (200, 80, 30),  (140, 50, 15),  (80, 25, 5)]
PALETTE_NPC2   = [(80, 230, 230), (40, 160, 170), (20, 100, 120), (10, 60, 80)]

def body_color(index, length, palette=PALETTE_PLAYER):
    """Palet terbatas 4 warna bergaya retro."""
    band = int(index / max(length, 1) * (len(palette) - 1))
    return palette[min(band, len(palette) - 1)]

def draw_pixel_cell(position, color, is_head=False, facing=(1, 0),
                   head_border=None, seg_index=0):
    x, y = position[0] * CELL, position[1] * CELL
    # Outline hitam tebal gaya NES
    pygame.draw.rect(screen, (0, 0, 0), (x + 1, y + 1, CELL - 2, CELL - 2))
    # Highlight terang di sudut kiri-atas (kesan 3D pixel-art)
    hi = tuple(min(c + 70, 255) for c in color)
    sh = tuple(max(c - 60, 0)   for c in color)
    pygame.draw.rect(screen, color, (x + 3, y + 3, CELL - 6, CELL - 6))
    pygame.draw.rect(screen, hi,   (x + 3, y + 3, CELL - 6, 2))   # highlight atas
    pygame.draw.rect(screen, hi,   (x + 3, y + 3, 2, CELL - 6))   # highlight kiri
    pygame.draw.rect(screen, sh,   (x + 3, y + CELL - 5, CELL - 6, 2))  # bayangan bawah
    pygame.draw.rect(screen, sh,   (x + CELL - 5, y + 3, 2, CELL - 6))  # bayangan kanan
    # Ring gelap setiap 4 segmen — pola seperti ular asli
    if not is_head and seg_index % 4 == 0:
        ring = tuple(max(c - 80, 0) for c in color)
        pygame.draw.rect(screen, ring, (x + 4, y + 4, CELL - 8, CELL - 8))
    # Border warna khusus di kepala
    if is_head and head_border:
        pygame.draw.rect(screen, head_border, (x + 1, y + 1, CELL - 2, CELL - 2), 3)
    # Mata
    if is_head:
        if facing[0]:
            eye_x = x + (12 if facing[0] > 0 else 5)
            eyes = ((eye_x, y + 5), (eye_x, y + 12))
        else:
            eye_y = y + (12 if facing[1] > 0 else 5)
            eyes = ((x + 5, eye_y), (x + 12, eye_y))
        for eye in eyes:
            pygame.draw.rect(screen, (0, 0, 0),       (*eye, 4, 4))
            pygame.draw.rect(screen, (255, 246, 190), (eye[0]+1, eye[1]+1, 2, 2))
        # Lidah pixel art — keluar ke arah gerak
        tx = x + CELL // 2 - 1
        ty = y + CELL // 2 - 1
        tdx, tdy = facing[0] * (CELL // 2 - 1), facing[1] * (CELL // 2 - 1)
        tip_x, tip_y = tx + tdx, ty + tdy
        pygame.draw.rect(screen, (255, 50, 80), (tx, ty, 2, 2))          # pangkal lidah
        pygame.draw.rect(screen, (255, 50, 80), (tip_x - 2, tip_y - 2, 2, 2))  # ujung atas
        pygame.draw.rect(screen, (255, 50, 80), (tip_x + 2, tip_y + 2, 2, 2))  # ujung bawah

# Sprite apel 2-frame pixel art (8x8) — dirender sebagai blok 2x2
_APPLE_F0 = [
    "  GGGG  ",
    " RRRRRR ",
    "RRRRRRRR",
    "RRHLRRRR",
    "RRRRRRRR",
    "RRRRRRRR",
    " RRRRRR ",
    "  RRRR  ",
]
_APPLE_F1 = [
    "  GGGG  ",
    " RRRRRR ",
    "RRHRRRR ",
    "RRRRRRRR",
    "RRRRRRRR",
    " RRRRRR ",
    " RRRRRR ",
    "  RRRR  ",
]
_APPLE_COLORS = {
    "R": (220, 50,  50),
    "H": (255, 180, 180),  # highlight
    "L": (160, 20,  20),   # shadow
    "G": (60,  200, 60),   # daun
    " ": None,
}
PX = 2  # ukuran tiap piksel sprite = 2x2 piksel layar

def draw_pixel_food(position, now_ms):
    x, y = position[0] * CELL + 2, position[1] * CELL + 2
    frame = _APPLE_F0 if (now_ms // 300) % 2 == 0 else _APPLE_F1
    for row_i, row in enumerate(frame):
        for col_i, ch in enumerate(row):
            col = _APPLE_COLORS.get(ch)
            if col:
                pygame.draw.rect(screen, col, (x + col_i * PX, y + row_i * PX, PX, PX))
    # Twinkle — kilatan putih kecil di sudut
    twinkle_cycle = (now_ms // 200) % 4
    corners = [(x, y), (x + 14, y), (x, y + 14), (x + 14, y + 14)]
    tw_pos = corners[twinkle_cycle]
    pygame.draw.rect(screen, (255, 255, 255), (*tw_pos, 2, 2))

def draw_bonus_food(position, now_ms, time_left_ms):
    x, y = position[0] * CELL, position[1] * CELL
    pulse = 0.7 + 0.3 * math.sin(now_ms / 80)
    frac  = time_left_ms / BONUS_FOOD_DURATION_MS
    if frac < 0.3 and (now_ms // 200) % 2 == 0:
        return
    r = int(255 * pulse)
    g = int(80  * pulse)
    b = int(200 * pulse)
    pygame.draw.rect(screen, (r, g, b), (x + 3, y + 3, CELL - 6, CELL - 6))
    pygame.draw.rect(screen, (255, 255, 200), (x + 7, y + 7, 6, 6))
    lbl = small_font.render("+5", True, (255, 255, 200))
    screen.blit(lbl, (x + 2, y - 14))

def draw_powerup(position, pu_type, now_ms):
    x, y = position[0] * CELL, position[1] * CELL
    pulse = 0.7 + 0.3 * math.sin(now_ms / 130)
    base  = POWERUP_COLORS[pu_type]
    color = tuple(int(c * pulse) for c in base)
    pygame.draw.rect(screen, (20, 20, 40), (x + 1, y + 1, CELL - 2, CELL - 2))
    pygame.draw.rect(screen, color,         (x + 3, y + 3, CELL - 6, CELL - 6))
    lbl = small_font.render(POWERUP_LABELS[pu_type], True, (255, 255, 255))
    screen.blit(lbl, (x + 1, y + 4))

def draw_obstacle(obstacle):
    x, y = obstacle[0] * CELL, obstacle[1] * CELL
    pygame.draw.rect(screen, (91,  45,  48), (x + 2, y + 2, CELL - 4, CELL - 4))
    pygame.draw.rect(screen, (196, 91,  62), (x + 4, y + 4, CELL - 8, CELL - 8))
    pygame.draw.rect(screen, (242, 164, 82), (x + 5, y + 5, CELL - 10, 3))
    pygame.draw.rect(screen, (91,  45,  48), (x + 8, y + 5, 3, CELL - 10))

# ─── Particles ────────────────────────────────────────────────────────────────
particles = []

def spawn_particles(grid_pos, color, count=12):
    cx = grid_pos[0] * CELL + CELL // 2
    cy = grid_pos[1] * CELL + CELL // 2
    for _ in range(count):
        angle = random.uniform(0, 2 * math.pi)
        speed = random.uniform(1.5, 5.0)
        particles.append([
            cx, cy,
            math.cos(angle) * speed,
            math.sin(angle) * speed,
            random.randint(18, 30),
            color,
        ])

def update_draw_particles():
    for p in particles[:]:
        p[0] += p[2]
        p[1] += p[3]
        p[3] += 0.18
        p[4] -= 1
        if p[4] <= 0:
            particles.remove(p)
        else:
            r, g, b = p[5]
            pygame.draw.rect(screen, (min(r, 255), min(g, 255), min(b, 255)),
                             (int(p[0]), int(p[1]), 4, 4))

# ─── Flash effect ─────────────────────────────────────────────────────────────
flash_surface = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
flash_frames  = 0
flash_color   = (255, 50, 50, 120)

def trigger_flash(color=(255, 50, 50, 120), frames=12):
    global flash_frames, flash_color
    flash_frames = frames
    flash_color  = color

def draw_flash():
    global flash_frames
    if flash_frames > 0:
        flash_surface.fill(flash_color)
        screen.blit(flash_surface, (0, 0))
        flash_frames -= 1

# ─── Floating text ────────────────────────────────────────────────────────────
float_texts = []

def spawn_float_text(text, grid_pos, color=(255, 255, 100), frames=40):
    float_texts.append([text, grid_pos[0] * CELL, grid_pos[1] * CELL, frames, color])

def draw_float_texts():
    for ft in float_texts[:]:
        alpha = min(255, int(255 * ft[3] / 40))
        surf = small_font.render(ft[0], True, ft[4])
        surf.set_alpha(alpha)
        screen.blit(surf, (ft[1], ft[2]))
        ft[2] -= 1.2
        ft[3] -= 1
        if ft[3] <= 0:
            float_texts.remove(ft)

# ─── Level-up banner ─────────────────────────────────────────────────────────
levelup_frames = 0
levelup_text   = ""

def trigger_levelup(level):
    global levelup_frames, levelup_text
    levelup_frames = 90
    levelup_text   = f"STAGE {level:02d}!"

def draw_levelup():
    global levelup_frames
    if levelup_frames > 0:
        t = levelup_frames / 90
        scale = 1.0 + 0.4 * math.sin(t * math.pi)
        size  = int(36 * scale)
        font  = pygame.font.SysFont("Courier New", size, bold=True)
        alpha = int(255 * min(1, t * 3))
        surf  = font.render(levelup_text, True, (255, 230, 60))
        surf.set_alpha(alpha)
        rect  = surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 60))
        screen.blit(surf, rect)
        levelup_frames -= 1

# ─── HUD ──────────────────────────────────────────────────────────────────────
score_bounce = 0

def draw_hud(score, level, high_score, active_powerups):
    global score_bounce
    theme = get_theme(level)
    hud_area = pygame.Rect(0, 0, 12 * CELL, 3 * CELL)
    pygame.draw.rect(screen, (8, 11, 22), hud_area)
    hud_panel = pygame.Rect(8, 8, 224, 48)
    pygame.draw.rect(screen, (6, 9, 18),     hud_panel)
    pygame.draw.rect(screen, theme["border"], hud_panel, width=3)
    pygame.draw.rect(screen, theme["inner"],  hud_panel.inflate(-8, -8), width=1)

    score_bounce = max(0, score_bounce - 1)
    bounce_off = int(math.sin(score_bounce / 5 * math.pi) * 4) if score_bounce > 0 else 0

    score_text = hud_font.render(f"SCORE {score:04d}", True, (255, 226, 116))
    level_text = hud_font.render(f"STAGE {level:02d} // WASD", True, (113, 238, 139))
    screen.blit(score_text, (16, 12 - bounce_off))
    screen.blit(level_text, (16, 32))

    hs_text = small_font.render(f"BEST:{high_score:04d}", True, (200, 160, 60))
    screen.blit(hs_text, (16 + 224 - 10, 12))

    px = 16
    for pu_type, end_time in active_powerups.items():
        time_left = end_time - pygame.time.get_ticks()
        frac = max(0, time_left / POWERUP_DURATION_MS)
        bar_w = int(60 * frac)
        color = POWERUP_COLORS[pu_type]
        lbl = small_font.render(POWERUP_LABELS[pu_type], True, color)
        screen.blit(lbl, (px, 52))
        pygame.draw.rect(screen, (30, 30, 50), (px, 66, 60, 5))
        pygame.draw.rect(screen, color,        (px, 66, bar_w, 5))
        px += 72

# ─── Grid helpers ─────────────────────────────────────────────────────────────
def random_food(occupied):
    occupied = set(occupied) | HUD_SAFE_CELLS
    empty = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) if (x, y) not in occupied]
    return random.choice(empty) if empty else None

def create_obstacles(occupied):
    occupied = set(occupied) | HUD_SAFE_CELLS
    available = [(x, y) for x in range(GRID_SIZE) for y in range(GRID_SIZE) if (x, y) not in occupied]
    count = min(OBSTACLES_PER_LEVEL, len(available))
    return random.sample(available, count)

def create_npc(occupied):
    occupied = set(occupied) | HUD_SAFE_CELLS
    possible = []
    for y in range(3, GRID_SIZE):
        for x in range(GRID_SIZE):
            segs = [((x - o) % GRID_SIZE, y) for o in range(3)]
            if not any(s in occupied for s in segs):
                possible.append(segs)
    return random.choice(possible) if possible else []

# ─── NPC smart move ───────────────────────────────────────────────────────────
def npc_best_direction(npc_snake, npc_direction, food, obstacles, snake):
    dirs = [(0, -1), (1, 0), (0, 1), (-1, 0)]
    opposite = (-npc_direction[0], -npc_direction[1])
    random.shuffle(dirs)
    blocked = set(obstacles) | set(npc_snake[:-1]) | HUD_SAFE_CELLS
    hx, hy = npc_snake[0]

    def score_dir(d):
        if d == opposite:
            return 9999
        nx, ny = hx + d[0], hy + d[1]
        if nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
            return 9000
        if (nx, ny) in blocked:
            return 8000
        if food:
            return abs(nx - food[0]) + abs(ny - food[1])
        return 0

    dirs.sort(key=score_dir)
    for d in dirs:
        nx, ny = hx + d[0], hy + d[1]
        if (nx, ny) in blocked or nx < 0 or nx >= GRID_SIZE or ny < 0 or ny >= GRID_SIZE:
            continue
        return d, (nx, ny)
    return None, None

# ─── Moving obstacles ─────────────────────────────────────────────────────────
def create_moving_obstacles(occupied, count=5):
    occupied = set(occupied) | HUD_SAFE_CELLS
    available = [(x, y) for x in range(3, GRID_SIZE - 3) for y in range(3, GRID_SIZE - 3)
                 if (x, y) not in occupied]
    movers = []
    for pos in random.sample(available, min(count, len(available))):
        vel = random.choice([(1, 0), (-1, 0), (0, 1), (0, -1)])
        movers.append([list(pos), vel, pygame.time.get_ticks(), random.randint(300, 600)])
    return movers

def update_moving_obstacles(moving_obstacles, snake, npc_all, static_obstacles, now):
    all_blocked = set(snake) | set(npc_all) | set(static_obstacles) | HUD_SAFE_CELLS
    for mo in moving_obstacles:
        pos, vel = mo[0], mo[1]
        if now - mo[2] >= mo[3]:
            mo[2] = now
            nx = pos[0] + vel[0]
            ny = pos[1] + vel[1]
            if nx <= 0 or nx >= GRID_SIZE - 1 or ny <= 0 or ny >= GRID_SIZE - 1 or (nx, ny) in all_blocked:
                mo[1] = (-vel[0], -vel[1])
            else:
                mo[0] = [nx, ny]

def moving_obs_positions(moving_obstacles):
    return [(mo[0][0], mo[0][1]) for mo in moving_obstacles]

# ─── Game state ───────────────────────────────────────────────────────────────
def reset_game():
    global snake, direction, obstacles, moving_obstacles, npc_snake, npc_snake2
    global npc_direction, npc_direction2, food, bonus_food, bonus_food_timer
    global powerup_item, powerup_type, score, level, game_over
    global last_player_move, last_npc_move, last_npc2_move, active_powerups
    global streak, score_bounce, background, particles, float_texts
    global flash_frames, levelup_frames

    snake            = [(15, 15), (14, 15), (13, 15)]
    direction        = (1, 0)
    obstacles        = []
    moving_obstacles = []
    npc_snake        = []
    npc_snake2       = []
    npc_direction    = (1, 0)
    npc_direction2   = (-1, 0)
    food             = random_food(snake)
    bonus_food       = None
    bonus_food_timer = 0
    powerup_item     = None
    powerup_type     = None
    score            = 0
    level            = 1
    game_over        = False
    active_powerups  = {}
    streak           = 0
    score_bounce     = 0
    particles.clear()
    float_texts.clear()
    flash_frames     = 0
    levelup_frames   = 0
    background       = make_background(1)
    t = pygame.time.get_ticks()
    last_player_move = t
    last_npc_move    = t
    last_npc2_move   = t

# Initial state
snake            = [(15, 15), (14, 15), (13, 15)]
direction        = (1, 0)
obstacles        = []
moving_obstacles = []
npc_snake        = []
npc_snake2       = []
npc_direction    = (1, 0)
npc_direction2   = (-1, 0)
food             = random_food(snake)
bonus_food       = None
bonus_food_timer = 0
powerup_item     = None
powerup_type     = None
score            = 0
level            = 1
game_over        = False
active_powerups  = {}
streak           = 0
score_bounce     = 0
background       = make_background(1)
particles        = []
float_texts      = []
flash_frames     = 0
levelup_frames   = 0
running          = True
game_state       = "menu"
menu_anim        = 0.0

last_player_move = pygame.time.get_ticks()
last_npc_move    = last_player_move
last_npc2_move   = last_player_move

# ─── Main loop ────────────────────────────────────────────────────────────────
while running:
    now = pygame.time.get_ticks()
    menu_anim += 0.03

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if game_state == "menu":
                if event.key == pygame.K_SPACE:
                    reset_game()
                    game_state = "playing"
            elif game_state == "gameover":
                if event.key == pygame.K_SPACE:
                    reset_game()
                    game_state = "playing"
                elif event.key == pygame.K_ESCAPE:
                    game_state = "menu"
            elif game_state == "playing":
                if event.key == pygame.K_w and direction != (0, 1):
                    direction = (0, -1)
                elif event.key == pygame.K_s and direction != (0, -1):
                    direction = (0, 1)
                elif event.key == pygame.K_a and direction != (1, 0):
                    direction = (-1, 0)
                elif event.key == pygame.K_d and direction != (-1, 0):
                    direction = (1, 0)

    # ── MENU ──────────────────────────────────────────────────────────────────
    if game_state == "menu":
        screen.fill((4, 6, 15))
        for xi in range(0, WIDTH + 1, CELL):
            alpha = int(128 + 80 * math.sin(menu_anim + xi / 60))
            pygame.draw.line(screen, (0, alpha // 6, alpha // 4), (xi, 0), (xi, HEIGHT))
        for yi in range(0, HEIGHT + 1, CELL):
            alpha = int(128 + 80 * math.sin(menu_anim + yi / 60))
            pygame.draw.line(screen, (0, alpha // 6, alpha // 4), (0, yi), (WIDTH, yi))

        glow_col = (
            int(60 + 40 * math.sin(menu_anim)),
            int(200 + 35 * math.sin(menu_anim * 0.7)),
            int(100 + 30 * math.sin(menu_anim * 1.3)),
        )
        for off in range(4, 0, -1):
            t_surf = title_font.render("PIXEL SNAKE", True,
                                       (glow_col[0]//off, glow_col[1]//off, glow_col[2]//off))
            r = t_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80))
            screen.blit(t_surf, r.move(-off, 0))
            screen.blit(t_surf, r.move(off, 0))
        t_surf = title_font.render("PIXEL SNAKE", True, glow_col)
        screen.blit(t_surf, t_surf.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 80)))

        sub = mid_font.render("// ARCADE 1995 //", True, (90, 180, 120))
        screen.blit(sub, sub.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 20)))

        if (now // 500) % 2 == 0:
            sp = mid_font.render("TEKAN SPASI UNTUK MULAI", True, (255, 226, 91))
            screen.blit(sp, sp.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 50)))

        ctrls = ["[ W A S D ] — GERAK", "[ SPASI ]  — RESTART", "[ ESC ]    — MENU"]
        for i, c in enumerate(ctrls):
            cs = small_font.render(c, True, (70, 120, 90))
            screen.blit(cs, cs.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 110 + i * 22)))

        hs_s = prompt_font.render(f"REKOR TERBAIK: {high_score:04d}", True, (200, 160, 60))
        screen.blit(hs_s, hs_s.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 200)))

        screen.blit(scanlines, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── GAME OVER ─────────────────────────────────────────────────────────────
    if game_state == "gameover":
        screen.blit(background, (0, 0))
        draw_hud(score, level, high_score, active_powerups)
        panel = pygame.Rect(60, HEIGHT // 2 - 90, WIDTH - 120, 180)
        pygame.draw.rect(screen, (4, 6, 15), panel.move(6, 6))
        pygame.draw.rect(screen, (20, 24, 38), panel)
        pygame.draw.rect(screen, (89, 235, 120), panel, width=4)
        pygame.draw.rect(screen, (37, 89, 63), panel.inflate(-12, -12), width=2)

        title_s  = title_font.render("GAME OVER", True, (255, 112, 100))
        score_s  = mid_font.render(f"SKOR: {score:04d}", True, (255, 226, 116))
        is_new   = score >= high_score and score > 0
        hs_label = mid_font.render(
            "* REKOR BARU! *" if is_new else f"REKOR: {high_score:04d}",
            True, (255, 220, 50) if is_new else (160, 130, 60)
        )
        prompt_s = prompt_font.render("SPASI=ULANG   ESC=MENU", True, (113, 238, 139))
        screen.blit(title_s,  title_s.get_rect(center=(WIDTH//2, HEIGHT//2 - 55)))
        screen.blit(score_s,  score_s.get_rect(center=(WIDTH//2, HEIGHT//2 - 5)))
        screen.blit(hs_label, hs_label.get_rect(center=(WIDTH//2, HEIGHT//2 + 38)))
        screen.blit(prompt_s, prompt_s.get_rect(center=(WIDTH//2, HEIGHT//2 + 78)))

        screen.blit(scanlines, (0, 0))
        pygame.display.flip()
        clock.tick(60)
        continue

    # ── PLAYING ───────────────────────────────────────────────────────────────
    expired = [k for k, v in active_powerups.items() if now >= v]
    for k in expired:
        del active_powerups[k]

    speed_factor = 0.55 if PU_SPEED in active_powerups else 1.0
    npc_frozen   = PU_FREEZE in active_powerups
    score_mult   = 2 if PU_DOUBLE in active_powerups else 1

    player_move_ms = max(
        MIN_PLAYER_MOVE_MS,
        int((START_PLAYER_MOVE_MS - (score // PLAYER_SPEEDUP_EVERY_POINTS) * PLAYER_SPEEDUP_MS) * speed_factor),
    )

    if now - last_player_move >= player_move_ms:
        last_player_move = now
        head_x, head_y  = snake[0]
        new_head         = (head_x + direction[0], head_y + direction[1])
        all_moving       = moving_obs_positions(moving_obstacles)
        eating           = new_head == food
        eating_bonus     = bonus_food is not None and new_head == bonus_food
        eating_pu        = powerup_item is not None and new_head == powerup_item

        if (
            new_head[0] < 0 or new_head[0] >= GRID_SIZE
            or new_head[1] < 0 or new_head[1] >= GRID_SIZE
            or new_head in obstacles
            or new_head in all_moving
            or new_head in npc_snake
            or new_head in npc_snake2
            or new_head in HUD_SAFE_CELLS
        ):
            game_over = True
            trigger_flash((255, 50, 50, 140), 18)
            snd_gameover.play()
            if score > high_score:
                high_score = score
                save_high_score(high_score)
        else:
            snake.insert(0, new_head)

            if eating_pu:
                active_powerups[powerup_type] = now + POWERUP_DURATION_MS
                spawn_particles(new_head, POWERUP_COLORS[powerup_type], 20)
                spawn_float_text(f"[{POWERUP_LABELS[powerup_type].strip()}!]", new_head, POWERUP_COLORS[powerup_type])
                snd_powerup.play()
                powerup_item = None
                powerup_type = None
                snake.pop()

            elif eating_bonus:
                bonus_pts = 5 * score_mult
                score += bonus_pts
                streak += 1
                score_bounce = 10
                spawn_particles(new_head, (255, 80, 255), 18)
                spawn_float_text(f"+{bonus_pts}", new_head, (255, 80, 255))
                snd_bonus_eat.play()
                bonus_food = None
                bonus_food_timer = 0

            elif eating:
                pts = 1 * score_mult
                if streak >= 3:
                    pts += streak // 3
                    spawn_float_text(f"STREAK x{streak}!", new_head, (255, 220, 60))
                score += pts
                streak += 1
                score_bounce = 10
                spawn_particles(new_head, (255, 226, 91), 12)
                spawn_float_text(f"+{pts}", new_head, (255, 240, 80))
                snd_eat.play()

                new_level = score // SCORE_PER_LEVEL + 1
                if new_level != level:
                    level = new_level
                    background = make_background(level)
                    snd_levelup.play()
                    trigger_flash((60, 120, 255, 80), 14)
                    trigger_levelup(level)
                    if level == 2:
                        obstacles = create_obstacles(snake)
                    elif level == 3:
                        npc_snake = create_npc(snake + obstacles)
                        obstacles.extend(create_obstacles(snake + obstacles + npc_snake))
                        npc_direction = (1, 0)
                        last_npc_move = now
                    elif level == 4:
                        moving_obstacles = create_moving_obstacles(
                            snake + obstacles + npc_snake, count=6)
                    elif level >= 5 and not npc_snake2:
                        npc_snake2 = create_npc(
                            snake + obstacles + npc_snake + moving_obs_positions(moving_obstacles))
                        npc_direction2 = (-1, 0)
                        last_npc2_move = now

                occ = snake + obstacles + npc_snake + npc_snake2 + moving_obs_positions(moving_obstacles)
                food = random_food(occ)

                if bonus_food is None and random.random() < 0.25:
                    bf_occ = list(set(occ) | ({food} if food else set()))
                    bonus_food = random_food(bf_occ)
                    bonus_food_timer = now + BONUS_FOOD_DURATION_MS

                if powerup_item is None and random.random() < POWERUP_SPAWN_CHANCE:
                    pu_occ = list(set(occ) | ({food} if food else set()) | ({bonus_food} if bonus_food else set()))
                    ppos = random_food(pu_occ)
                    if ppos:
                        powerup_item = ppos
                        powerup_type = random.choice([PU_SPEED, PU_FREEZE, PU_DOUBLE, PU_BONUS])
            else:
                streak = 0
                snake.pop()

            if food is None:
                game_over = True

    if bonus_food is not None and now > bonus_food_timer:
        bonus_food = None
        bonus_food_timer = 0

    # NPC 1
    if not npc_frozen and level >= 3 and npc_snake and now - last_npc_move >= NPC_MOVE_MS:
        last_npc_move = now
        nd, nh = npc_best_direction(npc_snake, npc_direction, food,
                                    obstacles + moving_obs_positions(moving_obstacles), snake)
        if nd is not None and nh is not None:
            if nh == snake[0]:
                game_over = True
                trigger_flash((255, 50, 50, 140), 18)
                snd_gameover.play()
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
            else:
                npc_direction = nd
                npc_snake.insert(0, nh)
                npc_snake.pop()
                if bonus_food and bonus_food in npc_snake:
                    bonus_food = None
                if food in npc_snake:
                    food = random_food(snake + obstacles + npc_snake)

    # NPC 2
    if not npc_frozen and level >= 5 and npc_snake2 and now - last_npc2_move >= NPC_MOVE_MS:
        last_npc2_move = now
        nd2, nh2 = npc_best_direction(npc_snake2, npc_direction2, food,
                                      obstacles + moving_obs_positions(moving_obstacles), snake)
        if nd2 is not None and nh2 is not None:
            if nh2 == snake[0]:
                game_over = True
                trigger_flash((255, 50, 50, 140), 18)
                snd_gameover.play()
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
            else:
                npc_direction2 = nd2
                npc_snake2.insert(0, nh2)
                npc_snake2.pop()
                if food in npc_snake2:
                    food = random_food(snake + obstacles + npc_snake + npc_snake2)

    update_moving_obstacles(moving_obstacles, snake, npc_snake + npc_snake2, obstacles, now)

    if game_over:
        game_state = "gameover"

    # ── DRAW ──────────────────────────────────────────────────────────────────
    screen.blit(background, (0, 0))

    for ob in obstacles:
        draw_obstacle(ob)

    for mo in moving_obstacles:
        mx, my = mo[0][0], mo[0][1]
        px, py = mx * CELL, my * CELL
        pygame.draw.rect(screen, (60, 200, 255), (px + 2, py + 2, CELL - 4, CELL - 4))
        pygame.draw.rect(screen, (20,  80, 140), (px + 5, py + 5, CELL - 10, CELL - 10))
        vel = mo[1]
        ax, ay = px + CELL // 2, py + CELL // 2
        pygame.draw.polygon(screen, (180, 240, 255), [
            (ax + vel[0]*6,  ay + vel[1]*6),
            (ax - vel[1]*3 - vel[0]*3, ay + vel[0]*3 - vel[1]*3),
            (ax + vel[1]*3 - vel[0]*3, ay - vel[0]*3 - vel[1]*3),
        ])

    # Badan dulu (tanpa kepala), lalu kepala digambar terakhir agar selalu di atas
    for i, segment in enumerate(snake):
        if i == 0:
            continue
        draw_pixel_cell(segment, body_color(i, len(snake), PALETTE_PLAYER),
                        False, direction, seg_index=i)
    if snake:
        draw_pixel_cell(snake[0], PALETTE_PLAYER[0], True, direction,
                        head_border=(255, 255, 180), seg_index=0)  # border putih-emas

    for i, segment in enumerate(npc_snake):
        if i == 0:
            continue
        draw_pixel_cell(segment, body_color(i, len(npc_snake), PALETTE_NPC1),
                        False, npc_direction, seg_index=i)
    if npc_snake:
        draw_pixel_cell(npc_snake[0], PALETTE_NPC1[0], True, npc_direction,
                        head_border=(80, 255, 80), seg_index=0)    # border hijau-lime

    for i, segment in enumerate(npc_snake2):
        if i == 0:
            continue
        draw_pixel_cell(segment, body_color(i, len(npc_snake2), PALETTE_NPC2),
                        False, npc_direction2, seg_index=i)
    if npc_snake2:
        draw_pixel_cell(npc_snake2[0], PALETTE_NPC2[0], True, npc_direction2,
                        head_border=(255, 60, 220), seg_index=0)   # border magenta

    if food is not None:
        draw_pixel_food(food, now)

    if bonus_food is not None:
        draw_bonus_food(bonus_food, now, bonus_food_timer - now)

    if powerup_item is not None:
        draw_powerup(powerup_item, powerup_type, now)

    update_draw_particles()
    draw_float_texts()
    draw_levelup()
    draw_flash()
    draw_hud(score, level, high_score, active_powerups)
    screen.blit(scanlines, (0, 0))   # scanlines CRT
    update_draw_marquee()             # teks berjalan bawah
    draw_crt_noise(14)                # grain analog
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
