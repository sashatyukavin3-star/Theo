"""Дорожные украшения: переходы, стоп-линии, «лежачие полицейские», фонари.

Украшение -- это набор анимаций (кадров) плюс таблица «какой кадр дороги
какие анимации показывает» (frame animation indices). Используется та же
логика, что и в штатном плагине-примере TheoTown: индекс 0 -- полоса по
ребру t=0 (северо-восток), 1 -- по ребру s=0 (северо-запад) на заднем
слое, и аналогично для переднего слоя (fg).

Ориентации дороги:
    кадр 5  -- дорога вдоль оси s (экранная "вертикаль")
    кадр 10 -- дорога вдоль оси t (экранная "горизонталь")
Все прочие кадры -- повороты, стыки и тупики.
"""

from __future__ import annotations

import numpy as np

from . import art, iso

SS = 3
MAT = art.MATERIALS

#: индексы анимаций по кадрам дороги 0..15 (см. пояснение выше)
INDICES_STRAIGHT_ONLY = [
    [], [], [], [],
    [], [0], [], [],
    [], [], [1], [],
    [], [], [], [],
]
INDICES_ROADSIDE = [
    [], [], [], [],
    [], [1], [], [],
    [], [], [0], [],
    [], [], [], [],
]


def _sprite(layers, seed: int = 0, height: int = iso.TILE_H):
    """Собрать спрайт из слоёв [(суперсэмпл-маска, материал, амплитуда шума, сдвиг seed)]."""
    canvas = art.new_canvas(iso.TILE_W, height)
    for i, (mask_ss, mat, amp) in enumerate(layers):
        m = iso.downsample(mask_ss, SS, thresh=0.42)
        if m.any():
            base = MAT[mat] if isinstance(mat, str) else mat
            art.paint(canvas, m, base, seed=seed + i, amp=amp)
    return canvas


# ---------------------------------------------------------------------------
# разметка: переход, стоп-линия, «лежачий полицейский»
# ---------------------------------------------------------------------------
def _axes(along_t: bool):
    """Пиксельные координаты (вдоль дороги, поперёк дороги, внутри плитки).

    Считаем сразу в пикселях (SS=1): так разметка получается чистой,
    без рваных краёв от суперсэмплинга -- линии идут ровно 2:1, как грани
    изометрической плитки.
    """
    s, t = iso.st_grid(1)
    inside = iso.tile_inside(s, t)
    if along_t:      # дорога вдоль оси t
        return t, s, inside
    return s, t, inside


def _paint(canvas, mask, color, seed=0, amp=2.0):
    art.paint(canvas, mask, color, seed=seed, amp=amp)
    return canvas


def zebra(style: dict, seed: int = 0):
    """2 кадра пешеходного перехода.

    Кадр 0 -- дорога вдоль оси s (игровой кадр 5), кадр 1 -- вдоль оси t
    (игровой кадр 10). Полосатый настил идёт поперёк дороги, белые полосы
    вытянуты вдоль направления движения.
    """
    hw = style["hw"] - 0.01
    out = []
    for along_t in (False, True):
        along, across, inside = _axes(along_t)
        band = (np.abs(along - 0.5) <= 0.17) & (np.abs(across - 0.5) <= hw) & inside
        u = (across - (0.5 - hw)) / (2 * hw)          # 0..1 поперёк дороги
        stripes = np.mod(u * 7.0, 1.0) < 0.56
        out.append(_paint(art.new_canvas(), band & stripes, MAT["white"], seed))
    return out


def stopline(style: dict, seed: int = 0):
    """2 кадра стоп-линии (широкая белая полоса поперёк дороги)."""
    hw = style["hw"] - 0.01
    out = []
    for along_t in (False, True):
        along, across, inside = _axes(along_t)
        bar = (np.abs(along - 0.42) <= 0.075) & (np.abs(across - 0.5) <= hw) & inside
        out.append(_paint(art.new_canvas(), bar, MAT["white"], seed))
    return out


def speedbump(style: dict, seed: int = 0):
    """2 кадра «лежачего полицейского»: жёлтая полоса с чёрными вставками."""
    hw = style["hw"] - 0.01
    out = []
    for along_t in (False, True):
        along, across, inside = _axes(along_t)
        body = (np.abs(along - 0.5) <= 0.11) & (np.abs(across - 0.5) <= hw) & inside
        u = (across - (0.5 - hw)) / (2 * hw)
        dark = np.mod(u * 6.0, 1.0) < 0.5
        canvas = art.new_canvas()
        _paint(canvas, body, MAT["yellow"], seed, amp=3.0)
        _paint(canvas, body & dark, (54, 54, 58), seed + 1, amp=2.0)
        out.append(canvas)
    return out


