"""Геометрия изометрической плитки TheoTown (32x16) и осевые линии дорог.

Система координат
-----------------
Экран: плитка -- ромб 32x16 с углами
    T (верх)    = (16,  0)
    R (право)   = (32,  8)
    B (низ)     = (16, 16)
    L (лево)    = ( 0,  8)

"Земля" (s, t) -- аффинное отображение плоскости земли:
    x = 16 + 16*s - 16*t
    y =      8*s +  8*t
s, t в [0, 1] покрывают плитку. Стороны (коннекторы) и их середины:
    NE  t = 0   (0.5, 0.0)   -- сосед (i, j-1), экран вверх-вправо
    SE  s = 1   (1.0, 0.5)   -- сосед (i+1, j), экран вниз-вправо
    SW  t = 1   (0.5, 1.0)   -- сосед (i, j+1), экран вниз-влево
    NW  s = 0   (0.0, 0.5)   -- сосед (i-1, j), экран вверх-влево

Индекс кадра дороги = сумма подключённых сторон (проверено на графике
штатных дорог TheoTown):
    SE = 1, NE = 2, NW = 4, SW = 8
    кадр 0  -- изолированная плитка, кадр 15 -- перекрёсток (все стороны),
    кадр 5  -- прямая NW-SE (вдоль оси s, "вертикаль" экрана),
    кадр 10 -- прямая NE-SW (вдоль оси t, "горизонталь" экрана).

Дорожное полотно рисуется как объединение полос: для каждого
подключённого направления берётся полоса постоянной ширины вдоль этого
направления, обрезанная по половине плитки (если напротив стыка нет) --
так получаются квадратные митры на поворотах и Т-образных стыках,
как в штатных дорогах игры.

Поворот дороги на 90 градусов (обмен s <-> t) в пикселях равен зеркалу
по горизонтали: x -> 32 - x, y -> y. Это используется для генерации
украшений во второй ориентации.
"""

from __future__ import annotations

import numpy as np

TILE_W = 32
TILE_H = 16

BIT = {"SE": 1, "NE": 2, "NW": 4, "SW": 8}
CONN = {"NE": (0.5, 0.0), "SE": (1.0, 0.5), "SW": (0.5, 1.0), "NW": (0.0, 0.5)}
OPP = {"NE": "SW", "SW": "NE", "SE": "NW", "NW": "SE"}
ORDER = ("NE", "SE", "SW", "NW")

#: для каждого направления: (ось поперёк = 's' или 't', сторона обрезки)
AXIS = {
    "NE": ("s", "<="),   # идёт вдоль t к t=0
    "SW": ("s", ">="),
    "SE": ("t", ">="),   # идёт вдоль s к s=1
    "NW": ("t", "<="),
}

BIT_TO_NAME = {v: k for k, v in BIT.items()}


def frame_mask(frame: int) -> int:
    """Индекс кадра 0..15 == маска соединений."""
    return frame & 15


def mask_name(mask: int) -> str:
    """Строка вида 'NE+SW' для отладки."""
    return "+".join(c for c in ORDER if mask & BIT[c]) or "-"


def st_grid(ss: int = 1):
    """Сетка (s, t) для пиксельных центров спрайта, ss -- суперсэмплинг."""
    xs = (np.arange(TILE_W * ss) + 0.5) / ss
    ys = (np.arange(TILE_H * ss) + 0.5) / ss
    gx, gy = np.meshgrid(xs, ys)
    s = (gy / 8.0 + (gx - 16.0) / 16.0) / 2.0
    t = (gy / 8.0 - (gx - 16.0) / 16.0) / 2.0
    return s, t


def tile_inside(s, t, pad: float = 0.0):
    """Маска пикселей внутри ромба плитки."""
    return (s >= -pad) & (s <= 1.0 + pad) & (t >= -pad) & (t <= 1.0 + pad)


def region(s, t, mask: int, half_width: float, cap: bool = True):
    """Полоса(ы) дороги шириной 2*half_width для маски соединений.

    Для каждого подключённого направления берётся полоса поперёк оси;
    если напротив стыка нет, полоса обрезается по середине плитки и
    дополняется округлым "тупиком" в центре.
    """
    conns = [c for c in ORDER if mask & BIT[c]]
    if not conns:
        if not cap:
            return np.zeros(np.shape(s), dtype=bool)
        return (s - 0.5) ** 2 + (t - 0.5) ** 2 <= (half_width) ** 2

    m = np.zeros(np.shape(s), dtype=bool)
    for c in conns:
        across, side = AXIS[c]
        pair = OPP[c]
        through = bool(mask & BIT[pair])
        band = np.abs((s if across == "s" else t) - 0.5) <= half_width
        if through:
            m |= band
        else:
            if across == "s":
                m |= band & ((t <= 0.5) if side == "<=" else (t >= 0.5))
            else:
                m |= band & ((s <= 0.5) if side == "<=" else (s >= 0.5))
    if cap and any(not (mask & BIT[OPP[c]]) for c in conns):
        m |= (s - 0.5) ** 2 + (t - 0.5) ** 2 <= (half_width) ** 2
    return m


def line_mask(s, t, along_t: bool, offset: float, half_width: float,
              dash: float | None = None, period: float = 0.5, phase: float = 0.0):
    """Полоса вдоль дороги: линия постоянной координаты с разрывами.

    along_t=True  -- дорога идёт вдоль t, линия имеет постоянную s.
    along_t=False -- наоборот.
    dash=None     -- сплошная линия.
    """
    across = s if along_t else t
    along = t if along_t else s
    m = np.abs(across - (0.5 + offset)) <= half_width
    if dash is not None:
        m = m & (np.mod(along + phase, period) <= dash)
    return m


def downsample(mask_ss: np.ndarray, ss: int, thresh: float = 0.5) -> np.ndarray:
    """Суперсэмплированная булева маска -> пиксельная (голосование)."""
    h, w = mask_ss.shape[0] // ss, mask_ss.shape[1] // ss
    m = mask_ss.reshape(h, ss, w, ss).mean(axis=(1, 3))
    return m > thresh


def erode(mask: np.ndarray, n: int = 1) -> np.ndarray:
    """Эрозия булевой маски на n пикселей (внутренняя кромка)."""
    out = mask.copy()
    for _ in range(n):
        e = out.copy()
        e[1:, :] &= out[:-1, :]
        e[:-1, :] &= out[1:, :]
        e[:, 1:] &= out[:, :-1]
        e[:, :-1] &= out[:, 1:]
        out = e
    return out


def dilate(mask: np.ndarray, n: int = 1) -> np.ndarray:
    """Дилатация булевой маски на n пикселей."""
    out = mask.copy()
    for _ in range(n):
        d = out.copy()
        d[1:, :] |= out[:-1, :]
        d[:-1, :] |= out[1:, :]
        d[:, 1:] |= out[:, :-1]
        d[:, :-1] |= out[:, 1:]
        out = d
    return out
