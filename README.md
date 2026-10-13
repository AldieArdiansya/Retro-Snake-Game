# 🐍 Pixel Snake // Arcade 1995

A retro 90s arcade-style Snake game built with **Python** and **Pygame**. Inspired by classic arcade cabinets and handheld consoles, featuring phosphor CRT themes, scanlines, chiptune sound effects, power-ups, and smart AI rival snakes!

---

## ✨ Features

- **📺 90s Retro Aesthetic**:
  - CRT scanlines and subtle analog grain noise.
  - Dynamic phosphor CRT color themes that shift as you advance stages.
  - Pixel-art brick borders, checkerboard arena floors, and arcade marquee ticker.
  - Authentic 8-bit typography powered by *Press Start 2P*.
- **🎮 Polished Gameplay**:
  - **No Self-Collision**: Pass freely through your own tail to pull off bold maneuvers.
  - **Smart Rival NPCs**: Dynamic AI-controlled snakes that compete with you for food.
  - **Moving Obstacles & Hazards**: Watch out for shifting obstacles appearing at higher stages.
  - **Streak Multipliers**: Chain consecutive apples to build up streak bonuses.
- **⚡ Power-ups & Bonuses**:
  - `[SPD]` Speed Boost
  - `[FRZ]` Freeze rival NPC snakes
  - `[x2]` Double score multiplier
  - `[+++]` Instant bonus points
  - Golden timed bonus fruit with countdown timer.
- **🔊 Procedural Synthesized Sound**:
  - Pure Python mathematical sound synthesis — **no external audio files required!**
- **💾 Persistent High Score**:
  - Automatically saves and tracks your all-time high score locally.

---

## 🕹️ Controls

| Key | Action |
| :--- | :--- |
| **`W` / `A` / `S` / `D`** | Move Up / Left / Down / Right |
| **`Arrow Keys`** | Alternative Movement |
| **`SPACE`** | Start Game / Play Again |
| **`ESC`** | Return to Main Menu |

---

## 🚀 Installation & Running

### 1. Prerequisites
Ensure you have **Python 3.8+** installed on your system.

### 2. Install Pygame
Install the Pygame library via terminal or command prompt:
```bash
pip install pygame
```

### 3. Run the Game
Clone or download this repository, navigate to the folder, and run:
```bash
python GameSnake.py
```

---

## 📁 Project Structure

```text
├── GameSnake.py        # Main game source code
├── PressStart2P.ttf    # 8-bit arcade font (auto-downloaded on first run)
├── highscore.txt       # Local persistent high score file
└── README.md           # Project documentation
```
