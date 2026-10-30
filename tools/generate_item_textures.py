#!/usr/bin/env python3
"""Genera le texture 16x16 degli oggetti della mod e degli sprite dei proiettili.

Solo libreria standard. Si lancia dalla radice del progetto:
    python3 tools/generate_item_textures.py
Oggetti ridisegnati: Freccia dello Stand, Pergamena dell'Hamon, Pergamena dello Spin,
Manuale di Pugilato, Maschera di Pietra, Pietra Rossa di Aja.
Sprite dei proiettili degli Stand (oggetti nascosti): coltello, stella, cerniera.
"""
import math
from pathlib import Path

from generate_textures import ASSETS, C, glyph, m_glove, m_spiral, m_star, m_sun, write_png

ITEM_DIR = ASSETS / 'textures/item'
CLEAR = (0, 0, 0, 0)


class Canvas:
    def __init__(self, n=16):
        self.n = n
        self.p = [[CLEAR] * n for _ in range(n)]

    def set(self, x, y, c):
        if 0 <= x < self.n and 0 <= y < self.n:
            self.p[y][x] = c

    def get(self, x, y):
        return self.p[y][x] if 0 <= x < self.n and 0 <= y < self.n else CLEAR

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.set(x, y, c)

    def line(self, x0, y0, x1, y1, c):
        steps = max(abs(x1 - x0), abs(y1 - y0))
        for i in range(steps + 1):
            t = i / steps if steps else 0
            self.set(round(x0 + (x1 - x0) * t), round(y0 + (y1 - y0) * t), c)

    def outline(self, color):
        """Contorno di 1 pixel attorno a tutto cio' che e' stato disegnato (stile oggetti vanilla)."""
        add = []
        for y in range(self.n):
            for x in range(self.n):
                if self.p[y][x][3] != 0:
                    continue
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    if self.get(x + dx, y + dy)[3] != 0:
                        add.append((x, y))
                        break
        for x, y in add:
            self.p[y][x] = color

    def stamp(self, rows, x0, y0, palette):
        """Disegna un simbolo da una griglia di caratteri; '.' lascia il pixel com'e'."""
        for yy, row in enumerate(rows):
            for xx, ch in enumerate(row):
                if ch in palette:
                    self.set(x0 + xx, y0 + yy, palette[ch])

    def emblem(self, mask_fn, x0, y0, size, color):
        """Disegna un simbolo (maschera 16x16 delle icone dell'HUD) ridotto a size x size."""
        k = 16.0 / size
        for yy in range(size):
            for xx in range(size):
                if mask_fn((xx + 0.5) * k, (yy + 0.5) * k):
                    self.set(x0 + xx, y0 + yy, color)


OUT = C(34, 24, 36)

SUN8 = [
    "...XX...",
    ".X.XX.X.",
    "..XXXX..",
    "XXXXXXXX",
    "XXXXXXXX",
    "..XXXX..",
    ".X.XX.X.",
    "...XX...",
]
SPIRAL8 = [
    "XXXXXXX.",
    "X.....X.",
    "X.XXX.X.",
    "X.X.X.X.",
    "X.X.XXX.",
    "X.X.....",
    "X.XXXXXX",
    "X.......",
]
GLOVE6 = [
    ".WWWW.",
    "WWWWWW",
    "WWWWWW",
    "WWWWWW",
    "WWWWW.",
    ".WWWW.",
    ".GGGG.",
    ".GGGG.",
]


# ---------------------------------------------------------------- Freccia dello Stand
# ---------------------------------------------------------------- Pergamene e manuale
def scroll(accent, accent_d, symbol_rows, emblem_color):
    c = Canvas()
    paper, paper_d, rod, rod_d = C(240, 226, 182), C(206, 184, 132), C(128, 84, 46), C(86, 54, 30)
    # bastoni in alto e in basso
    for y0 in (1, 12):
        c.rect(1, y0, 14, y0 + 2, rod)
        c.rect(1, y0 + 2, 14, y0 + 2, rod_d)
        c.rect(0, y0, 0, y0 + 2, accent)
        c.rect(15, y0, 15, y0 + 2, accent)
        c.rect(0, y0 + 2, 0, y0 + 2, accent_d)
        c.rect(15, y0 + 2, 15, y0 + 2, accent_d)
    # pergamena
    c.rect(2, 4, 13, 11, paper)
    c.rect(2, 4, 2, 11, paper_d)
    c.rect(13, 4, 13, 11, paper_d)
    c.rect(2, 10, 13, 11, paper_d)
    c.rect(2, 4, 13, 4, paper_d)
    # simbolo centrale ridotto
    c.stamp(symbol_rows, 4, 4, {'X': emblem_color})
    c.outline(OUT)
    return c.p


