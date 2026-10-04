"""Генерация первого российского жилого сектора для TheoTown.

Спрайты рисуются здесь как небольшой пиксель-арт на изометрической сетке
32x16. В пак не попадают заимствованные игровые картинки.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

TILE_W = 32
TILE_H = 16
AUTHOR = "sashatyukavin3-star"
PACK_DIRNAME = "TheoRussianHomesStarter"
PACK_VERSION = "1.0.0"

MANIFEST = {
    "id": "a3e8f997-de47-4b55-b7a9-5297ce567b55",
    "version": 1,
    "title": "Russian Homes: Starter Sector[ru]Жилые дома РФ: начальный сектор",
    "text": (
        "Three level-one homes inspired by Russian village and Soviet residential "
        "architecture.[ru]Три жилых здания первого уровня по мотивам российской "
        "деревни и советской жилой застройки."
    ),
    "author": AUTHOR,
    "thumbnail": "thumbnail.png",
    "multiplayer": True,
}

STARTER_BUILDINGS = [
    {
        "id": "$theorussia_res_starter_timber00",
        "title": "Village Timber Cottage[ru]Деревянный дом в селе",
        "text": "A small timber home with a blue metal roof."
        "[ru]Небольшой деревянный дом с синей металлической крышей.",
        "width": 1,
        "height": 1,
        "sprite": "res_ru_timber_cottage.png",
        "renderer": "timber",
    },
    {
        "id": "$theorussia_res_starter_brick00",
        "title": "Brick Dacha[ru]Кирпичная дача",
        "text": "A modest brick dacha with a red gabled roof."
        "[ru]Небольшая кирпичная дача с красной двускатной крышей.",
        "width": 1,
        "height": 1,
        "sprite": "res_ru_brick_dacha.png",
        "renderer": "brick",
    },
    {
        "id": "$theorussia_res_starter_panel05",
        "title": "Five-storey Panel Block[ru]Пятиэтажный панельный дом",
        "text": "A compact five-storey Soviet-era panel apartment block."
        "[ru]Компактный пятиэтажный панельный жилой дом советской эпохи.",
        "width": 2,
        "height": 2,
        "sprite": "res_ru_panel_five_storey.png",
        "renderer": "panel",
    },
]

# Палитра намеренно приглушённая, чтобы маленькие спрайты не выбивались
# из пиксельной графики TheoTown.
C = {
    "outline": (51, 48, 43, 255),
    "grass": (104, 137, 72, 255),
    "grass_light": (117, 148, 78, 255),
    "grass_dark": (83, 117, 61, 255),
    "path": (163, 147, 119, 255),
    "path_dark": (125, 112, 91, 255),
    "stone": (138, 136, 127, 255),
    "stone_dark": (105, 105, 100, 255),
    "wood_front": (174, 132, 83, 255),
    "wood_side": (142, 103, 68, 255),
    "wood_light": (205, 164, 108, 255),
    "wood_dark": (107, 77, 54, 255),
    "brick_front": (179, 119, 91, 255),
    "brick_side": (145, 91, 72, 255),
    "brick_light": (204, 145, 109, 255),
    "mortar": (214, 177, 143, 255),
    "roof_blue_far": (47, 80, 99, 255),
    "roof_blue_near": (66, 112, 132, 255),
    "roof_red_far": (109, 57, 47, 255),
    "roof_red_near": (151, 76, 57, 255),
    "roof_edge": (42, 55, 62, 255),
    "panel_front": (190, 194, 184, 255),
    "panel_side": (151, 158, 154, 255),
    "panel_light": (211, 213, 202, 255),
    "panel_dark": (117, 126, 124, 255),
    "roof_concrete": (109, 116, 115, 255),
    "roof_concrete_light": (142, 147, 143, 255),
    "window_frame": (226, 211, 172, 255),
    "window_frame_dark": (110, 105, 91, 255),
    "glass": (72, 105, 119, 255),
    "glass_light": (123, 157, 166, 255),
    "door": (95, 66, 49, 255),
    "door_light": (142, 102, 69, 255),
}


def _point(s: float, t: float, z: float, size: int, base_y: int) -> tuple[int, int]:
    """Преобразовать координату на квадратной iso-основе в пиксели."""
    x = TILE_W * size / 2 + TILE_W * (s - t) / 2
    y = base_y + TILE_H * (s + t) / 2 - z
    return round(x), round(y)


def _ground_points(size: int, base_y: int) -> list[tuple[int, int]]:
    return [
        _point(0, 0, 0, size, base_y),
        _point(size, 0, 0, size, base_y),
        _point(size, size, 0, size, base_y),
        _point(0, size, 0, size, base_y),
    ]


def _draw_ground(draw: ImageDraw.ImageDraw, size: int, base_y: int, path_to=None) -> None:
    """Изометрическая лужайка/площадка основания; фон вне ромба прозрачен."""
    diamond = _ground_points(size, base_y)
    draw.polygon(diamond, fill=C["grass"])
    # Два тихих цветовых пятна дают ощущение травы, но остаются крупными пикселями.
    top, right, bottom, left = diamond
    draw.polygon([top, right, bottom], fill=C["grass_light"])
    draw.polygon([top, bottom, left], fill=C["grass"])
    draw.line(diamond + [diamond[0]], fill=C["grass_dark"], width=1)
    if path_to is not None:
        start, end = path_to
        draw.line(
            [_point(start[0], start[1], 0, size, base_y),
             _point(end[0], end[1], 0, size, base_y)],
            fill=C["path_dark"], width=3,
        )
        draw.line(
            [_point(start[0], start[1], 0, size, base_y),
             _point(end[0], end[1], 0, size, base_y)],
            fill=C["path"], width=2,
        )


def _box_points(bounds, z: float, size: int, base_y: int):
    s0, s1, t0, t1 = bounds
    return [
        _point(s0, t0, z, size, base_y),
        _point(s1, t0, z, size, base_y),
        _point(s1, t1, z, size, base_y),
        _point(s0, t1, z, size, base_y),
    ]


def _draw_box(
    draw: ImageDraw.ImageDraw,
    size: int,
    base_y: int,
    bounds: tuple[float, float, float, float],
    z0: float,
    z1: float,
    front_color,
    side_color,
    outline=C["outline"],
) -> None:
    """Нарисовать две видимые грани изометрического прямоугольного объёма."""
    s0, s1, t0, t1 = bounds
    front = [
        _point(s0, t1, z0, size, base_y),
        _point(s1, t1, z0, size, base_y),
        _point(s1, t1, z1, size, base_y),
        _point(s0, t1, z1, size, base_y),
    ]
    side = [
        _point(s1, t0, z0, size, base_y),
        _point(s1, t1, z0, size, base_y),
        _point(s1, t1, z1, size, base_y),
        _point(s1, t0, z1, size, base_y),
    ]
    draw.polygon(front, fill=front_color)
    draw.polygon(side, fill=side_color)
    draw.line(front + [front[0]], fill=outline, width=1)
    draw.line(side + [side[0]], fill=outline, width=1)


def _face_quad(face: str, fixed: float, center: float, half: float,
               z0: float, z1: float, size: int, base_y: int):
    if face == "front":  # t = fixed, горизонталь фасада идёт по s
        coords = [
            (center - half, fixed, z0), (center + half, fixed, z0),
            (center + half, fixed, z1), (center - half, fixed, z1),
        ]
    else:  # s = fixed, фасад уходит по оси t
        coords = [
            (fixed, center - half, z0), (fixed, center + half, z0),
            (fixed, center + half, z1), (fixed, center - half, z1),
        ]
    return [_point(s, t, z, size, base_y) for s, t, z in coords]


def _draw_window(draw, face, fixed, center, half, z0, z1, size, base_y,
                 frame=C["window_frame"], glass=C["glass"]):
    outer = _face_quad(face, fixed, center, half, z0, z1, size, base_y)
    draw.polygon(outer, fill=C["window_frame_dark"])
    inner_half = max(0.015, half - 0.025)
    inner = _face_quad(face, fixed, center, inner_half, z0 + 0.7, z1 - 0.6, size, base_y)
    draw.polygon(inner, fill=frame)
    # Стекло и одна светлая полоска читаются даже на мелких кадрах 1x1.
    glass_inner = _face_quad(face, fixed, center, max(0.01, inner_half - 0.025),
                             z0 + 1.0, z1 - 1.0, size, base_y)
    draw.polygon(glass_inner, fill=glass)
    if glass_inner:
        a, b = glass_inner[3], glass_inner[2]
        draw.line([a, b], fill=C["glass_light"], width=1)


def _draw_door(draw, face, fixed, center, half, height, size, base_y):
    outer = _face_quad(face, fixed, center, half, 0, height, size, base_y)
    draw.polygon(outer, fill=C["outline"])
    inner = _face_quad(face, fixed, center, max(0.01, half - 0.025),
                       0.7, height - 0.5, size, base_y)
    draw.polygon(inner, fill=C["door"])
    # Ручка: один пиксель на теневой стороне двери.
    if inner:
        x, y = inner[1]
        draw.point((x - 1, y - 2), fill=C["door_light"])


def _face_line(draw, face, fixed, start, end, z, size, base_y, color, width=1):
    if face == "front":
        points = [_point(start, fixed, z, size, base_y),
                  _point(end, fixed, z, size, base_y)]
    else:
        points = [_point(fixed, start, z, size, base_y),
                  _point(fixed, end, z, size, base_y)]
    draw.line(points, fill=color, width=width)


def _draw_cottage(spec: dict) -> Image.Image:
    size = 1
    wall_h = 11 if spec["renderer"] == "timber" else 12
    roof_h = 6
    extra = wall_h + roof_h + 10
    base_y = extra
    image = Image.new("RGBA", (TILE_W * size, TILE_H * size + extra), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    _draw_ground(draw, size, base_y)

    s0, s1, t0, t1 = 0.23, 0.77, 0.24, 0.76
    bounds = (s0, s1, t0, t1)
    floor = _box_points(bounds, 0, size, base_y)
    draw.polygon(floor, fill=C["stone_dark"])
    draw.polygon(_box_points((s0 + 0.03, s1 - 0.03, t0 + 0.03, t1 - 0.03), 0,
                             size, base_y), fill=C["stone"])

    is_timber = spec["renderer"] == "timber"
    front_color = C["wood_front"] if is_timber else C["brick_front"]
    side_color = C["wood_side"] if is_timber else C["brick_side"]
    trim = C["wood_light"] if is_timber else C["brick_light"]
    _draw_box(draw, size, base_y, bounds, 0, wall_h, front_color, side_color)

    # Торец с фронтоном. Он частично виден над теневой боковой стеной.
    mid_t = (t0 + t1) / 2
    gable = [
        _point(s1, t0, wall_h, size, base_y),
        _point(s1, mid_t, wall_h + roof_h, size, base_y),
        _point(s1, t1, wall_h, size, base_y),
    ]
    draw.polygon(gable, fill=side_color, outline=C["outline"])

    # Горизонтальные доски/ряды кирпича на двух видимых фасадах.
    if is_timber:
        for z in (2.5, 5.0, 7.5, 10.0):
            _face_line(draw, "front", t1, s0 + 0.02, s1 - 0.02, z,
                       size, base_y, C["wood_dark"])
            _face_line(draw, "side", s1, t0 + 0.02, t1 - 0.02, z,
                       size, base_y, C["wood_dark"])
    else:
        for z in (3.0, 6.0, 9.0):
            _face_line(draw, "front", t1, s0 + 0.02, s1 - 0.02, z,
                       size, base_y, C["mortar"])
            _face_line(draw, "side", s1, t0 + 0.02, t1 - 0.02, z,
                       size, base_y, C["mortar"])
        # Несколько коротких вертикальных швов не превращают кладку в шум.
        _face_line(draw, "front", t1, s0 + 0.18, s0 + 0.18, 0,
                   size, base_y, C["mortar"])

    # Окна и вход.
    _draw_window(draw, "front", t1, s0 + (s1 - s0) * 0.27, 0.065,
                 4.0, 8.5, size, base_y, frame=trim)
    _draw_window(draw, "side", s1, t0 + (t1 - t0) * 0.37, 0.065,
                 4.0, 8.5, size, base_y, frame=trim)
    _draw_door(draw, "front", t1, s0 + (s1 - s0) * 0.76, 0.075,
               7.0, size, base_y)

    # Дорожка от входа к краю участка.
    door_s = s0 + (s1 - s0) * 0.76
    draw.line([_point(door_s, t1 + 0.03, 0, size, base_y),
               _point(door_s, 0.97, 0, size, base_y)],
              fill=C["path_dark"], width=2)
    draw.line([_point(door_s, t1 + 0.03, 0, size, base_y),
               _point(door_s, 0.97, 0, size, base_y)],
              fill=C["path"], width=1)

    # Двускатная металлическая/шиферная крыша с небольшим свесом.
    roof = (s0 - 0.07, s1 + 0.07, t0 - 0.06, t1 + 0.06)
    rs0, rs1, rt0, rt1 = roof
    ridge_t = (rt0 + rt1) / 2
    far_slope = [
        _point(rs0, rt0, wall_h, size, base_y),
        _point(rs1, rt0, wall_h, size, base_y),
        _point(rs1, ridge_t, wall_h + roof_h, size, base_y),
        _point(rs0, ridge_t, wall_h + roof_h, size, base_y),
    ]
    near_slope = [
        _point(rs0, ridge_t, wall_h + roof_h, size, base_y),
        _point(rs1, ridge_t, wall_h + roof_h, size, base_y),
        _point(rs1, rt1, wall_h, size, base_y),
        _point(rs0, rt1, wall_h, size, base_y),
    ]
    far_color = C["roof_blue_far"] if is_timber else C["roof_red_far"]
    near_color = C["roof_blue_near"] if is_timber else C["roof_red_near"]
    draw.polygon(far_slope, fill=far_color, outline=C["roof_edge"])
    draw.polygon(near_slope, fill=near_color, outline=C["roof_edge"])
    draw.line([_point(rs0, ridge_t, wall_h + roof_h, size, base_y),
               _point(rs1, ridge_t, wall_h + roof_h, size, base_y)],
              fill=C["roof_edge"], width=1)
    for fraction in (0.34, 0.68):
        t = ridge_t + (rt1 - ridge_t) * fraction
        z = wall_h + roof_h * (1 - fraction)
        draw.line([_point(rs0, t, z, size, base_y),
                   _point(rs1, t, z, size, base_y)],
                  fill=C["roof_edge"], width=1)
    return image


def _draw_panel_block(spec: dict) -> Image.Image:
    size = 2
    floors = 5
    floor_h = 5.4
    wall_h = floors * floor_h
    roof_z = wall_h + 3
    extra = int(roof_z + 12)
    base_y = extra
    image = Image.new("RGBA", (TILE_W * size, TILE_H * size + extra), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    _draw_ground(draw, size, base_y)

    s0, s1, t0, t1 = 0.08, 1.92, 0.08, 1.92
    bounds = (s0, s1, t0, t1)
    draw.polygon(_box_points(bounds, 0, size, base_y), fill=C["stone"])
    _draw_box(draw, size, base_y, bounds, 0, wall_h,
              C["panel_front"], C["panel_side"])

    # Стеновые швы и межэтажные пояса.
    for floor in range(1, floors):
        z = floor * floor_h
        _face_line(draw, "front", t1, s0, s1, z, size, base_y, C["panel_dark"])
        _face_line(draw, "side", s1, t0, t1, z, size, base_y, C["panel_dark"])
    for index in (1, 3, 5):
        u = s0 + (s1 - s0) * index / 6
        _face_line(draw, "front", t1, u, u, 0, size, base_y, C["panel_light"])
        u = t0 + (t1 - t0) * index / 6
        _face_line(draw, "side", s1, u, u, 0, size, base_y, C["panel_dark"])

    # Одинаковая ритмика окон на каждом этаже, без чрезмерно ярких акцентов.
    columns = 6
    front_centres = [s0 + (s1 - s0) * (i + 0.5) / columns for i in range(columns)]
    side_centres = [t0 + (t1 - t0) * (i + 0.5) / columns for i in range(columns)]
    for floor in range(floors):
        z0 = floor * floor_h + 1.1
        z1 = floor * floor_h + 4.0
        for center in front_centres:
            _draw_window(draw, "front", t1, center, 0.055,
                         z0, z1, size, base_y,
                         frame=C["panel_light"], glass=C["glass"])
        for center in side_centres:
            _draw_window(draw, "side", s1, center, 0.055,
                         z0, z1, size, base_y,
                         frame=C["panel_light"], glass=C["glass"])

    # Подъезд и короткая бетонная дорожка на ближней стороне участка.
    entry_s = s0 + 0.20
    _draw_door(draw, "front", t1, entry_s, 0.075, 4.8,
               size, base_y)
    draw.line([_point(entry_s, t1 + 0.02, 0, size, base_y),
               _point(entry_s, 1.99, 0, size, base_y)],
              fill=C["stone_dark"], width=2)
    draw.line([_point(entry_s, t1 + 0.02, 0, size, base_y),
               _point(entry_s, 1.99, 0, size, base_y)],
              fill=C["stone"], width=1)

    # Плоская крыша с парапетом и небольшим техблоком.
    roof = _box_points(bounds, roof_z, size, base_y)
    draw.polygon(roof, fill=C["roof_concrete"])
    draw.line(roof + [roof[0]], fill=C["outline"], width=1)
    # Светлая кромка на передних рёбрах крыши.
    draw.line([_point(s0, t1, roof_z, size, base_y),
               _point(s1, t1, roof_z, size, base_y),
               _point(s1, t1, wall_h, size, base_y)],
              fill=C["roof_concrete_light"], width=1)
    draw.line([_point(s1, t0, roof_z, size, base_y),
               _point(s1, t1, roof_z, size, base_y)],
              fill=C["roof_concrete_light"], width=1)
    _draw_box(draw, size, base_y,
              (0.65, 1.00, 0.55, 0.92), roof_z, roof_z + 3,
              C["stone"], C["stone_dark"], outline=C["outline"])
    roof_top = _box_points((0.65, 1.00, 0.55, 0.92), roof_z + 3, size, base_y)
    draw.polygon(roof_top, fill=C["panel_light"], outline=C["outline"])
    return image


def render_building(spec: dict) -> Image.Image:
    """Вернуть RGBA-спрайт одного здания."""
    if spec["renderer"] in ("timber", "brick"):
        return _draw_cottage(spec)
    if spec["renderer"] == "panel":
        return _draw_panel_block(spec)
    raise ValueError(f"Неизвестный тип рендера: {spec['renderer']}")


def write_json(path: str | os.PathLike, value) -> None:
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)
        stream.write("\n")


def make_drafts(pack_dir: str | os.PathLike) -> list[dict]:
    drafts = []
    for spec in STARTER_BUILDINGS:
        sprite = render_building(spec)
        sprite.save(os.path.join(pack_dir, spec["sprite"]))
        drafts.append({
            "id": spec["id"],
            "type": "residential",
            "author": AUTHOR,
            "title": spec["title"],
            "text": spec["text"],
            "width": spec["width"],
            "height": spec["height"],
            "level": 1,
            "frames": [{"bmp": spec["sprite"]}],
        })
    return drafts


def _font(size: int):
    candidates = (
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/arial.ttf",
    )
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_preview(pack_dir: str | os.PathLike, output_path: str | os.PathLike) -> Image.Image:
    """Каталожный превью-кадр (x4/x3 nearest-neighbour), без сглаживания."""
    canvas = Image.new("RGBA", (768, 320), (82, 116, 62, 255))
    draw = ImageDraw.Draw(canvas)
    # Тихая диагональная фактура фона.
    for y in range(42, canvas.height, 24):
        draw.line([(0, y), (canvas.width, y - 70)], fill=(91, 125, 68, 255), width=1)
    draw.text((22, 12), "RUSSIAN HOMES  /  STARTER SECTOR",
              font=_font(16), fill=(244, 238, 218, 255))

    slots = [
        ("res_ru_timber_cottage.png", 4, 132, "Деревянный дом", "Timber cottage"),
        ("res_ru_brick_dacha.png", 4, 384, "Кирпичная дача", "Brick dacha"),
        ("res_ru_panel_five_storey.png", 3, 636, "Пятиэтажка", "Panel block"),
    ]
    baseline = 267
    for name, scale, center_x, label, fallback in slots:
        sprite = Image.open(os.path.join(pack_dir, name)).convert("RGBA")
        sprite = sprite.resize((sprite.width * scale, sprite.height * scale), Image.Resampling.NEAREST)
        x = center_x - sprite.width // 2
        y = baseline - sprite.height
        canvas.alpha_composite(sprite, (x, y))
        font = _font(13)
        try:
            box = draw.textbbox((0, 0), label, font=font)
        except UnicodeEncodeError:
            label = fallback
            box = draw.textbbox((0, 0), label, font=font)
        text_width = box[2] - box[0]
        draw.text((center_x - text_width // 2, 286), label,
                  font=font, fill=(244, 238, 218, 255))
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    canvas.convert("RGB").save(output_path)
    return canvas


def build_thumbnail(pack_dir: str | os.PathLike) -> None:
    """Небольшое превью манифеста без текста, 128x64."""
    thumb = Image.new("RGBA", (128, 64), (92, 126, 66, 255))
    placements = [
        ("res_ru_timber_cottage.png", (3, 20), (28, 36)),
        ("res_ru_brick_dacha.png", (37, 20), (28, 36)),
        ("res_ru_panel_five_storey.png", (75, 7), (48, 55)),
    ]
    for name, xy, max_size in placements:
        sprite = Image.open(os.path.join(pack_dir, name)).convert("RGBA")
        scale = min(max_size[0] / sprite.width, max_size[1] / sprite.height)
        size = (max(1, round(sprite.width * scale)), max(1, round(sprite.height * scale)))
        sprite = sprite.resize(size, Image.Resampling.NEAREST)
        thumb.alpha_composite(sprite, xy)
    thumb.save(os.path.join(pack_dir, "thumbnail.png"))


def validate_pack(pack_dir: str | os.PathLike) -> list[str]:
    """Проверить manifest, residential drafts, id и связанные спрайты."""
    errors = []
    manifest_path = os.path.join(pack_dir, "plugin.manifest")
    if not os.path.exists(manifest_path):
        errors.append("нет plugin.manifest")
    else:
        try:
            with open(manifest_path, encoding="utf-8") as stream:
                manifest = json.load(stream)
            for key in ("id", "version", "title", "author"):
                if key not in manifest:
                    errors.append(f"в манифесте отсутствует {key}")
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"некорректный plugin.manifest: {exc}")

    json_files = sorted(name for name in os.listdir(pack_dir) if name.endswith(".json"))
    ids = set()
    total = 0
    for filename in json_files:
        path = os.path.join(pack_dir, filename)
        try:
            with open(path, encoding="utf-8") as stream:
                drafts = json.load(stream)
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{filename}: некорректный JSON: {exc}")
            continue
        if not isinstance(drafts, list):
            errors.append(f"{filename}: ожидается JSON-массив зданий")
            continue
        for draft in drafts:
            total += 1
            building_id = draft.get("id")
            if not building_id:
                errors.append(f"{filename}: здание без id")
            elif building_id in ids:
                errors.append(f"повтор id {building_id}")
            else:
                ids.add(building_id)
            if draft.get("type") != "residential":
                errors.append(f"{building_id}: type должен быть residential")
            if draft.get("level") != 1:
                errors.append(f"{building_id}: стартовый сектор должен иметь level 1")
            width, height = draft.get("width"), draft.get("height")
            frames = draft.get("frames")
            if not isinstance(frames, list) or not frames:
                errors.append(f"{building_id}: отсутствуют frames")
                continue
            for frame in frames:
                sprite_name = frame.get("bmp")
                sprite_path = os.path.join(pack_dir, sprite_name or "")
                if not sprite_name or not os.path.isfile(sprite_path):
                    errors.append(f"{building_id}: не найден PNG {sprite_name}")
                    continue
                try:
                    with Image.open(sprite_path) as sprite:
                        sprite.load()
                        if sprite.mode != "RGBA":
                            errors.append(f"{sprite_name}: нужен RGBA с прозрачностью")
                        if width and sprite.width != TILE_W * width:
                            errors.append(
                                f"{sprite_name}: ширина {sprite.width}px, ожидалось {TILE_W * width}px"
                            )
                        if height and sprite.height < TILE_H * height:
                            errors.append(f"{sprite_name}: высота меньше footprint {height}x{TILE_H}px")
                        if sprite.getchannel("A").getbbox() is None:
                            errors.append(f"{sprite_name}: пустой PNG")
                except OSError as exc:
                    errors.append(f"{sprite_name}: не удалось прочитать PNG: {exc}")
    if total != len(STARTER_BUILDINGS):
        errors.append(f"ожидалось {len(STARTER_BUILDINGS)} зданий, найдено {total}")
    return errors


def build_starter_sector(pack_dir: str | os.PathLike) -> list[dict]:
    """Создать локальную папку плагина с графикой, JSON и манифестом."""
    os.makedirs(pack_dir, exist_ok=True)
    drafts = make_drafts(pack_dir)
    write_json(os.path.join(pack_dir, "10_residential_starter_sector.json"), drafts)
    write_json(os.path.join(pack_dir, "plugin.manifest"), MANIFEST)
    build_thumbnail(pack_dir)
    return drafts
