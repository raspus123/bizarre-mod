#!/usr/bin/env python3
"""Genera le texture degli Stand (64x64) e le icone dell'HUD (16x16).

Solo libreria standard di Python. Si lancia dalla radice del progetto:
    python3 tools/generate_textures.py
Le texture degli Stand seguono la mappa UV del modello "giocatore" di Minecraft 1.16.5 (PlayerModel 64x64),
che ha un SECONDO STRATO per corpo, braccia e gambe (cinture, fasce, stivali, stemmi in rilievo):
    testa (0,0)  capelli/cresta (32,0)
    corpo (16,16)  corpo, strato esterno (16,32)
    braccio destro (40,16)  strato esterno (40,32)     braccio sinistro (32,48)  strato esterno (48,48)
    gamba destra (0,16)     strato esterno (0,32)      gamba sinistra (16,48)    strato esterno (0,48)
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
BODY_OV = faces(16, 32, 8, 12, 4)
R_ARM, R_ARM_OV = faces(40, 16, 4, 12, 4), faces(40, 32, 4, 12, 4)
L_ARM, L_ARM_OV = faces(32, 48, 4, 12, 4), faces(48, 48, 4, 12, 4)
R_LEG, R_LEG_OV = faces(0, 16, 4, 12, 4), faces(0, 32, 4, 12, 4)
L_LEG, L_LEG_OV = faces(16, 48, 4, 12, 4), faces(0, 48, 4, 12, 4)
ARMS, ARMS_OV = [R_ARM, L_ARM], [R_ARM_OV, L_ARM_OV]
LEGS, LEGS_OV = [R_LEG, L_LEG], [R_LEG_OV, L_LEG_OV]
BASE = [HEAD, BODY] + ARMS + LEGS
SIDES = ('right', 'front', 'left', 'back')
SHADE = {'top': 1.12, 'front': 1.0, 'right': 0.88, 'left': 0.88, 'back': 0.80, 'bottom': 0.62}


def shade(c, k, jit=0):
    return (max(0, min(255, int(c[0] * k) + jit)), max(0, min(255, int(c[1] * k) + jit)),
            max(0, min(255, int(c[2] * k) + jit)), c[3])


def _each(F):
    return F if isinstance(F, (list, tuple)) else [F]


class Sheet:
    def __init__(self, w=64, h=64):
        self.w, self.h = w, h
        self.p = [[(0, 0, 0, 0)] * w for _ in range(h)]

    def set(self, x, y, c):
        if 0 <= x < self.w and 0 <= y < self.h:
            self.p[y][x] = c

    # --- colorazione di scatole intere, con ombre per faccia e una leggera grana
    def box(self, F, color, grain=True):
        for box in _each(F):
            for name, (x, y, w, h) in box.items():
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        jit = (((xx * 73856093) ^ (yy * 19349663)) % 7 - 3) if grain else 0
                        self.set(xx, yy, shade(color, SHADE[name], jit))

    def solid(self, F, color, faces_=None):
        """Colora le facce in tinta unita (per gli strati esterni: stoffa, armatura)."""
        for box in _each(F):
            for name in (faces_ or box.keys()):
                x, y, w, h = box[name]
                for yy in range(y, y + h):
                    for xx in range(x, x + w):
                        self.set(xx, yy, shade(color, SHADE[name]))

    # --- primitive relative a una faccia (F puo' essere una lista: viene applicata a tutte)
    def put(self, F, face, dx, dy, c):
        for box in _each(F):
            x, y, w, h = box[face]
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

    def band(self, F, dy0, dy1, c, shaded=True):
        """Fascia che avvolge i quattro lati (cintura, polsini, stivali...)."""
        for box in _each(F):
            for face in SIDES:
                w = box[face][2]
                col = shade(c, SHADE[face]) if shaded else c
                self.blk(box, face, 0, dy0, w - 1, dy1, col)

    def stamp(self, F, face, x, y, rows, palette):
        """Disegna un emblema da una griglia di caratteri; i caratteri non nella palette non toccano nulla."""
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


# ------------------------------------------------------------------ emblemi
HEART5 = ['.X.X.', 'XXXXX', '.XXX.', '..X..']
HEART3 = ['X.X', 'XXX', '.X.']
SKULL = ['.WWWW.', 'WWWWWW', 'WKWWKW', 'WWKKWW', '.WWWW.', '.WKWK.']
LADYBUG = ['..KK..', '.RKKR.', 'RKRRKR', 'RRKKRR', 'RKRRKR', '.RKKR.']
LADYBUG3 = ['.K.', 'RKR', 'RKR']
STAR3 = ['.X.', 'XXX', '.X.']
CHEVRON = ['X......X', '.X....X.', '..X..X..', '...XX...']


# ------------------------------------------------------------------ gli Stand
def star_platinum(s):
    """Violetto-azzurro, capelli neri a punta lunghi sulla schiena, calzoncini blu notte con cintura dorata."""
    skin, dark, light = C(112, 98, 218), C(72, 60, 160), C(152, 138, 244)
    navy, gold, ink = C(30, 36, 92), C(234, 194, 80), C(16, 14, 30)
    s.box(BASE, skin)
    s.hl(BODY, 'front', 3, 1, 6, dark)                     # pettorali e addominali
    s.vl(BODY, 'front', 3, 4, 8, dark)
    s.vl(BODY, 'front', 4, 4, 8, dark)
    s.hl(BODY, 'front', 5, 1, 2, dark)
    s.hl(BODY, 'front', 5, 5, 6, dark)
    s.hl(BODY, 'front', 7, 1, 2, dark)
    s.hl(BODY, 'front', 7, 5, 6, dark)
    s.hl(BODY, 'front', 1, 1, 2, light)
    s.hl(BODY, 'front', 1, 5, 6, light)
    s.hl(ARMS, 'front', 3, 0, 3, dark)                     # bicipiti
    s.hl(ARMS, 'front', 6, 0, 3, dark)
    s.vl(ARMS, 'front', 1, 0, 2, light)
    s.hl(LEGS, 'front', 6, 0, 3, dark)                     # ginocchia
    s.band(BODY_OV, 8, 8, gold)                            # cintura con fibbia a stella
    s.stamp(BODY_OV, 'front', 3, 7, ['.X.', 'XXX'], {'X': C(255, 244, 170)})
    s.band(BODY_OV, 9, 11, navy)
    s.band(LEGS_OV, 0, 4, navy)
    s.band(ARMS_OV, 9, 11, navy)
    s.band(ARMS_OV, 8, 8, gold)
    s.band(LEGS_OV, 10, 11, C(52, 44, 118))
    # volto
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.blk(HEAD, 'front', 1, 3, 2, 4, C(236, 244, 255))
    s.blk(HEAD, 'front', 5, 3, 6, 4, C(236, 244, 255))
    s.put(HEAD, 'front', 2, 3, C(70, 140, 210))
    s.put(HEAD, 'front', 5, 3, C(70, 140, 210))
    s.put(HEAD, 'front', 2, 4, ink)
    s.put(HEAD, 'front', 5, 4, ink)
    s.hl(HEAD, 'front', 5, 3, 4, dark)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.put(HEAD, 'front', 0, 7, dark)
    s.put(HEAD, 'front', 7, 7, dark)
    s.hair(C(18, 16, 30), [2, 3, 2, 3, 3, 2, 3, 2], side_rows=3, back_rows=7)


def the_world(s):
    """Giallo oro con visiera nera e lenti verdi, pettorale nero a X con gemma, cintura, guanti e stivali neri e verdi."""
    skin, dark, light = C(244, 212, 66), C(196, 160, 36), C(255, 240, 134)
    ink, green, glow, gold = C(20, 22, 26), C(30, 150, 112), C(130, 255, 202), C(252, 218, 92)
    s.box(BASE, skin)
    s.band(HEAD, 3, 4, ink)                                # visiera nera che avvolge la testa
    s.hl(HEAD, 'front', 4, 1, 2, glow)
    s.hl(HEAD, 'front', 4, 5, 6, glow)
    s.blk(HEAD, 'front', 2, 6, 5, 7, dark)                 # protezione della bocca
    s.vl(HEAD, 'front', 3, 6, 7, ink)
    s.vl(HEAD, 'front', 4, 6, 7, ink)
    s.hl(BODY, 'front', 3, 1, 6, dark)
    s.vl(BODY, 'front', 3, 4, 8, dark)
    s.vl(BODY, 'front', 4, 4, 8, dark)
    for i in range(8):                                     # bretelle nere a X
        if 1 + i <= 7:
            s.put(BODY_OV, 'front', i, 1 + i, ink)
            s.put(BODY_OV, 'front', 7 - i, 1 + i, ink)
    s.put(BODY_OV, 'front', 3, 4, green)
    s.put(BODY_OV, 'front', 4, 4, green)
    s.put(BODY_OV, 'front', 3, 5, glow)
    s.put(BODY_OV, 'front', 4, 5, glow)
    s.band(BODY_OV, 8, 8, green)
    s.band(BODY_OV, 9, 11, ink)
    s.band(LEGS_OV, 0, 3, ink)
    s.band(ARMS_OV, 0, 1, ink)
    s.band(ARMS_OV, 8, 8, green)
    s.band(ARMS_OV, 9, 11, ink)
    s.band(LEGS_OV, 8, 8, green)
    s.band(LEGS_OV, 9, 11, ink)
    s.hair(gold, [1, 1, 2, 2, 2, 2, 1, 1], side_rows=1, back_rows=3, top_color=gold)
    for dy in range(8):
        s.hat_px('top', 3, dy, ink)
        s.hat_px('top', 4, dy, ink)


def crazy_diamond(s):
    """Azzurro-lavanda con cuori rosa su petto, spalle e ginocchia, ciuffo rosa e guanti/stivali rosa."""
    skin, dark = C(120, 148, 240), C(78, 104, 198)
    pink, pink_d, white, ink = C(255, 130, 192), C(212, 84, 150), C(255, 255, 255), C(26, 26, 58)
    s.box(BASE, skin)
    s.hl(BODY, 'front', 3, 1, 6, dark)
    s.vl(BODY, 'front', 3, 5, 8, dark)
    s.vl(BODY, 'front', 4, 5, 8, dark)
    s.stamp(BODY_OV, 'front', 1, 1, HEART5, {'X': pink})
    s.stamp(BODY_OV, 'front', 3, 1, HEART5, {'X': pink_d})
    s.stamp(BODY_OV, 'front', 2, 1, HEART5, {'X': pink})
    s.stamp(ARMS_OV, 'front', 1, 0, HEART3, {'X': pink})
    s.stamp(ARMS_OV, 'back', 1, 0, HEART3, {'X': pink})
    s.stamp(ARMS_OV, 'right', 0, 0, ['XX'], {'X': pink_d})
    s.stamp(LEGS_OV, 'front', 1, 5, HEART3, {'X': pink})
    s.band(BODY_OV, 8, 8, pink_d)
    s.band(BODY_OV, 9, 11, pink)
    s.band(LEGS_OV, 0, 3, pink)
    s.band(ARMS_OV, 8, 11, pink)
    s.band(LEGS_OV, 8, 11, pink)
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.blk(HEAD, 'front', 1, 3, 2, 4, white)
    s.blk(HEAD, 'front', 5, 3, 6, 4, white)
    s.put(HEAD, 'front', 2, 3, pink)
    s.put(HEAD, 'front', 2, 4, pink)
    s.put(HEAD, 'front', 5, 3, pink)
    s.put(HEAD, 'front', 5, 4, pink)
    s.hl(HEAD, 'front', 6, 2, 5, dark)
    s.hair(C(252, 198, 226), [2, 3, 3, 2, 2, 3, 3, 2], side_rows=3, back_rows=5)
    s.stamp(HAT, 'front', 2, 0, HEART3, {'X': pink})


def killer_queen(s):
    """Rosa chiarissimo con orecchie da gatto, occhi cerchiati di nero e teschio sul petto."""
    skin, dark, ink = C(248, 216, 228), C(212, 156, 178), C(30, 20, 32)
    white, maroon, ear, ear_in = C(255, 255, 255), C(96, 44, 70), C(240, 180, 204), C(150, 70, 100)
    s.box(BASE, skin)
    s.blk(HEAD, 'front', 0, 3, 3, 5, ink)                  # cerchi neri intorno agli occhi
    s.blk(HEAD, 'front', 4, 3, 7, 5, ink)
    s.blk(HEAD, 'front', 1, 3, 2, 4, white)
    s.blk(HEAD, 'front', 5, 3, 6, 4, white)
    s.put(HEAD, 'front', 2, 4, ink)
    s.put(HEAD, 'front', 5, 4, ink)
    s.put(HEAD, 'front', 3, 5, ink)                        # naso
    s.put(HEAD, 'front', 4, 5, ink)
    s.hl(HEAD, 'front', 6, 2, 5, ink)                      # bocca
    s.put(HEAD, 'front', 2, 7, ink)
    s.put(HEAD, 'front', 5, 7, ink)
    s.blk(BODY_OV, 'front', 0, 0, 7, 7, maroon)            # teschio sul petto
    s.stamp(BODY_OV, 'front', 1, 1, SKULL, {'W': white, 'K': ink})
    s.band(BODY_OV, 8, 8, ink)
    s.band(BODY_OV, 9, 11, maroon)
    s.band(LEGS_OV, 0, 2, maroon)
    s.band(ARMS_OV, 9, 11, maroon)
    s.band(ARMS_OV, 8, 8, ink)
    s.band(LEGS_OV, 9, 11, maroon)
    s.hl(ARMS, 'front', 4, 0, 3, dark)
    s.hl(LEGS, 'front', 6, 0, 3, dark)
    s.hair(C(244, 196, 214), [0] * 8, side_rows=0, back_rows=0, top_color=skin)
    for (ax, ay) in ((0, 0), (6, 0)):                      # orecchie da gatto
        for dx in (0, 1):
            for dy in (0, 1):
                s.hat_px('top', ax + dx, ay + dy, ear)
        s.hat_px('top', ax + (1 if ax == 0 else 0), ay + 1, ear_in)
    for dx in (0, 1, 6, 7):
        s.hat_px('front', dx, 0, ear)
        s.hat_px('back', dx, 0, ear)
    for dx in (0, 1, 2, 3):
        s.hat_px('right', dx, 0, ear)
        s.hat_px('left', dx, 0, ear)


def gold_experience(s):
    """Oro con elmo, visiera nera dagli occhi verdi, coccinelle su petto, spalle e fronte, fasce verdi."""
    skin, dark, light = C(240, 190, 44), C(190, 142, 18), C(254, 230, 118)
    red, ink, green = C(216, 44, 44), C(26, 20, 16), C(52, 176, 96)
    s.box(BASE, skin)
    s.blk(HEAD, 'front', 1, 3, 6, 4, ink)
    s.hl(HEAD, 'front', 4, 2, 3, green)
    s.hl(HEAD, 'front', 4, 4, 5, green)
    s.put(HEAD, 'front', 1, 3, light)
    s.put(HEAD, 'front', 6, 3, light)
    s.hl(HEAD, 'front', 5, 2, 5, dark)
    s.hl(HEAD, 'front', 6, 3, 4, dark)
    s.vl(HEAD, 'front', 3, 6, 7, ink)
    s.hl(BODY, 'front', 3, 1, 6, dark)
    s.stamp(BODY_OV, 'front', 1, 1, LADYBUG, {'R': red, 'K': ink})
    s.stamp(ARMS_OV, 'front', 1, 0, LADYBUG3, {'R': red, 'K': ink})
    s.stamp(ARMS_OV, 'back', 1, 0, LADYBUG3, {'R': red, 'K': ink})
    s.band(BODY_OV, 8, 8, green)
    s.band(BODY_OV, 9, 11, dark)
    s.band(LEGS_OV, 0, 3, dark)
    s.band(ARMS_OV, 8, 8, green)
    s.band(ARMS_OV, 9, 11, dark)
    s.band(LEGS_OV, 8, 8, green)
    s.band(LEGS_OV, 9, 11, dark)
    s.vl(ARMS, 'front', 1, 3, 7, light)
    s.hair(C(248, 214, 84), [1, 1, 2, 2, 2, 2, 1, 1], side_rows=2, back_rows=3)
    s.stamp(HAT, 'front', 3, 0, ['RR'], {'R': red})
    s.hat_px('front', 3, 1, ink)
    s.hat_px('front', 4, 1, ink)


def silver_chariot(s):
    """Armatura d'argento: elmo con fessura a T, pettorale, spallacci, bracciali, schinieri e cimiero."""
    skin, dark, light = C(194, 202, 214), C(128, 140, 158), C(240, 244, 250)
    ink, steel, blue, gold = C(22, 26, 36), C(158, 170, 188), C(70, 96, 150), C(206, 174, 74)
    s.box(BASE, skin)
    s.hl(HEAD, 'front', 3, 1, 6, ink)                      # visiera a T
    s.hl(HEAD, 'front', 4, 1, 6, ink)
    s.vl(HEAD, 'front', 3, 5, 7, ink)
    s.vl(HEAD, 'front', 4, 5, 7, ink)
    s.hl(HEAD, 'front', 2, 0, 7, light)
    s.vl(HEAD, 'front', 0, 3, 7, dark)
    s.vl(HEAD, 'front', 7, 3, 7, dark)
    s.solid(BODY_OV, steel, ('front', 'right', 'left', 'back'))   # pettorale in rilievo
    s.hl(BODY_OV, 'front', 0, 0, 7, gold)
    s.vl(BODY_OV, 'front', 3, 1, 8, dark)
    s.vl(BODY_OV, 'front', 4, 1, 8, dark)
    s.hl(BODY_OV, 'front', 4, 0, 7, dark)
    for (px, py) in ((1, 2), (6, 2), (1, 6), (6, 6)):
        s.put(BODY_OV, 'front', px, py, light)
    s.band(BODY_OV, 9, 11, dark)                           # gonnellino a lamelle
    for dx in (0, 2, 4, 6):
        s.vl(BODY_OV, 'front', dx, 9, 11, steel)
    s.solid(ARMS_OV, steel, ('front', 'right', 'left', 'back'))
    s.band(ARMS_OV, 0, 2, light)                           # spallacci
    s.band(ARMS_OV, 3, 7, C(0, 0, 0, 0), shaded=False)     # braccio scoperto sotto la spalla
    s.band(ARMS_OV, 8, 11, steel)                          # guanti d'arme
    s.band(ARMS_OV, 8, 8, gold)
    s.band(LEGS_OV, 0, 2, steel)
    s.band(LEGS_OV, 3, 11, C(0, 0, 0, 0), shaded=False)
    s.band(LEGS_OV, 6, 11, steel)                          # schinieri e stivali
    s.hl(LEGS_OV, 'front', 5, 0, 3, light)
    s.hl(LEGS_OV, 'front', 6, 0, 3, gold)
    s.hair(C(196, 202, 214), [0] * 8, side_rows=1, back_rows=1, top_color=C(170, 180, 196))
    for dy in range(8):                                    # cimiero blu sul cappello
        s.hat_px('top', 3, dy, blue)
        s.hat_px('top', 4, dy, blue)
    for dy in range(6):
        s.hat_px('back', 3, dy, blue)
        s.hat_px('back', 4, dy, blue)