def boxing_manual():
    c = Canvas()
    cover, cover_d, cover_l = C(188, 40, 44), C(124, 22, 30), C(226, 84, 80)
    page, page_d, gold = C(244, 236, 212), C(206, 194, 164), C(240, 196, 72)
    c.rect(2, 1, 12, 14, cover)                      # copertina
    c.rect(2, 1, 3, 14, cover_d)                     # dorso
    c.rect(4, 1, 12, 1, cover_l)
    c.rect(13, 2, 14, 14, page)                      # pagine a destra
    c.rect(13, 2, 13, 14, page_d)
    c.rect(3, 14, 12, 14, page_d)
    c.rect(4, 2, 11, 2, gold)                        # cornice dorata
    c.rect(4, 13, 11, 13, gold)
    c.rect(4, 2, 4, 13, gold)
    c.rect(11, 2, 11, 13, gold)
    c.rect(5, 3, 10, 12, cover)
    c.stamp(GLOVE6, 5, 4, {'W': C(255, 255, 255), 'G': gold})
    c.rect(2, 4, 3, 4, gold)                         # fascette sul dorso
    c.rect(2, 11, 3, 11, gold)
    c.outline(OUT)
    return c.p


# ---------------------------------------------------------------- Maschera di Pietra
# ---------------------------------------------------------------- Pietra Rossa di Aja
RUBY = [
    "................",
    "................",
    ".....KKKKKK.....",
    "....KLLLLMMK....",
    "...KLWLLLMMMK...",
    "..KLLLLLMMMMMK..",
    "..KKKKKKKKKKKK..",
    "..KLLMMMMMMDDK..",
    "...KLMMMMMMDK...",
    "...KMMMMMMDDK...",
    "....KMMMMDDK....",
    "....KMMMDDDK....",
    ".....KMMDDK.....",
    "......KDDK......",
    ".......KK.......",
    "................",
]


def red_stone():
    pal = {'K': C(70, 8, 20), 'D': C(142, 16, 34), 'M': C(214, 34, 52), 'L': C(255, 104, 112),
           'W': C(255, 238, 236), 'O': C(255, 176, 130)}
    rows = []
    for line in RUBY:
        assert len(line) == 16, line
        rows.append([pal.get(ch, CLEAR) for ch in line])
    # riflesso arancione e scintilla
    rows[3][5] = pal['O']
    rows[9][5] = pal['L']
    return rows


# ---------------------------------------------------------------- sprite dei proiettili
def projectile_knife():
    c = Canvas()
    blade, blade_d, white = C(214, 224, 238), C(136, 150, 176), C(255, 255, 255)
    handle, handle_d, gold = C(70, 50, 38), C(44, 30, 22), C(236, 190, 70)
    for i in range(7):                               # lama verso l'alto a destra
        x, y = 7 + i, 8 - i
        c.set(x, y, blade)
        c.set(x + 1, y, blade_d)
        if i in (2, 3):
            c.set(x, y, white)
    c.set(14, 1, white)
    c.set(15, 0, blade_d)
    for (x, y) in ((6, 9), (7, 9), (5, 8), (6, 8), (7, 10), (6, 10)):   # guardia
        c.set(x, y, gold)
    for i in range(4):                               # impugnatura
        x, y = 5 - i, 10 + i
        c.set(x, y, handle)
        c.set(x + 1, y, handle_d)
    c.outline(OUT)
    return c.p


def projectile_star():
    return glyph(m_star, fill=C(226, 196, 255), outline=C(88, 52, 150, 255))


def projectile_zip():
    c = Canvas()
    blue, blue_d, white, gold = C(66, 130, 232), C(38, 88, 184), C(246, 246, 252), C(244, 204, 76)
    for i in range(11):                              # nastro diagonale con denti
        x, y = 2 + i, 12 - i
        c.set(x, y, blue)
        c.set(x + 1, y, blue_d)
        c.set(x + (i % 2), y - 1 + (i % 2) * 2, white)
    c.rect(11, 2, 13, 4, gold)                       # cursore
    c.set(12, 3, C(60, 44, 20))
    c.outline(OUT)
    return c.p


# ---------------------------------------------------------------- Oggetti a 32x32 (piu' dettagliati)
def _noise(x, y, k=5):
    return (((x * 73856093) ^ (y * 19349663)) % (2 * k + 1)) - k


