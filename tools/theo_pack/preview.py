"""Демонстрационные картинки пака: изометрические сцены и листы кадров."""

from __future__ import annotations

import os

from PIL import Image, ImageDraw

from . import art, decos, iso, roads
from .decos import LAMP_ANCHOR

GRASS = (104, 138, 74, 255)
GRASS2 = (96, 130, 68, 255)
BG = (92, 134, 70, 255)


# ---------------------------------------------------------------------------
# мини-рендер изометрической сцены
# ---------------------------------------------------------------------------
def _pos(i: int, j: int):
    return 16 * (i - j), 8 * (i + j)


def render_scene(cells, deco_cells=None, scale=3, bg=GRASS, lights_step=4):
    """Собрать сцену.

    cells      -- {(i, j): ключ стиля дороги}
    deco_cells -- {(i, j): (имя украшения, поворот)}
    """
    deco_cells = deco_cells or {}
    frames = {}
    for key in set(cells.values()):
        st = roads.ROAD_STYLES[key]
        frames[key] = [art.to_image(f) for f in roads.build_road_frames(st)]

    dirs = {"SE": (1, 0), "SW": (0, 1), "NW": (-1, 0), "NE": (0, -1)}
    coords = list(cells) + list(deco_cells)
    xs = [_pos(i, j) for i, j in coords]
    minx = min(p[0] for p in xs) - 64
    miny = min(p[1] for p in xs) - 48
    maxx = max(p[0] for p in xs) + 64
    maxy = max(p[1] for p in xs) + 48
    img = Image.new("RGBA", (maxx - minx, maxy - miny), bg)

    # порядок рисования: сверху вниз по (i+j), затем по (i-j)
    for i, j in sorted(cells, key=lambda c: (c[0] + c[1], c[0] - c[1])):
        mask = sum(iso.BIT[d] for d, (di, dj) in dirs.items() if (i + di, j + dj) in cells)
        x, y = _pos(i, j)
        sprite = frames[cells[(i, j)]][mask]
        # у высоких спрайтов (отбойники) плитка лежит в нижней половине
        img.alpha_composite(sprite, (x - minx, y - miny - (sprite.height - 16)))

    # украшения рисуем после дорог
    for (i, j), (name, rot) in sorted(deco_cells.items(), key=lambda c: (c[0][0] + c[0][1], c[0][0] - c[0][1])):
        mask = sum(iso.BIT[d] for d, (di, dj) in dirs.items() if (i + di, j + dj) in cells)
        frames_list, anchor_y, index_map = _deco_sprites(name)
        idx_list = index_map.get(mask) or []
        if not idx_list:
            continue
        frame = frames_list[idx_list[0]]
        x, y = _pos(i, j)
        img.alpha_composite(frame, (x - minx, y - miny - anchor_y))

    # фонари вдоль длинных прямых участков
    if lights_step:
        for i, j in sorted(cells, key=lambda c: (c[0] + c[1], c[0] - c[1])):
            mask = sum(iso.BIT[d] for d, (di, dj) in dirs.items() if (i + di, j + dj) in cells)
            key = cells[(i, j)]
            if mask not in (5, 10) or key in ("motorway",):
                continue
            if (i + j) % lights_step:
                continue
            frames_list, anchor_y, index_map = _deco_sprites("streetlight")
            idx_list = index_map.get(mask) or []
            if not idx_list:
                continue
            lamp = frames_list[idx_list[0]]
            x, y = _pos(i, j)
            img.alpha_composite(lamp, (x - minx, y - miny - LAMP_ANCHOR))

    img = img.resize((img.width * scale, img.height * scale), Image.NEAREST)
    return img.convert("RGB")


_DECO_CACHE = {}


def _deco_sprites(name: str):
    """Спрайты украшений: (картинка, handle y, карта индекс-массивов)."""
    if name in _DECO_CACHE:
        return _DECO_CACHE[name]
    style = roads.ROAD_STYLES["street"]
    specs = {s["key"]: s for s in decos.decorations_for(style, "p", seed=77)}
    spec = specs[name]
    frame_imgs = [art.to_image(f) for f in spec["frames"]]
    index_map = {m: list(spec["indices"][m]) for m in range(16)}
    result = (frame_imgs, spec.get("anchor", 0), index_map)
    _DECO_CACHE[name] = result
    return result


