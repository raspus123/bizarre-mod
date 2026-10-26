#!/usr/bin/env python3
"""Genera le texture degli Stand (64x32) e le icone dell'HUD (16x16).

Solo libreria standard di Python. Si lancia dalla radice del progetto:
    python3 tools/generate_textures.py
Le texture degli Stand seguono la mappa UV del modello umanoide di Minecraft 1.16.5 (BipedModel 64x32):
testa (0,0), cappello/capelli (32,0), corpo (16,16), braccio (40,16), gamba (0,16).
Il braccio e la gamba sinistri riusano quelli destri (specchiati), quindi i disegni sono simmetrici.
"""
import math
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'src/main/resources/assets/bizarremod'


def C(r, g, b, a=255):
    return (r, g, b, a)


# ------------------------------------------------------------------ PNG
def write_png(path, width, height, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = b''.join(b'\x00' + b''.join(bytes(p) for p in row) for row in rows)

    def chunk(tag, data):
        body = struct.pack('>I', len(data)) + tag + data
        return body + struct.pack('>I', zlib.crc32(tag + data) & 0xffffffff)

    data = (b'\x89PNG\r\n\x1a\n'
            + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 6, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(raw, 9))
            + chunk(b'IEND', b''))
    path.write_bytes(data)


# ------------------------------------------------------------------ mappa UV del modello
def faces(u, v, w, h, d):
    """Rettangoli (x, y, larghezza, altezza) delle sei facce di un parallelepipedo."""
    return {
        'top': (u + d, v, w, d),
        'bottom': (u + d + w, v, w, d),
        'right': (u, v + d, d, h),
        'front': (u + d, v + d, w, h),
        'left': (u + d + w, v + d, d, h),
        'back': (u + 2 * d + w, v + d, w, h),
    }


HEAD = faces(0, 0, 8, 8, 8)
HAT = faces(32, 0, 8, 8, 8)
BODY = faces(16, 16, 8, 12, 4)
ARM = faces(40, 16, 4, 12, 4)
LEG = faces(0, 16, 4, 12, 4)
SIDES = ('right', 'front', 'left', 'back')
SHADE = {'top': 1.12, 'front': 1.0, 'right': 0.88, 'left': 0.88, 'back': 0.80, 'bottom': 0.62}


def shade(c, k, jit=0):
    return (max(0, min(255, int(c[0] * k) + jit)), max(0, min(255, int(c[1] * k) + jit)),
            max(0, min(255, int(c[2] * k) + jit)), c[3])


