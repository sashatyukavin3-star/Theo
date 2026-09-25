"""Палитры, шум и низкоуровневая упаковка спрайтов.

Стиль намеренно повторяет графику штатных дорог TheoTown: асфальт
тёмно-серый с шумом, бордюр светлый, тротуар светло-серый, разметка
почти белая, обочины -- земля/гравий.
"""

from __future__ import annotations

import numpy as np
from PIL import Image

TILE_W = 32
TILE_H = 16

#: базовые материалы (RGB) -- палитра подогнана под штатные дороги TheoTown
MATERIALS = {
    "asphalt": (88, 77, 75),
    "asphalt_warm": (94, 82, 79),
    "asphalt_dark": (66, 58, 57),
    "concrete": (150, 148, 144),
    "gravel": (158, 145, 122),
    "dirt": (126, 106, 84),
    "pavement": (159, 159, 159),
    "pavement_dark": (133, 133, 133),
    "kerb": (183, 183, 183),
    "white": (228, 229, 231),
    "yellow": (226, 196, 84),
    "rail": (168, 168, 170),
    "rail_dark": (96, 96, 100),
    "post": (74, 74, 78),
    "stone": (128, 122, 114),
    "stone_dark": (88, 84, 78),
    "hole": (18, 18, 20),
    "grass": (104, 138, 74),
    "grass_dark": (88, 120, 62),
    "water": (78, 126, 178),
}


def noise2(x, y, seed: int = 0):
    """Детерминированный шум в [-1, 1] для каждого пикселя."""
    x = np.asarray(x, dtype=np.float64)
    y = np.asarray(y, dtype=np.float64)
    v = np.sin(x * 12.9898 + y * 78.233 + (seed + 1) * 37.719) * 43758.5453
    return (v - np.floor(v)) * 2.0 - 1.0


def pixel_grid(w: int = TILE_W, h: int = TILE_H):
    """Сетки индексов пикселей."""
    gx, gy = np.meshgrid(np.arange(w), np.arange(h))
    return gx, gy


def tint(base, amount: float = 0.0):
    """Цвет с аддитивной поправкой (float -> uint8 кортеж)."""
    return tuple(int(np.clip(c + amount, 0, 255)) for c in base)


def blend(a, b, t: float):
    """Линейное смешивание двух RGB."""
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))


def new_canvas(w: int = TILE_W, h: int = TILE_H):
    """Пустой RGBA-холст."""
    return np.zeros((h, w, 4), dtype=np.uint8)


def paint(canvas, mask, base, seed: int = 0, amp: float = 7.0, y_offset: int = 0):
    """Залить маску материалом с шумом (маска -- булев массив h x w)."""
    if not mask.any():
        return
    gx, gy = pixel_grid(canvas.shape[1], canvas.shape[0])
    n = noise2(gx, gy + y_offset, seed)
    col = np.empty(mask.shape + (3,), dtype=np.float64)
    for i in range(3):
        col[..., i] = base[i] + n * amp
    col = np.clip(col, 0, 255).astype(np.uint8)
    canvas[mask, 0:3] = col[mask]
    canvas[mask, 3] = 255


def paint_solid(canvas, mask, color):
    """Залить маску одним цветом (без шума)."""
    if not mask.any():
        return
    canvas[mask, 0:3] = np.array(color, dtype=np.uint8)
    canvas[mask, 3] = 255


def compose_above(canvas, overlay):
    """Наложить RGBA-спрайт поверх холста (простое копирование альфы)."""
    a = overlay[:, :, 3] > 0
    canvas[a] = overlay[a]
    return canvas


def to_image(arr) -> Image.Image:
    """numpy RGBA -> PIL.Image."""
    return Image.fromarray(np.ascontiguousarray(arr), "RGBA")


def frames_to_sheet(frames, bg=None) -> Image.Image:
    """Склеить кадры 32x16 (или 32xN одинаковой высоты) в один лист."""
    if not frames:
        raise ValueError("нет кадров")
    h = frames[0].shape[0]
    w = frames[0].shape[1]
    sheet = np.zeros((h, w * len(frames), 4), dtype=np.uint8)
    for i, f in enumerate(frames):
        sheet[: f.shape[0], i * w: i * w + f.shape[1]] = f
    return to_image(sheet)


def sprite_bbox(arr):
    """Границы непрозрачной части (x0, y0, x1, y1) или None."""
    ys, xs = np.where(arr[:, :, 3] > 0)
    if len(xs) == 0:
        return None
    return int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max())
