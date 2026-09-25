"""Генерация спрайт-листов дорог TheoTown.

Каждый тип дороги описывается стилем (ширина, покрытие, тротуар, обочина,
разметка, отбойники) и превращается в лист из 16 кадров 32x16 (или 32x32
для дорог с отбойниками -- верхняя половина спрайта отводится под
ограждение, как у штатной скоростной дороги TheoTown).
"""

from __future__ import annotations

import numpy as np

from . import art, iso

SS = 3
MAT = art.MATERIALS

# ---------------------------------------------------------------------------
# стили дорог
# ---------------------------------------------------------------------------
# hw        -- половина ширины проезжей части (в единицах s/t)
# walk      -- ширина тротуара снаружи проезжей части
# shoulder  -- ширина обочины (гравий/бетон) снаружи тротуара
# marks     -- полосы разметки: offset (поперёк), w (полуширина),
#              dash/period (штрих), color
# tall      -- спрайт 32x32, верхняя половина -- отбойники
# rail      -- рисовать отбойники (вместе с tall)

ROAD_STYLES = {
    "gravel": dict(
        surface="gravel", hw=0.385, walk=0.0, shoulder=0.100, shoulder_mat="dirt",
        marks=[],
    ),
    "rural": dict(
        surface="asphalt_warm", hw=0.400, walk=0.0, shoulder=0.085, shoulder_mat="gravel",
        marks=[dict(offset=0.0, w=0.075, dash=0.26, period=0.50, phase=-0.14, color="white")],
    ),
    "street": dict(
        surface="asphalt", hw=0.400, walk=0.070, shoulder=0.0, shoulder_mat="dirt",
        marks=[dict(offset=0.0, w=0.075, dash=0.26, period=0.50, phase=-0.14, color="white")],
    ),
    "street1": dict(
        surface="asphalt", hw=0.425, walk=0.048, shoulder=0.0, shoulder_mat="dirt",
        marks=[
            dict(offset=0.0, w=0.080, dash=0.30, period=0.50, phase=-0.16, color="white"),
            dict(offset=-0.450, w=0.085, dash=None, color="white"),
            dict(offset=0.450, w=0.085, dash=None, color="white"),
        ],
    ),
    "avenue1": dict(
        surface="asphalt", hw=0.440, walk=0.045, shoulder=0.0, shoulder_mat="dirt",
        marks=[
            dict(offset=0.0, w=0.090, dash=None, color="yellow"),
            dict(offset=-0.225, w=0.070, dash=0.30, period=0.50, phase=-0.16, color="white"),
            dict(offset=0.225, w=0.070, dash=0.30, period=0.50, phase=-0.16, color="white"),
        ],
    ),
    "avenue": dict(
        surface="asphalt", hw=0.440, walk=0.045, shoulder=0.0, shoulder_mat="dirt",
        marks=[
            dict(offset=0.0, w=0.090, dash=None, color="yellow"),
            dict(offset=-0.465, w=0.075, dash=None, color="white"),
            dict(offset=0.465, w=0.075, dash=None, color="white"),
        ],
    ),
    "express": dict(
        surface="asphalt", hw=0.440, walk=0.0, shoulder=0.050, shoulder_mat="concrete",
        marks=[
            dict(offset=0.0, w=0.090, dash=None, color="yellow"),
            dict(offset=-0.225, w=0.070, dash=0.30, period=0.50, phase=-0.16, color="white"),
            dict(offset=0.225, w=0.070, dash=0.30, period=0.50, phase=-0.16, color="white"),
            dict(offset=-0.472, w=0.060, dash=None, color="white"),
            dict(offset=0.472, w=0.060, dash=None, color="white"),
        ],
    ),
    "motorway": dict(
        surface="asphalt", hw=0.300, walk=0.0, shoulder=0.045, shoulder_mat="concrete",
        tall=True, rail=True,
        marks=[
            dict(offset=0.0, w=0.090, dash=None, color="yellow"),
            dict(offset=-0.245, w=0.055, dash=None, color="white"),
            dict(offset=0.245, w=0.055, dash=None, color="white"),
        ],
    ),
}

RAIL_LIFT = 8          # на сколько пикселей отбойник поднят над дорогой
RAIL_THICK = 0.070     # толщина полосы отбойника (в единицах s/t)