class Sheet:
    def __init__(self, w=64, h=32):
        self.w, self.h = w, h
        self.p = [[(0, 0, 0, 0)] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    # --- colorazione di un'intera scatola, con ombre per faccia e una leggera grana
    def box(self, F, color, grain=True):
        for name, (x, y, w, h) in F.items():
            for yy in range(y, y + h):
                for xx in range(x, x + w):
                    jit = (((xx * 73856093) ^ (yy * 19349663)) % 7 - 3) if grain else 0
                    self.set(xx, yy, shade(color, SHADE[name], jit))

    # --- primitive relative a una faccia
    def put(self, F, face, dx, dy, c):
        x, y, w, h = F[face]
        if 0 <= dx < w and 0 <= dy < h:
            self.set(x + dx, y + dy, c)

    def hl(self, F, face, dy, dx0, dx1, c):
        for dx in range(dx0, dx1 + 1):
            self.put(F, face, dx, dy, c)

    def vl(self, F, face, dx, dy0, dy1, c):
        for dy in range(dy0, dy1 + 1):
            self.put(F, face, dx, dy, c)

    def blk(self, F, face, dx0, dy0, dx1, dy1, c):
        for dy in range(dy0, dy1 + 1):
            self.hl(F, face, dy, dx0, dx1, c)

    def band(self, F, dy0, dy1, c):
        """Fascia che avvolge i quattro lati (cintura, polsini, stivali...)."""
        for face in SIDES:
            w = F[face][2]
            self.blk(F, face, 0, dy0, w - 1, dy1, c)

    def stamp(self, F, face, x, y, rows, palette):
        """Disegna un emblema da una griglia di caratteri; '.' = trasparente (non tocca)."""
        for r, row in enumerate(rows):
            for q, ch in enumerate(row):
                if ch in palette:
                    self.put(F, face, x + q, y + r, palette[ch])

    # --- capelli / cresta sul livello "cappello" (sopra la testa)
    def hair(self, color, depths, side_rows=2, back_rows=None, top_color=None):
        x, y, w, h = HAT['top']
        for yy in range(y, y + h):
            for xx in range(x, x + w):
                self.set(xx, yy, top_color or shade(color, 1.1, ((xx * 31 + yy * 17) % 5) - 2))
        back_rows = side_rows if back_rows is None else back_rows
        for face, rows in (('right', side_rows), ('left', side_rows), ('back', back_rows)):
            fx, fy, fw, fh = HAT[face]
            for dx in range(fw):
                for dy in range(rows):
                    self.set(fx + dx, fy + dy, shade(color, SHADE[face], ((dx * 13 + dy * 7) % 5) - 2))
        fx, fy, fw, fh = HAT['front']
        for dx, depth in enumerate(depths):
            for dy in range(depth):
                self.set(fx + dx, fy + dy, shade(color, 1.0, ((dx * 11 + dy * 5) % 5) - 2))

    def hat_px(self, face, dx, dy, c):
        self.put(HAT, face, dx, dy, c)


# ------------------------------------------------------------------ gli Stand
def star_platinum(s):
    skin, dark, light = C(120, 98, 208), C(82, 64, 156), C(156, 136, 240)
    navy, gold, ink = C(34, 40, 96), C(226, 186, 74), C(18, 16, 28)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # muscoli
    s.hl(BODY, 'front', 3, 1, 6, dark)
    s.vl(BODY, 'front', 3, 4, 8, dark)
    s.vl(BODY, 'front', 4, 4, 8, dark)
    s.hl(BODY, 'front', 1, 1, 2, light)
    s.hl(BODY, 'front', 1, 5, 6, light)
    s.hl(ARM, 'front', 3, 0, 3, dark)
    s.hl(ARM, 'front', 6, 0, 3, dark)
    s.vl(ARM, 'front', 1, 0, 2, light)
    # cintura e pantaloncini blu notte, polsini
    s.band(BODY, 8, 8, gold)
    s.band(BODY, 9, 11, navy)
    s.band(LEG, 0, 3, navy)
    s.band(LEG, 10, 11, navy)
    s.band(ARM, 9, 11, navy)
    s.band(ARM, 8, 8, gold)
    # volto: sopracciglia scure, occhi azzurri, bocca severa
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.blk(HEAD, 'front', 1, 3, 2, 4, C(166, 240, 255))
    s.blk(HEAD, 'front', 5, 3, 6, 4, C(166, 240, 255))
    s.put(HEAD, 'front', 2, 4, ink)
    s.put(HEAD, 'front', 5, 4, ink)
    s.put(HEAD, 'front', 3, 5, dark)
    s.put(HEAD, 'front', 4, 5, dark)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.hair(C(20, 18, 30), [2, 3, 2, 3, 3, 2, 3, 2], side_rows=3, back_rows=4)


def the_world(s):
    skin, dark, light = C(238, 208, 62), C(192, 158, 34), C(255, 238, 126)
    teal, ink, glow, gem = C(26, 140, 122), C(22, 24, 28), C(120, 255, 210), C(255, 80, 90)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    s.band(HEAD, 1, 1, teal)                       # fascia sulla fronte
    s.put(HEAD, 'front', 3, 1, gem)
    s.put(HEAD, 'front', 4, 1, gem)
    s.blk(HEAD, 'front', 1, 3, 2, 4, ink)
    s.blk(HEAD, 'front', 5, 3, 6, 4, ink)
    s.hl(HEAD, 'front', 3, 1, 2, glow)
    s.hl(HEAD, 'front', 3, 5, 6, glow)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.hl(HEAD, 'front', 5, 3, 4, dark)
    # orologio sul petto
    s.blk(BODY, 'front', 2, 2, 5, 5, teal)
    s.blk(BODY, 'front', 3, 3, 4, 4, ink)
    s.put(BODY, 'front', 3, 3, glow)
    s.put(BODY, 'front', 4, 4, glow)
    s.hl(BODY, 'front', 7, 1, 6, dark)
    s.band(BODY, 8, 8, teal)
    s.band(BODY, 9, 11, ink)
    s.band(ARM, 0, 1, teal)
    s.band(ARM, 9, 11, ink)
    s.band(LEG, 0, 2, ink)
    s.band(LEG, 8, 11, teal)
    s.vl(ARM, 'front', 1, 3, 7, light)
    s.hair(C(252, 226, 96), [1, 1, 1, 2, 2, 1, 1, 1], side_rows=1, back_rows=2)


HEART5 = ['.X.X.', 'XXXXX', '.XXX.', '..X..']
HEART3 = ['X.X', 'XXX', '.X.']


def crazy_diamond(s):
    skin, dark = C(104, 140, 232), C(70, 102, 190)
    pink, white, ink = C(255, 128, 188), C(255, 255, 255), C(24, 24, 52)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    s.stamp(BODY, 'front', 2, 2, HEART5, {'X': pink})
    s.stamp(ARM, 'front', 1, 2, HEART3, {'X': pink})
    s.stamp(ARM, 'back', 1, 2, HEART3, {'X': pink})
    s.hl(BODY, 'front', 8, 0, 7, pink)
    s.band(BODY, 9, 11, pink)
    s.band(LEG, 0, 2, pink)
    s.band(LEG, 9, 11, pink)
    s.band(ARM, 9, 11, pink)
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.blk(HEAD, 'front', 1, 3, 2, 4, white)
    s.blk(HEAD, 'front', 5, 3, 6, 4, white)
    s.put(HEAD, 'front', 2, 4, pink)
    s.put(HEAD, 'front', 5, 4, pink)
    s.hl(HEAD, 'front', 6, 2, 5, dark)
    s.hair(C(250, 192, 222), [2, 3, 3, 2, 2, 3, 3, 2], side_rows=3, back_rows=4)


SKULL = ['.WWWW.', 'WWWWWW', 'WKWWKW', 'WWKKWW', '.WWWW.', '.WKWK.']


def killer_queen(s):
    skin, dark, ink = C(246, 208, 222), C(208, 150, 172), C(34, 22, 36)
    white, maroon, ear = C(255, 255, 255), C(112, 56, 80), C(232, 168, 196)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # volto: occhi neri, muso come una maschera
    s.blk(HEAD, 'front', 1, 3, 2, 4, ink)
    s.blk(HEAD, 'front', 5, 3, 6, 4, ink)
    s.put(HEAD, 'front', 1, 3, white)
    s.put(HEAD, 'front', 5, 3, white)
    s.blk(HEAD, 'front', 2, 5, 5, 7, dark)
    s.hl(HEAD, 'front', 5, 3, 4, ink)
    s.hl(HEAD, 'front', 7, 3, 4, ink)
    # teschio sul petto
    s.blk(BODY, 'front', 0, 0, 7, 7, maroon)
    s.stamp(BODY, 'front', 1, 1, SKULL, {'W': white, 'K': ink})
    s.band(BODY, 8, 9, maroon)
    s.band(ARM, 9, 11, maroon)
    s.band(LEG, 10, 11, maroon)
    s.hl(BODY, 'front', 11, 0, 7, dark)
    # orecchie da gatto sul cappello
    s.hair(C(240, 188, 208), [0] * 8, side_rows=0, back_rows=0, top_color=skin)
    for (ax, ay) in ((0, 0), (6, 0)):
        s.hat_px('top', ax, ay, ear)
        s.hat_px('top', ax + 1, ay, ear)
        s.hat_px('top', ax, ay + 1, ear)
        s.hat_px('top', ax + 1, ay + 1, maroon)
    for dx in (0, 1, 6, 7):
        s.hat_px('front', dx, 0, ear)
        s.hat_px('back', dx, 0, ear)


LADYBUG = ['..KK..', '.RKKR.', 'RKRRKR', 'RRKKRR', 'RKRRKR', '.RKKR.']


def gold_experience(s):
    skin, dark, light = C(238, 188, 44), C(190, 142, 18), C(252, 228, 116)
    red, ink, green = C(214, 44, 44), C(26, 20, 16), C(46, 160, 86)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # elmo con visiera nera
    s.blk(HEAD, 'front', 1, 3, 6, 4, ink)
    s.put(HEAD, 'front', 1, 3, light)
    s.put(HEAD, 'front', 6, 3, light)
    s.hl(HEAD, 'front', 5, 2, 5, dark)
    s.hl(HEAD, 'front', 6, 3, 4, dark)
    s.vl(HEAD, 'front', 3, 0, 1, light)
    s.vl(HEAD, 'front', 4, 0, 1, light)
    # coccinella sul petto
    s.stamp(BODY, 'front', 1, 1, LADYBUG, {'R': red, 'K': ink})
    s.hl(BODY, 'front', 8, 0, 7, dark)
    s.band(BODY, 9, 11, dark)
    s.band(ARM, 8, 8, green)
    s.band(ARM, 9, 11, dark)
    s.band(LEG, 0, 1, dark)
    s.band(LEG, 8, 8, green)
    s.band(LEG, 9, 11, dark)
    s.vl(ARM, 'front', 1, 1, 6, light)
    s.hair(C(246, 210, 80), [1, 1, 2, 2, 2, 2, 1, 1], side_rows=2, back_rows=3)


def silver_chariot(s):
    skin, dark, light = C(190, 198, 210), C(130, 140, 158), C(238, 242, 248)
    ink, red, gold = C(22, 26, 36), C(196, 40, 44), C(204, 172, 72)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # elmo: fessura orizzontale e verticale (a T)
    s.hl(HEAD, 'front', 3, 1, 6, ink)
    s.hl(HEAD, 'front', 4, 1, 6, ink)
    s.vl(HEAD, 'front', 3, 5, 7, ink)
    s.vl(HEAD, 'front', 4, 5, 7, ink)
    s.hl(HEAD, 'front', 2, 0, 7, light)
    s.vl(HEAD, 'front', 0, 3, 7, dark)
    s.vl(HEAD, 'front', 7, 3, 7, dark)
    # armatura: piastra con croce, rivetti, bordi dorati
    s.hl(BODY, 'front', 0, 0, 7, gold)
    s.vl(BODY, 'front', 3, 1, 8, dark)
    s.vl(BODY, 'front', 4, 1, 8, dark)
    s.hl(BODY, 'front', 4, 0, 7, dark)
    for (px, py) in ((1, 2), (6, 2), (1, 6), (6, 6)):
        s.put(BODY, 'front', px, py, light)
    s.band(BODY, 9, 9, dark)
    s.band(BODY, 10, 11, gold)
    s.band(ARM, 0, 2, dark)
    s.hl(ARM, 'front', 2, 0, 3, light)
    s.band(ARM, 8, 11, dark)
    s.band(LEG, 0, 1, gold)
    s.hl(LEG, 'front', 5, 0, 3, light)
    s.hl(LEG, 'front', 6, 0, 3, dark)
    s.band(LEG, 7, 11, dark)
    # cimiero rosso
    s.hair(C(196, 196, 208), [0] * 8, side_rows=1, back_rows=1, top_color=C(168, 176, 190))
    for dy in range(8):
        s.hat_px('top', 3, dy, red)
        s.hat_px('top', 4, dy, red)
    for dy in range(6):
        s.hat_px('back', 3, dy, red)
        s.hat_px('back', 4, dy, red)


CHEVRON = ['X......X', '.X....X.', '..X..X..', '...XX...']


def magicians_red(s):
    skin, dark, light = C(216, 50, 42), C(158, 28, 24), C(240, 96, 64)
    orange, yellow, ink = C(244, 138, 40), C(244, 200, 64), C(24, 12, 12)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # testa d'uccello: occhi gialli e becco
    s.blk(HEAD, 'front', 1, 3, 2, 4, yellow)
    s.blk(HEAD, 'front', 5, 3, 6, 4, yellow)
    s.put(HEAD, 'front', 2, 4, ink)
    s.put(HEAD, 'front', 5, 4, ink)
    s.blk(HEAD, 'front', 3, 4, 4, 6, orange)
    s.hl(HEAD, 'front', 4, 3, 4, yellow)
    s.hl(HEAD, 'front', 6, 3, 4, dark)
    # piume a V sul petto
    for oy in (1, 4, 7):
        s.stamp(BODY, 'front', 0, oy, CHEVRON, {'X': light})
    s.band(BODY, 9, 9, yellow)
    s.band(BODY, 10, 11, dark)
    s.band(ARM, 3, 3, yellow)
    s.band(ARM, 9, 11, yellow)
    s.band(LEG, 0, 1, dark)
    s.band(LEG, 8, 8, yellow)
    s.band(LEG, 9, 11, dark)
    s.vl(ARM, 'front', 1, 4, 8, light)
    # cresta di piume
    s.hair(orange, [1, 2, 2, 3, 3, 2, 2, 1], side_rows=2, back_rows=4)
    cols = (orange, skin, yellow)
    for dx in range(8):
        for dy in range(8):
            s.hat_px('top', dx, dy, cols[(dx + dy // 3) % 3])


def lattice(s, F, faces_, base, line):
    for face in faces_:
        x, y, w, h = F[face]
        for dy in range(h):
            for dx in range(w):
                if (dx + dy) % 4 == 0 or (dx - dy) % 4 == 0:
                    s.put(F, face, dx, dy, line)


def hierophant_green(s):
    skin, dark, deep = C(62, 168, 92), C(36, 116, 58), C(22, 76, 40)
    light, slit, gem = C(156, 232, 156), C(224, 255, 120), C(120, 255, 190)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # losanghe sul corpo e sugli arti
    for F in (BODY, ARM, LEG):
        lattice(s, F, SIDES, skin, dark)
    for F in (BODY, ARM, LEG):
        s.hl(F, 'front', 0, 0, F['front'][2] - 1, deep)
    # visiera con fessura luminosa
    s.hl(HEAD, 'front', 3, 1, 6, slit)
    s.hl(HEAD, 'front', 4, 1, 6, deep)
    s.hl(HEAD, 'front', 6, 2, 5, deep)
    s.vl(HEAD, 'front', 0, 2, 7, dark)
    s.vl(HEAD, 'front', 7, 2, 7, dark)
    s.put(BODY, 'front', 3, 3, gem)
    s.put(BODY, 'front', 4, 3, gem)
    s.put(BODY, 'front', 3, 4, gem)
    s.put(BODY, 'front', 4, 4, gem)
    s.band(BODY, 9, 9, deep)
    s.band(ARM, 9, 11, deep)
    s.band(LEG, 10, 11, deep)
    s.hair(C(50, 140, 76), [1, 2, 1, 2, 2, 1, 2, 1], side_rows=2, back_rows=3)
    s.hat_px('front', 3, 0, gem)
    s.hat_px('front', 4, 0, gem)


def spots(s, F, face_names, spot, freckle, seed):
    for face in face_names:
        x0, y0, w, h = F[face]
        for dy in range(h):
            for dx in range(w):
                v = (dx * 31 + dy * 17 + x0 * 7 + y0 * 13 + seed) % 23
                if v == 0:
                    s.put(F, face, dx, dy, spot)
                    s.put(F, face, dx + 1, dy, spot)
                elif v == 11:
                    s.put(F, face, dx, dy, freckle)


def king_crimson(s):
    skin, dark, light = C(190, 42, 66), C(98, 16, 42), C(240, 122, 142)
    bone, ink, eye = C(246, 214, 220), C(20, 8, 14), C(255, 240, 170)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    for i, F in enumerate((HEAD, BODY, ARM, LEG)):
        spots(s, F, tuple(F.keys()), dark, light, i * 5)
    # il secondo volto sulla fronte
    s.blk(HEAD, 'front', 2, 0, 5, 1, bone)
    s.put(HEAD, 'front', 3, 1, ink)
    s.put(HEAD, 'front', 4, 1, ink)
    # volto principale
    s.blk(HEAD, 'front', 1, 3, 2, 4, eye)
    s.blk(HEAD, 'front', 5, 3, 6, 4, eye)
    s.put(HEAD, 'front', 1, 4, ink)
    s.put(HEAD, 'front', 6, 4, ink)
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.band(BODY, 10, 11, ink)
    s.band(ARM, 10, 11, ink)
    s.band(LEG, 0, 1, ink)
    s.band(LEG, 10, 11, ink)
    s.hair(C(150, 30, 70), [2, 3, 2, 3, 3, 2, 3, 2], side_rows=3, back_rows=5)
    s.hat_px('top', 3, 0, C(255, 150, 190))
    s.hat_px('top', 4, 0, C(255, 150, 190))


def sticky_fingers(s):
    skin, dark, ink = C(58, 126, 226), C(36, 86, 178), C(22, 30, 66)
    white, gold = C(246, 246, 252), C(244, 204, 76)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # cerniere (denti alternati bianco/azzurro) su corpo, braccia e gambe
    for F, cx in ((BODY, 3), (ARM, 1), (LEG, 1)):
        h = F['front'][3]
        for dy in range(h):
            s.put(F, 'front', cx + (dy % 2), dy, white)
            s.put(F, 'back', cx + (dy % 2), dy, white)
    s.put(BODY, 'front', 3, 0, gold)
    s.put(BODY, 'front', 4, 0, gold)
    s.vl(BODY, 'front', 3, 1, 1, gold)
    # volto: fessura chiara e cerniera sulla bocca
    s.hl(HEAD, 'front', 3, 1, 6, ink)
    s.hl(HEAD, 'front', 4, 1, 6, ink)
    s.hl(HEAD, 'front', 3, 1, 2, white)
    s.hl(HEAD, 'front', 3, 5, 6, white)
    for dx in range(1, 7):
        s.put(HEAD, 'front', dx, 6, white if dx % 2 == 0 else dark)
    s.band(BODY, 9, 11, ink)
    s.band(ARM, 9, 11, ink)
    s.band(LEG, 0, 1, ink)
    s.band(LEG, 10, 11, ink)
    s.hair(C(24, 36, 84), [2, 2, 2, 3, 3, 2, 2, 2], side_rows=3, back_rows=4)
    for dy in range(6):
        s.hat_px('back', 3, dy, C(40, 60, 130))
        s.hat_px('back', 4, dy, C(40, 60, 130))


def stone_free(s):
    skin, dark = C(142, 170, 200), C(98, 126, 160)
    thread, ink, eye = C(238, 246, 252), C(24, 26, 34), C(150, 232, 252)
    for F in (HEAD, BODY, ARM, LEG):
        s.box(F, skin)
    # fili cuciti in diagonale su corpo e arti
    for F in (BODY, ARM, LEG):
        for face in SIDES:
            x, y, w, h = F[face]
            for dy in range(h):
                for dx in range(w):
                    if (dx + dy) % 6 == 0:
                        s.put(F, face, dx, dy, thread)
                    elif (dx + dy) % 6 == 3:
                        s.put(F, face, dx, dy, dark)
    # volto
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.hl(HEAD, 'front', 3, 1, 2, eye)
    s.hl(HEAD, 'front', 3, 5, 6, eye)
    s.hl(HEAD, 'front', 4, 1, 2, ink)
    s.hl(HEAD, 'front', 4, 5, 6, ink)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.band(BODY, 9, 9, ink)
    s.band(ARM, 9, 9, thread)
    s.band(LEG, 9, 9, thread)
    s.hair(C(26, 28, 38), [2, 3, 2, 3, 3, 2, 3, 2], side_rows=3, back_rows=4)


STANDS = {
    'star_platinum': star_platinum, 'the_world': the_world, 'crazy_diamond': crazy_diamond,
    'killer_queen': killer_queen, 'gold_experience': gold_experience, 'silver_chariot': silver_chariot,
    'magicians_red': magicians_red, 'hierophant_green': hierophant_green, 'king_crimson': king_crimson,
    'sticky_fingers': sticky_fingers, 'stone_free': stone_free,
}


def face_icon(sheet):
    """Ritratto 16x16: volto frontale (testa + capelli) ingrandito 2x."""
    hx, hy, _, _ = HEAD['front']
    cx, cy, _, _ = HAT['front']
    rows = []
    for y in range(8):
        base = []
        for x in range(8):
            over = sheet.p[cy + y][cx + x]
            base.append(over if over[3] > 0 else sheet.p[hy + y][hx + x])
        rows.append(base)
    out = []
    for y in range(16):
        out.append([rows[y // 2][x // 2] for x in range(16)])
    # bordino scuro sottile
    for i in range(16):
        for (x, y) in ((i, 0), (i, 15), (0, i), (15, i)):
            r, g, b, a = out[y][x]
            out[y][x] = (int(r * 0.55), int(g * 0.55), int(b * 0.55), a)
    return out


# ------------------------------------------------------------------ icone dell'HUD (bianche, colorabili)
def glyph(mask_fn, fill=C(255, 255, 255), outline=C(0, 0, 0, 230)):
    size = 16
    mask = [[bool(mask_fn(x + 0.5, y + 0.5)) for x in range(size)] for y in range(size)]
    rows = [[(0, 0, 0, 0)] * size for _ in range(size)]
    for y in range(size):
        for x in range(size):
            if mask[y][x]:
                rows[y][x] = fill
    for y in range(size):
        for x in range(size):
            if mask[y][x]:
                continue
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nx, ny = x + dx, y + dy
                if 0 <= nx < size and 0 <= ny < size and mask[ny][nx]:
                    rows[y][x] = outline
                    break
    return rows


FIST = [
    "................",
    "................",
    "..XXX.XXX.XXX...",
    ".XXXXXXXXXXXXX..",
    ".XXXX.XXX.XXXX..",
    ".XXXX.XXX.XXXX..",
    ".XXXXXXXXXXXXX..",
    "XXXXXXXXXXXXXX..",
    "XXXXXXXXXXXXXX..",
    ".XXXXXXXXXXXXX..",
    "..XXXXXXXXXXX...",
    "...XXXXXXXXX....",
    "...XXXXXXXXX....",
    "...XXXXXXXXX....",
    "................",
    "................",
]


def m_fist(x, y):
    """Pugno disegnato a mano: quattro nocche separate, pollice e polso."""
    return FIST[int(y)][int(x)] == 'X'


def m_star(x, y):
    cx, cy = 8.0, 8.4
    pts = []
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = 7.4 if i % 2 == 0 else 3.1
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            inside = not inside
        j = i
    return inside


def m_wave(x, y):
    d = math.hypot(x - 8, y - 8)
    return d < 1.8 or 3.6 <= d < 5.0 or 6.4 <= d < 7.8


def m_clock(x, y):
    d = math.hypot(x - 8, y - 8)
    ring = 5.8 <= d < 7.6
    hand1 = abs(x - 8) < 0.7 and 3.0 <= y <= 8.4
    hand2 = abs(y - 8) < 0.7 and 8 <= x <= 11.6
    return ring or hand1 or hand2 or d < 1.2


def m_sun(x, y):
    d = math.hypot(x - 8, y - 8)
    if d < 3.6:
        return True
    ang = math.atan2(y - 8, x - 8)
    ray = abs(((ang / (math.pi / 4)) + 0.5) % 1 - 0.5) < 0.17
    return 5.0 <= d < 7.6 and ray


def m_spiral(x, y):
    dx, dy = x - 8, y - 8
    r = math.hypot(dx, dy)
    if r > 7.6:
        return False
    th = math.atan2(dy, dx) % (2 * math.pi)
    for k in range(3):
        rr = 0.9 + 0.72 * (th + 2 * math.pi * k)
        if abs(r - rr) < 0.95:
            return True
    return False


def m_glove(x, y):
    main = ((x - 7.6) / 5.2) ** 2 + ((y - 6.6) / 5.4) ** 2 < 1
    thumb = ((x - 3.2) / 2.6) ** 2 + ((y - 8.6) / 2.8) ** 2 < 1
    cuff = 4.2 <= x < 11.6 and 11.2 <= y < 14.8
    return main or thumb or cuff


def make_hud_icons():
    write_png(ASSETS / 'textures/gui/hud/move_0.png', 16, 16, glyph(m_fist))
    write_png(ASSETS / 'textures/gui/hud/move_1.png', 16, 16, glyph(m_star))
    write_png(ASSETS / 'textures/gui/hud/move_2.png', 16, 16, glyph(m_wave))
    write_png(ASSETS / 'textures/gui/hud/move_3.png', 16, 16, glyph(m_clock))
    write_png(ASSETS / 'textures/gui/hud/style_hamon.png', 16, 16, glyph(m_sun, fill=C(255, 214, 90)))
    write_png(ASSETS / 'textures/gui/hud/style_spin.png', 16, 16, glyph(m_spiral, fill=C(120, 232, 190)))
    write_png(ASSETS / 'textures/gui/hud/style_boxing.png', 16, 16, glyph(m_glove, fill=C(236, 84, 84)))


def main():
    for name, painter in STANDS.items():
        s = Sheet()
        painter(s)
        write_png(ASSETS / ('textures/entity/stand/%s.png' % name), 64, 32, s.p)
        write_png(ASSETS / ('textures/gui/hud/stand_%s.png' % name), 16, 16, face_icon(s))
    make_hud_icons()
    print('Texture generate: %d stand + icone HUD' % len(STANDS))


if __name__ == '__main__':
    main()