CHEVRON8 = CHEVRON


def magicians_red(s):
    """Rosso con testa d'uccello (becco e cresta di piume), collare di piume e bracciali dorati."""
    skin, dark, light = C(218, 50, 42), C(158, 28, 24), C(244, 100, 66)
    orange, yellow, ink = C(246, 140, 40), C(246, 204, 66), C(24, 12, 12)
    s.box(BASE, skin)
    s.blk(HEAD, 'front', 1, 3, 2, 4, yellow)               # occhi gialli
    s.blk(HEAD, 'front', 5, 3, 6, 4, yellow)
    s.put(HEAD, 'front', 2, 4, ink)
    s.put(HEAD, 'front', 5, 4, ink)
    s.blk(HEAD, 'front', 3, 4, 4, 6, orange)               # becco
    s.hl(HEAD, 'front', 4, 3, 4, yellow)
    s.hl(HEAD, 'front', 6, 3, 4, dark)
    for oy in (2, 5, 8):                                   # piume a V sul petto
        s.stamp(BODY, 'front', 0, oy, CHEVRON, {'X': light})
    for dx in range(0, 8, 2):                              # collare di piume
        s.vl(BODY_OV, 'front', dx, 0, 1, orange)
        s.vl(BODY_OV, 'front', dx + 1, 0, 1, yellow)
        s.vl(BODY_OV, 'back', dx, 0, 1, orange)
        s.vl(BODY_OV, 'back', dx + 1, 0, 1, yellow)
    s.band(BODY_OV, 9, 9, yellow)
    s.band(BODY_OV, 10, 11, dark)
    s.band(ARMS_OV, 3, 3, yellow)
    s.band(ARMS_OV, 8, 11, yellow)
    s.band(LEGS_OV, 0, 2, dark)
    s.band(LEGS_OV, 8, 8, yellow)
    s.band(LEGS_OV, 9, 11, dark)
    s.hair(orange, [1, 2, 2, 3, 3, 2, 2, 1], side_rows=2, back_rows=5)
    cols = (orange, skin, yellow)
    for dx in range(8):
        for dy in range(8):
            s.hat_px('top', dx, dy, cols[(dx + dy // 3) % 3])


def lattice(s, Fs, line, period=4):
    for F in _each(Fs):
        for face in SIDES:
            x, y, w, h = F[face]
            for dy in range(h):
                for dx in range(w):
                    if (dx + dy) % period == 0 or (dx - dy) % period == 0:
                        s.put(F, face, dx, dy, line)


def hierophant_green(s):
    """Verde con losanghe tipo smeraldo su corpo e arti, visiera luminosa, gemma sul petto e cresta."""
    skin, dark, deep = C(66, 172, 96), C(38, 120, 60), C(22, 80, 42)
    light, slit, gem = C(158, 234, 160), C(226, 255, 124), C(124, 255, 196)
    s.box(BASE, skin)
    lattice(s, [BODY] + ARMS + LEGS, dark)
    s.hl(HEAD, 'front', 3, 1, 6, slit)
    s.hl(HEAD, 'front', 4, 1, 6, deep)
    s.hl(HEAD, 'front', 6, 2, 5, deep)
    s.vl(HEAD, 'front', 0, 2, 7, dark)
    s.vl(HEAD, 'front', 7, 2, 7, dark)
    s.blk(BODY_OV, 'front', 3, 2, 4, 5, gem)
    s.put(BODY_OV, 'front', 3, 2, light)
    s.band(BODY_OV, 8, 8, deep)
    s.band(BODY_OV, 9, 11, dark)
    s.band(ARMS_OV, 8, 11, deep)
    s.band(LEGS_OV, 9, 11, deep)
    s.hair(C(54, 148, 80), [1, 2, 1, 2, 2, 1, 2, 1], side_rows=2, back_rows=3)
    s.hat_px('front', 3, 0, gem)
    s.hat_px('front', 4, 0, gem)


def spots(s, Fs, spot, freckle, seed):
    for F in _each(Fs):
        for face in F.keys():
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
    """Cremisi con macchie scure, secondo volto sulla fronte, capelli rosa, occhi chiari e brache nere."""
    skin, dark, light = C(194, 42, 68), C(98, 16, 42), C(242, 126, 146)
    bone, ink, eye = C(248, 216, 222), C(20, 8, 14), C(255, 242, 176)
    s.box(BASE, skin)
    for i, F in enumerate([HEAD, BODY] + ARMS + LEGS):
        spots(s, F, dark, light, i * 5)
    s.hl(BODY, 'front', 3, 1, 6, dark)
    s.vl(BODY, 'front', 3, 4, 8, dark)
    s.vl(BODY, 'front', 4, 4, 8, dark)
    s.blk(HEAD, 'front', 2, 0, 5, 1, bone)                 # il secondo volto sulla fronte
    s.put(HEAD, 'front', 3, 1, ink)
    s.put(HEAD, 'front', 4, 1, ink)
    s.blk(HEAD, 'front', 1, 3, 2, 4, eye)                  # volto principale
    s.blk(HEAD, 'front', 5, 3, 6, 4, eye)
    s.put(HEAD, 'front', 2, 4, ink)
    s.put(HEAD, 'front', 5, 4, ink)
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.put(HEAD, 'front', 2, 7, bone)
    s.put(HEAD, 'front', 5, 7, bone)
    s.band(BODY_OV, 8, 8, ink)
    s.band(BODY_OV, 9, 11, C(60, 12, 30))
    s.band(LEGS_OV, 0, 3, C(60, 12, 30))
    s.band(ARMS_OV, 9, 11, ink)
    s.band(LEGS_OV, 10, 11, ink)
    s.hair(C(236, 130, 160), [2, 3, 2, 3, 3, 2, 3, 2], side_rows=3, back_rows=6)
    s.hat_px('top', 3, 0, C(255, 214, 224))
    s.hat_px('top', 4, 0, C(255, 214, 224))


def sticky_fingers(s):
    """Blu con cerniere bianche su corpo, braccia, gambe e volto, cappuccio blu notte con cresta."""
    skin, dark, ink = C(60, 128, 228), C(36, 86, 180), C(22, 30, 70)
    white, gold = C(248, 248, 254), C(246, 206, 78)
    s.box(BASE, skin)
    for F, cx in ((BODY, 3), (BODY_OV, 3)):
        for dy in range(12):
            s.put(F, 'front', cx + (dy % 2), dy, white)
            s.put(F, 'back', cx + (dy % 2), dy, white)
    for F in ARMS_OV + LEGS_OV:
        for dy in range(12):
            s.put(F, 'front', 1 + (dy % 2), dy, white)
            s.put(F, 'back', 1 + (dy % 2), dy, white)
    s.put(BODY_OV, 'front', 3, 0, gold)
    s.put(BODY_OV, 'front', 4, 0, gold)
    s.hl(HEAD, 'front', 3, 1, 6, ink)                      # fessura degli occhi
    s.hl(HEAD, 'front', 4, 1, 6, ink)
    s.hl(HEAD, 'front', 3, 1, 2, white)
    s.hl(HEAD, 'front', 3, 5, 6, white)
    for dx in range(1, 7):                                 # cerniera sulla bocca
        s.put(HEAD, 'front', dx, 6, white if dx % 2 == 0 else dark)
    for dy in range(0, 3):                                 # cerniera sulla fronte
        s.put(HEAD, 'front', 3 + (dy % 2), dy, white)
    s.band(BODY_OV, 9, 11, ink)
    s.band(ARMS_OV, 9, 11, ink)
    s.band(LEGS_OV, 0, 1, ink)
    s.band(LEGS_OV, 10, 11, ink)
    for dy in range(9, 12):                                # cerniera sul busto resta visibile sopra il nero
        s.put(BODY_OV, 'front', 3 + (dy % 2), dy, white)
    s.hair(C(24, 36, 88), [2, 2, 2, 3, 3, 2, 2, 2], side_rows=3, back_rows=5)
    for dy in range(7):
        s.hat_px('back', 3, dy, C(44, 66, 140))
        s.hat_px('back', 4, dy, C(44, 66, 140))


def stone_free(s):
    """Grigio-azzurro avvolto da fili: righe diagonali sulla pelle e fasce di filo in rilievo su busto e arti."""
    skin, dark = C(104, 140, 182), C(66, 98, 140)
    thread, ink, eye = C(240, 248, 254), C(24, 26, 36), C(150, 234, 254)
    s.box(BASE, skin)
    for F in [BODY] + ARMS + LEGS:                         # righe diagonali radi
        for face in SIDES:
            x, y, w, h = F[face]
            for dy in range(h):
                for dx in range(w):
                    if (dx + dy) % 8 == 0:
                        s.put(F, face, dx, dy, thread)
                    elif (dx + dy) % 8 == 4:
                        s.put(F, face, dx, dy, dark)
    for F in ARMS_OV + LEGS_OV:                            # fasce di filo a spirale (come bende)
        for dy in (1, 4, 7):
            s.band(F, dy, dy, thread)
    for dy in (1, 4, 7):
        s.band(BODY_OV, dy, dy, thread)
    s.hl(HEAD, 'front', 2, 1, 2, ink)
    s.hl(HEAD, 'front', 2, 5, 6, ink)
    s.hl(HEAD, 'front', 3, 1, 2, eye)
    s.hl(HEAD, 'front', 3, 5, 6, eye)
    s.hl(HEAD, 'front', 4, 1, 2, ink)
    s.hl(HEAD, 'front', 4, 5, 6, ink)
    s.hl(HEAD, 'front', 6, 2, 5, ink)
    s.band(BODY_OV, 9, 9, ink)
    s.band(BODY_OV, 10, 11, dark)
    s.band(ARMS_OV, 10, 11, dark)
    s.band(LEGS_OV, 10, 11, dark)
    s.hair(C(26, 28, 40), [2, 3, 2, 3, 3, 2, 3, 2], side_rows=3, back_rows=5)


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
        write_png(ASSETS / ('textures/entity/stand/%s.png' % name), 64, 64, s.p)
        write_png(ASSETS / ('textures/gui/hud/stand_%s.png' % name), 16, 16, face_icon(s))
    make_hud_icons()
    print('Texture generate: %d stand + icone HUD' % len(STANDS))


if __name__ == '__main__':
    main()