def steel_ball():
    """Sfera d'acciaio: acciaio lucido con riflesso e spirale aurea dorata incisa."""
    c = Canvas(32)
    R = 14.4
    for y in range(32):
        for x in range(32):
            dx, dy = x + 0.5 - 16.0, y + 0.5 - 16.0
            d = math.hypot(dx, dy)
            if d > R:
                continue
            nx, ny = dx / R, dy / R
            nz = math.sqrt(max(0.0, 1 - nx * nx - ny * ny))
            lam = max(0.0, nx * -0.5 + ny * -0.6 + nz * 0.62)
            spec = max(0.0, nx * -0.35 + ny * -0.45 + nz * 0.82) ** 18 * 130
            v = max(0, min(255, 62 + 165 * lam + spec - (d / R) ** 6 * 38 + _noise(x, y, 2)))
            c.set(x, y, C(int(v) - 8 if v > 8 else 0, int(v), min(255, int(v) + 16)))
    # spirale logaritmica (tre giri circa, come l'incisione della sfera): solco scuro + filo d'oro
    pts = []
    for i in range(0, 1800):
        t = i * 0.01
        r = 1.0 * math.exp(0.155 * t)
        if r > R - 1.8:
            break
        ang = t + 0.6
        pts.append((16.0 + r * math.cos(ang), 16.0 + r * math.sin(ang)))
    for (px, py) in pts:
        c.set(int(px) + 1, int(py) + 1, C(70, 48, 18))
    for (px, py) in pts:
        c.set(int(px), int(py), C(244, 202, 80))
    for (px, py) in pts[::7]:
        c.set(int(px), int(py), C(255, 238, 150))
    c.set(15, 15, C(244, 202, 80))
    c.set(16, 15, C(244, 202, 80))
    c.set(15, 16, C(170, 120, 36))
    for (x, y) in ((8, 7), (9, 7), (8, 8), (7, 9)):          # riflesso principale
        c.set(x, y, C(255, 255, 255))
    c.outline(OUT)
    return c.p


def _hw(y):
    """Mezza larghezza del volto della Maschera di Pietra alla quota y (cupola larga, mento stretto)."""
    t = (y - 2.0) / 28.0
    if t < 0 or t > 1:
        return 0.0
    if t < 0.30:
        return 12.6 * math.sqrt(max(0.0, 1 - ((0.30 - t) / 0.30) ** 2))
    return 12.6 * math.sqrt(max(0.0, 1 - ((t - 0.30) / 0.70) ** 1.7)) + 1.5 * (1 - t)