# ---------------------------------------------------------------------------
# сцены пака
# ---------------------------------------------------------------------------
def town_layout():
    """Небольшой город: кольцо + кварталы, разные типы дорог и разметка."""
    cells = {}
    N = 9
    # внешнее кольцо -- проспект
    for i in range(N + 1):
        for j in (0, N):
            cells[(i, j)] = "avenue"
    for j in range(N + 1):
        for i in (0, N):
            cells[(i, j)] = "avenue"
    # внутренние улицы (соединяются с кольцом)
    for i in range(1, N):
        for j in (3, 6):
            cells[(i, j)] = "street"
    for j in range(1, N):
        for i in (3, 6):
            cells[(i, j)] = "street"
    # пара двухполосных улиц и магистраль сбоку
    for i in range(N + 2, N + 7):
        cells[(i, 3)] = "street1"
    for j in range(4, 8):
        for i in (N + 4,):
            cells[(i, j)] = "express"
    # загородная дорога и гравийка на окраине
    for i in range(1, 5):
        cells[(i, N + 2)] = "rural"
    for i in range(5, 8):
        cells[(i, N + 2)] = "gravel"

    decos_map = {
        (4, 3): ("crosswalk", 0),      # улица вдоль оси s
        (6, 3): ("speedbump", 0),
        (3, 2): ("stopline", 0),       # улица вдоль оси t
        (2, 6): ("crosswalk", 0),
    }
    return cells, decos_map


def build_all(pack_dir: str, dist_dir: str):
    os.makedirs(dist_dir, exist_ok=True)
    out = []

    # 1. город
    cells, decos_map = town_layout()
    scene = render_scene(cells, decos_map, scale=4)
    p = os.path.join(dist_dir, "preview_town.png")
    scene.save(p)
    out.append(p)

    # 2. витрина типов дорог
    out.append(_swatch(os.path.join(dist_dir, "preview_roads.png")))

    # 3. листы кадров
    out.append(_frames_grid(os.path.join(dist_dir, "preview_frames.png")))

    # 4. разметка крупным планом
    out.append(_markings(os.path.join(dist_dir, "preview_markings.png")))
    return out


def _swatch(path):
    from PIL import ImageDraw
    keys = list(roads.ROAD_STYLES)
    scale = 4
    w = 32 * scale + 12
    h = 48 * scale + 26
    img = Image.new("RGBA", (w * 4, h * 2), BG)
    d = ImageDraw.Draw(img)
    for n, key in enumerate(keys):
        st = roads.ROAD_STYLES[key]
        tile = art.to_image(roads.render_road_frame(10, st))
        tile = tile.resize((tile.width * scale, tile.height * scale), Image.NEAREST)
        x = (n % 4) * w + 6
        y = (n // 4) * h + 20
        img.alpha_composite(tile, (x, y))
        d.text((x, y - 14), key, fill=(255, 255, 255))
    img.convert("RGB").save(path)
    return path


def _frames_grid(path):
    keys = list(roads.ROAD_STYLES)
    cells = []
    for key in keys:
        st = roads.ROAD_STYLES[key]
        for f in roads.build_road_frames(st):
            cells.append(art.to_image(f).convert("RGB"))
    cw = 34
    ch = 34
    img = Image.new("RGB", (cw * 16, ch * len(keys)), BG)
    for r, key in enumerate(keys):
        frames = roads.build_road_frames(roads.ROAD_STYLES[key])
        for c, f in enumerate(frames):
            im = art.to_image(f).convert("RGB")
            img.paste(im, (c * cw + 1, r * ch + (ch - im.height)))
    img.save(path)
    return path


def _markings(path):
    """Сцена-крупный план: переход, стоп-линия, «лежачий полицейский», фонарь."""
    cells = {}
    for i in range(7):
        cells[(i, 0)] = "street"
    for j in range(1, 4):
        cells[(3, j)] = "street"
    decos_map = {
        (1, 0): ("crosswalk", 0),
        (2, 0): ("stopline", 0),
        (4, 0): ("speedbump", 0),
        (3, 2): ("crosswalk", 1),
    }
    scene = render_scene(cells, decos_map, scale=8, lights_step=2)
    scene.save(path)
    return path