# ---------------------------------------------------------------------------
# кадры дороги
# ---------------------------------------------------------------------------
def _layers(mask: int, style: dict):
    s, t = iso.st_grid(SS)
    inside = iso.tile_inside(s, t)
    hw = style["hw"]
    walk = style.get("walk", 0.0)
    shoulder = style.get("shoulder", 0.0)

    core = iso.region(s, t, mask, hw) & inside
    road = iso.region(s, t, mask, 0) & inside
    walk_region = iso.region(s, t, mask, hw + walk, cap=True)
    sh_region = iso.region(s, t, mask, hw + walk + shoulder, cap=True)
    rail_region = iso.region(s, t, mask, hw + walk + shoulder + RAIL_THICK, cap=True)

    if walk:
        walk_band = walk_region & ~core & inside
    else:
        walk_band = np.zeros_like(core)
    shoulder_band = sh_region & ~(core | walk_band) & inside
    rail_band = rail_region & ~(core | walk_band | shoulder_band) & inside

    marks = []
    if mask in (5, 10):  # разметка только на прямых проездах
        along_t = mask == 10
        for spec in style.get("marks", []):
            m = iso.line_mask(
                s, t, along_t, spec["offset"], spec["w"],
                dash=spec.get("dash"), period=spec.get("period", 0.5),
                phase=spec.get("phase", 0.0),
            )
            marks.append((m & core, spec["color"]))

    def ds(m):
        return iso.downsample(m, SS)

    return dict(
        road=ds(core),
        walk=ds(walk_band),
        shoulder=ds(shoulder_band),
        rail=ds(rail_band) if style.get("rail") else None,
        marks=[(ds(m), c) for m, c in marks],
    )


def render_road_frame(mask: int, style: dict, seed: int = 0) -> np.ndarray:
    """Один кадр дороги: RGBA массив 32x16 либо 32x32 (для tall-дорог)."""
    lay = _layers(mask, style)
    tall = bool(style.get("tall"))
    h = iso.TILE_H * 2 if tall else iso.TILE_H
    canvas = art.new_canvas(iso.TILE_W, h)
    y0 = iso.TILE_H if tall else 0  # смещение дорожного слоя в высоком спрайте
    tile = canvas[y0:y0 + iso.TILE_H]

    def put(paint_mask, base, amp=7.0, seed_off=0):
        if paint_mask.any():
            art.paint(tile, paint_mask, MAT[base], seed=seed + seed_off, amp=amp)

    if lay["shoulder"].any():
        put(lay["shoulder"], style.get("shoulder_mat", "dirt"), 9.0, 1)
    if lay["walk"].any():
        put(lay["walk"], "pavement", 8.0, 2)
        put(iso.erode(lay["walk"], 1) & ~lay["walk"], "pavement_dark", 4.0, 3)
    put(lay["road"], style["surface"], 7.0, 0)
    if lay["walk"].any():
        kerb = iso.dilate(lay["road"], 1) & lay["walk"]
        put(kerb, "kerb", 5.0, 4)
    for mm, color in lay["marks"]:
        sel = mm & lay["road"]
        if sel.any():
            art.paint_solid(tile, sel, MAT[color])
    if lay["rail"] is not None and lay["rail"].any():
        _draw_rail(canvas, lay["rail"])

    return canvas


def _shift_up(mask: np.ndarray, dy: int) -> np.ndarray:
    """Сдвиг маски вверх на dy пикселей (без переноса по кругу)."""
    out = np.zeros_like(mask)
    if dy <= 0:
        out[: mask.shape[0] + dy] = mask[-dy:] if dy else mask
    else:
        out[dy:] = mask[: mask.shape[0] - dy]
    return out


def _draw_rail(canvas: np.ndarray, rail: np.ndarray):
    """Отбойник: балка, поднятая над дорогой, со стойками и тенью."""
    tile_h, tile_w = rail.shape
    y0 = iso.TILE_H  # нижняя половина спрайта -- плитка
    beam = _shift_up(rail, -RAIL_LIFT)
    beam_lo = _shift_up(rail, -RAIL_LIFT + 2)
    shadow = _shift_up(rail, -RAIL_LIFT + 3)

    def stamp(mask, color, alpha=255):
        for i, j in zip(*np.where(mask)):
            ty = y0 + i
            if 0 <= ty < canvas.shape[0]:
                canvas[ty, j] = (*color, alpha)

    stamp(shadow, MAT["asphalt_dark"], 170)
    stamp(beam, MAT["rail"])
    stamp(beam_lo, MAT["rail_dark"])
    # стойки каждые 8 пикселей по низу балки
    posts = np.zeros_like(rail)
    for j in range(2, tile_w, 8):
        posts[:, j] = rail[:, j]
    for i, j in zip(*np.where(posts)):
        for dy in range(-RAIL_LIFT + 1, 1):
            ty = y0 + i + dy
            if 0 <= ty < canvas.shape[0]:
                canvas[ty, j] = (*MAT["post"], 255)


def build_road_frames(style: dict, seed: int = 0):
    """16 кадров дороги (индекс кадра == маска соединений)."""
    return [render_road_frame(mask, style, seed=seed) for mask in range(16)]


def build_road_sheet(style: dict, seed: int = 0):
    """(PIL-лист, список numpy-кадров) для типа дороги."""
    frames = build_road_frames(style, seed=seed)
    return art.frames_to_sheet(frames), frames