def stone_mask():
    """Maschera di Pietra: volto di pietra pallida con arcate sopracciliari, occhi incavati, naso,
    bocca severa, incisioni sulle guance e le punte che escono dai bordi."""
    c = Canvas(32)
    cx = 15.5
    stone, light, dark = (208, 202, 188), (236, 232, 220), (112, 104, 92)
    for y in range(2, 31):
        w = _hw(y + 0.5)
        for x in range(32):
            u = (x + 0.5 - cx)
            if abs(u) > w:
                continue
            k = 1.08 - 0.32 * ((u / max(w, 1)) + 1) / 2            # luce da sinistra
            k -= max(0.0, (y - 22) / 40.0)                         # piu' scuro verso il mento
            v = _noise(x, y, 5)
            c.set(x, y, C(int(min(255, stone[0] * k + v)), int(min(255, stone[1] * k + v)),
                          int(min(255, stone[2] * k + v))))
    # punte sui bordi (la maschera ha gli spuntoni che penetrano nel cranio)
    for yy in (10, 16, 22):
        w = _hw(yy + 0.5)
        for side in (-1, 1):
            ex = cx + side * w
            for step in range(5):
                half = max(0, 1 - step // 2)
                for dyy in range(-half, half + 1):
                    c.set(int(ex + side * (step + 0.5)), yy + dyy, C(*light))
    # incisione a losanga sulla fronte
    for (x, y) in ((15, 6), (16, 6), (14, 7), (17, 7), (13, 8), (18, 8), (14, 9), (17, 9), (15, 10), (16, 10)):
        c.set(x, y, C(*dark))
    # arcate sopracciliari (inclinate verso il naso) con riflesso sopra
    for side in (-1, 1):
        for i in range(9):
            x = int(cx + side * (3 + i))
            y = 11 + int((8 - i) * 0.35) - 0
            c.set(x, y, C(*dark))
            c.set(x, y + 1, C(*dark))
            c.set(x, y - 1, C(*light))
    # occhi: mandorle incavate inclinate
    for side, tilt in ((-1, 0.28), (1, -0.28)):
        ex, ey = cx + side * 6.6, 15.4
        for y in range(11, 21):
            for x in range(32):
                dx, dy = x + 0.5 - ex, y + 0.5 - ey
                rx = dx * math.cos(tilt * side) + dy * math.sin(tilt * side) * -1
                ry = dx * math.sin(tilt * side) + dy * math.cos(tilt * side)
                if (rx / 4.4) ** 2 + (ry / 1.9) ** 2 <= 1.0:
                    c.set(x, y, C(26, 22, 24))
        c.set(int(ex - side * 1.5), 14, C(74, 66, 66))
    # naso: costa luminosa a sinistra, ombra a destra, narici
    for y in range(14, 23):
        c.set(15, y, C(*light))
        c.set(16, y, C(150, 142, 128))
    for (x, y) in ((13, 22), (14, 22), (17, 22), (18, 22), (14, 23), (17, 23)):
        c.set(x, y, C(72, 64, 58))
    # bocca: linea severa leggermente china, labbra evidenziate
    for x in range(10, 22):
        yy = 25 + int(((x - 15.5) / 6.0) ** 2 * 1.6)
        c.set(x, yy, C(58, 50, 48))
        c.set(x, yy - 1, C(*light))
        c.set(x, yy + 1, C(150, 142, 128))
    # incisioni verticali sulle guance
    for side in (-1, 1):
        for y in range(18, 25):
            c.set(int(cx + side * 8.5 - (0 if side < 0 else 1)), y, C(*dark))
    c.outline(OUT)
    return c.p


def stand_arrow():
    """Freccia dello Stand: punta d'acciaio ornata con foro e alette, asta scura con fasce dorate e piume."""
    c = Canvas(32)
    ox, oy = 2.0, 30.0
    ux, uy, nx, ny = 0.7071, -0.7071, 0.7071, 0.7071
    shaft, shaft_l = (104, 44, 44), (150, 76, 66)
    gold, gold_d = (246, 206, 84), (170, 118, 30)
    cream, red, red_d = (244, 236, 214), (200, 52, 60), (132, 30, 42)
    for y in range(32):
        for x in range(32):
            px, py = x + 0.5 - ox, y + 0.5 - oy
            a = px * ux + py * uy
            b = px * nx + py * ny
            col = None
            if 8 <= a <= 31 and abs(b) <= 1.5:                              # asta
                col = shaft_l if b < -0.3 else shaft
                if abs(b) < 0.5:
                    col = (178, 96, 80)
                for (lo, hi) in ((11, 12.6), (17, 18.6), (27, 29)):
                    if lo <= a <= hi:
                        col = gold if b < 0.4 else gold_d
            if 0 <= a < 12 and abs(b) <= 1.4 + (12 - a) * 0.42:             # impennaggio
                stripe = int(a * 0.9) % 3
                col = cream if stripe == 0 else (red if b < 0 else red_d)
                if abs(b) < 0.45:
                    col = (96, 44, 40)
            if 29 <= a <= 42:                                              # punta d'acciaio
                if a <= 34:
                    hw = 1.5 + (a - 29) * (6.2 - 1.5) / 5.0
                else:
                    hw = 6.2 * max(0.0, 1 - ((a - 34) / 8.0) ** 1.5)
                if abs(b) <= hw:
                    col = (226, 234, 244) if b < -0.6 else ((150, 164, 190) if b > 1.2 else (196, 208, 224))
                    if abs(b) < 0.5:
                        col = (255, 255, 255)
                    if hw - abs(b) < 0.9:
                        col = (112, 124, 150)
            if 26 <= a <= 31 and 1.5 < abs(b) <= 1.5 + (a - 26) * 0.9:     # alette
                col = (170, 184, 208) if b < 0 else (118, 130, 156)
            if math.hypot(a - 35.5, b) <= 1.7:                             # foro nella punta
                col = None
            if col is not None:
                c.set(x, y, C(col[0], col[1], col[2]))
    c.outline(OUT)
    return c.p


ITEMS = {
    'steel_ball': steel_ball,
    'stand_arrow': stand_arrow,
    'hamon_scroll': lambda: scroll(C(244, 196, 64), C(176, 124, 28), SUN8, C(240, 130, 24)),
    'spin_scroll': lambda: scroll(C(70, 200, 150), C(34, 130, 96), SPIRAL8, C(24, 140, 104)),
    'boxing_manual': boxing_manual,
    'stone_mask': stone_mask,
    'red_stone_of_aja': red_stone,
    'projectile_knife': projectile_knife,
    'projectile_star': projectile_star,
    'projectile_zip': projectile_zip,
}


def main():
    for name, fn in ITEMS.items():
        rows = fn()
        write_png(ITEM_DIR / (name + '.png'), len(rows), len(rows), rows)
    print('Texture oggetti generate: %d' % len(ITEMS))


if __name__ == '__main__':
    main()
