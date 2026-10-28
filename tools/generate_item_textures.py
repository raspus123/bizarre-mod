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
    def __init__(self):
        self.p = [[CLEAR] * 16 for _ in range(16)]

    def set(self, x, y, c):
        if 0 <= x < 16 and 0 <= y < 16:
            self.p[y][x] = c

    def get(self, x, y):
        return self.p[y][x] if 0 <= x < 16 and 0 <= y < 16 else CLEAR

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
        for y in range(16):
            for x in range(16):
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
def stand_arrow():
    c = Canvas()
    shaft, shaft_d = C(122, 84, 52), C(84, 56, 34)
    gold, gold_d = C(244, 200, 72), C(176, 122, 30)
    silver, silver_d, white = C(214, 224, 238), C(140, 156, 182), C(255, 255, 255)
    red, red_d = C(206, 52, 62), C(132, 28, 40)
    # asta diagonale (dal basso a sinistra verso l'alto a destra)
    for i in range(9):
        x, y = 3 + i, 12 - i
        c.set(x, y, shaft)
        c.set(x + 1, y, shaft_d)
    for i in (2, 3, 7):                              # fasce dorate
        c.set(3 + i, 12 - i, gold)
        c.set(4 + i, 12 - i, gold_d)
    # impennaggi rossi all'estremita'
    for (x, y) in ((0, 10), (1, 10), (1, 11), (2, 11), (2, 12)):
        c.set(x, y, red)
    for (x, y) in ((3, 13), (4, 13), (4, 14), (5, 14), (3, 14)):
        c.set(x, y, red_d)
    c.set(2, 13, red)
    c.set(1, 14, red)
    # punta a losanga con riflessi
    cx, cy = 11.5, 3.5
    for y in range(0, 8):
        for x in range(7, 16):
            a = ((x + 0.5 - cx) - (y + 0.5 - cy)) / 1.414
            b = ((x + 0.5 - cx) + (y + 0.5 - cy)) / 1.414
            if -2.6 <= a <= 4.8 and abs(b) <= 3.5 * (5.0 - a) / 7.6:
                col = silver if b < 0.4 else silver_d
                if abs(b + 1.0) < 0.55 and -1.5 < a < 3.0:
                    col = white
                c.set(x, y, col)
    c.set(11, 3, C(60, 70, 96))                      # foro al centro della punta
    c.outline(OUT)
    return c.p


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
def stone_mask():
    c = Canvas()
    stone, stone_l, stone_d = C(186, 180, 168), C(222, 216, 204), C(132, 126, 116)
    hole, glow, tooth = C(26, 22, 26), C(176, 44, 44), C(238, 234, 224)
    # volto ovale
    for y in range(1, 15):
        for x in range(2, 14):
            nx, ny = (x + 0.5 - 8) / 5.9, (y + 0.5 - 8) / 6.9
            if nx * nx + ny * ny <= 1.0:
                col = stone_l if (nx < -0.35 and ny < 0.2) else (stone_d if (nx > 0.55 or ny > 0.72) else stone)
                c.set(x, y, col)
    # sopracciglia e occhi incavati
    for (x0, x1) in ((4, 6), (9, 11)):
        c.rect(x0, 5, x1, 5, stone_d)
        c.rect(x0, 6, x1, 7, hole)
        c.set(x0 + 1, 7, glow)
    # naso
    c.rect(7, 7, 8, 10, stone_d)
    c.set(7, 10, hole)
    c.set(8, 10, hole)
    # bocca con denti
    c.rect(5, 12, 10, 12, hole)
    for x in (6, 8, 10):
        c.set(x, 12, tooth)
    # spuntoni ai lati (la maschera ha le punte che penetrano nel cranio)
    for (x, y) in ((1, 5), (0, 4), (14, 5), (15, 4), (1, 8), (14, 8)):
        c.set(x, y, tooth)
    c.set(2, 4, stone_d)
    c.set(13, 4, stone_d)
    c.outline(OUT)
    return c.p


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


def steel_ball():
    c = Canvas()
    for y in range(16):
        for x in range(16):
            dx, dy = x + 0.5 - 8.0, y + 0.5 - 8.0
            d = math.hypot(dx, dy)
            if d > 6.6:
                continue
            # sfumatura metallica: luce in alto a sinistra, ombra in basso a destra
            lit = 1.0 - ((dx + dy) / (2 * 6.6) + 1) / 2          # 1 = luce, 0 = ombra
            base = int(92 + 150 * lit)
            col = C(min(255, base - 6), min(255, base), min(255, base + 12))
            if abs(dy + 0.5) < 0.9 and d < 6.0:                     # fascia incisa al centro
                col = C(236, 190, 70) if lit > 0.35 else C(168, 122, 34)
            c.set(x, y, col)
    for (x, y) in ((4, 3), (5, 3), (4, 4)):                         # riflesso brillante
        c.set(x, y, C(255, 255, 255))
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
        write_png(ITEM_DIR / (name + '.png'), 16, 16, fn())
    print('Texture oggetti generate: %d' % len(ITEMS))


if __name__ == '__main__':
    main()