# ---------------------------------------------------------------------------
# тоннели и светофоры
# ---------------------------------------------------------------------------
def build_tunnel_frames(seed: int = 0):
    """4 кадра тоннеля 16x19: портал со стенками и тёмный проём."""
    h, w = 19, 16
    frames = []
    for flip in (False, True):
        a = np.zeros((h, w, 4), dtype=np.uint8)
        for y in range(h):
            left = max(0, 14 - 2 * y)
            right = min(w - 1, 37 - 2 * y)
            for x in range(left, right + 1):
                base = MAT["stone"]
                if (x + y) % 7 in (0, 1):
                    base = MAT["stone_dark"]
                j = int((np.sin(x * 12.9898 + y * 78.233 + seed) * 43758.5453) % 1 * 16) - 8
                a[y, x] = (
                    int(np.clip(base[0] + j, 0, 255)),
                    int(np.clip(base[1] + j, 0, 255)),
                    int(np.clip(base[2] + j, 0, 255)),
                    255,
                )
            if left < w:
                a[y, left:min(w, left + 2), 0:3] = MAT["stone_dark"]
        frames.append(a)
    for flip in (False, True):
        a = np.zeros((h, w, 4), dtype=np.uint8)
        for y in range(h):
            left = max(0, 14 - 2 * y)
            right = min(w - 1, 37 - 2 * y)
            for x in range(left, right + 1):
                a[y, x, 0:3] = MAT["hole"]
                a[y, x, 3] = 255
            if 0 <= left < w:
                col = MAT["white"] if (y // 2) % 2 == 0 else (176, 62, 56)
                a[y, left, 0:3] = col
                if left + 1 < w:
                    a[y, left + 1, 0:3] = col
        frames.append(np.fliplr(a) if flip else a)
    # кадры: 0,1 -- левые части портала (SE/SW), 2,3 -- зеркальные
    return [frames[0], np.fliplr(frames[0]), frames[2], np.fliplr(frames[2])]


def build_traffic_lights(seed: int = 0):
    """4 кадра светофоров 32x32 с фазами (вариант как у штатных дорог)."""
    frames = []
    lamp_colors = {
        "red": (232, 72, 64),
        "yellow": (238, 206, 84),
        "green": (96, 214, 96),
    }
    posts = [(1, 22), (15, 12), (29, 22)]  # L, T, R (координаты спрайта)
    for phase in range(4):
        a = np.zeros((32, 32, 4), dtype=np.uint8)
        for idx, (px, py) in enumerate(posts):
            if idx == 1:
                lit = ("red", "red", "green", "yellow")[phase]
            else:
                lit = ("green", "yellow", "red", "red")[phase]
            for y in range(py, min(32, py + 10)):
                for dx in (0, 1):
                    if 0 <= px + dx < 32:
                        a[y, px + dx] = (*MAT["post"], 255)
            for y in range(max(0, py - 9), py):
                for dx in (-1, 0, 1):
                    if 0 <= px + dx < 32:
                        a[y, px + dx] = (*MAT["post"], 255)
            for name, ly in (("red", py - 8), ("yellow", py - 5), ("green", py - 2)):
                col = lamp_colors[name]
                if name != lit:
                    col = tuple(int(c * 0.25) for c in col)
                if 0 <= ly < 32 and 0 <= px < 32:
                    a[ly, px] = (*col, 255)
        frames.append(a)
    return frames



def build_one_way_frames(style: dict, seed: int = 0):
    """4 кадра-оверлея для односторонних дорог (стрелки по направлению).

    Порядок кадров как в игре: SOUTH_EAST, NORTH_EAST, NORTH_WEST, SOUTH_WEST,
    то есть +i (экран вниз-вправо), -j (вверх-вправо), -i (вверх-влево),
    +j (вниз-влево).
    """
    import numpy as np

    # направление в осях (s, t) -> экранный вектор
    dirs = [(1, 0), (0, -1), (-1, 0), (0, 1)]
    out = []
    for ds, dt in dirs:
        canvas = art.new_canvas(iso.TILE_W, iso.TILE_H)
        vx = 16.0 * ds - 16.0 * dt
        vy = 8.0 * ds + 8.0 * dt
        norm = (vx * vx + vy * vy) ** 0.5
        vx, vy = vx / norm, vy / norm
        cx, cy = 16.0, 8.0
        color = MAT["white"]

        def px(x, y, c=color):
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < iso.TILE_W and 0 <= yi < iso.TILE_H:
                canvas[yi, xi] = (*c, 255)

        for t in np.arange(-4.0, 4.0, 0.25):
            px(cx + vx * t, cy + vy * t)
        # наконечник
        for side in (-1, 1):
            wx, wy = -vy * side, vx * side
            for t in np.arange(0.0, 4.0, 0.25):
                px(cx + vx * 4 - vx * t + wx * t * 0.6,
                   cy + vy * 4 - vy * t + wy * t * 0.6)
        out.append(canvas)
    return out


# ---------------------------------------------------------------------------
# превью для списка плагинов
# ---------------------------------------------------------------------------
def preview_frame(tile: np.ndarray, scale: int = 2):
    """Увеличенный кадр дороги для предпросмотра."""
    return art.to_image(np.kron(tile, np.ones((scale, scale, 1), dtype=np.uint8)))