LAMP_H = 24           # высота спрайта фонаря
LAMP_ANCHOR = 16      # handle y: строка спрайта, соответствующая y=0 плитки


def _lamp_frame(flip: bool, seed: int = 0):
    """Спрайт уличного фонаря.

    Опора стоит на тротуаре у кромки плитки, кронштейн с плафоном заходит
    над дорогой. flip=False -- для дороги вдоль оси t (кадр 10),
    flip=True -- вдоль оси s (кадр 5).
    """
    canvas = art.new_canvas(iso.TILE_W, LAMP_H)
    y0 = LAMP_ANCHOR                   # строка спрайта == y=0 плитки
    base = (10, 3)                     # опора: тротуар у северо-западной кромки

    def px(x, y, color, alpha=255):
        if 0 <= x < iso.TILE_W and 0 <= y < LAMP_H:
            canvas[y, x] = (*color, alpha)

    def put(x, y, color, alpha=255):
        x = (iso.TILE_W - 1 - x) if flip else x
        px(int(x), int(y), color, alpha)

    bx, by = base
    # тень у основания
    for k in range(-2, 3):
        put(bx + k, y0 + by + 2, MAT["asphalt_dark"], 110)
    put(bx - 1, y0 + by + 1, MAT["stone_dark"])
    put(bx + 2, y0 + by + 1, MAT["stone_dark"])
    # столб
    for k in range(10):
        put(bx, y0 + by - k, MAT["post"])
        put(bx + 1, y0 + by - k, MAT["post"])
    # кронштейн к дороге
    ax, ay = bx + 2, y0 + by - 9
    for k in range(6):
        put(ax + k, ay + int(k * 0.5), MAT["post"])
        put(ax + k, ay + 1 + int(k * 0.5), MAT["post"])
    # плафон
    hx = ax + 6
    for k in range(4):
        put(hx + k, ay + 3, MAT["post"])
    for k in range(4):
        put(hx + k, ay + 4, (252, 244, 198))
    for k in range(3):
        put(hx + 1 + k, ay + 5, (250, 240, 190), 90)
    return canvas


def streetlight(style: dict, seed: int = 0):
    """2 кадра: 0 -- для дороги вдоль оси t, 1 -- вдоль оси s."""
    return [_lamp_frame(False, seed), _lamp_frame(True, seed)]


# ---------------------------------------------------------------------------
# спецификации украшений для JSON
# ---------------------------------------------------------------------------
def decorations_for(style: dict, prefix: str, seed: int = 0):
    """Список спецификаций украшений (кадры + JSON-поля) для одного стиля."""
    specs = []

    zeb = zebra(style, seed)
    specs.append(dict(
        key="crosswalk",
        frames=zeb,
        indices=INDICES_STRAIGHT_ONLY,
        draft=dict(
            title="Crosswalk[ru]Пешеходный переход",
            text="Zebra crossing for your streets.[ru]«Зебра» для пешеходов.",
            price=40, **{"monthly price": 1},
            **{"line tool": True, "min dirs": 2, "max dirs": 2, "symmetric dirs": True},
        ),
    ))

    stop = stopline(style, seed)
    specs.append(dict(
        key="stopline",
        frames=stop,
        indices=INDICES_STRAIGHT_ONLY,
        draft=dict(
            title="Stop line[ru]Стоп-линия",
            text="Marks where cars have to stop.[ru]Показывает, где машины должны остановиться.",
            price=25, **{"monthly price": 1},
            **{"line tool": True, "min dirs": 2, "max dirs": 2, "symmetric dirs": True},
        ),
    ))

    bump = speedbump(style, seed)
    specs.append(dict(
        key="speedbump",
        frames=bump,
        indices=INDICES_STRAIGHT_ONLY,
        draft=dict(
            title="Speed bump[ru]Лежачий полицейский",
            text="Slows down traffic on a road (speed x0.6).[ru]Снижает скорость машин на дороге (x0.6).",
            price=60, **{"monthly price": 1}, speed=0.6,
            **{"line tool": True, "min dirs": 2, "max dirs": 2, "symmetric dirs": True},
        ),
    ))

    lamp = streetlight(style, seed)
    specs.append(dict(
        key="streetlight",
        frames=lamp,
        indices=INDICES_ROADSIDE,
        anchor=LAMP_ANCHOR,
        height=LAMP_H,
        draft=dict(
            title="Street light[ru]Уличный фонарь",
            text="Lights up the road at night.[ru]Освещает дорогу ночью.",
            price=80, **{"monthly price": 2}, speed=1.0,
            **{"line tool": True, "allow road crossing": False},
        ),
    ))
    return specs
