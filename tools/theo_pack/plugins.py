"""Сборка JSON-описаний и упаковка плагинов TheoTown.

Каталог результата повторяет структуру плагина TheoTown:

    dist/TheoRoadsPack/
        plugin.manifest          -- манифест плагина
        thumbnail.png            -- картинка для списка плагинов
        00_categories.json       -- категории в меню постройки
        05_decorations.json      -- дорожные украшения (общие для всех дорог)
        10_roads.json            -- типы дорог
        *.png                    -- графика (спрайты 32x16 и т.п.)

Плюс готовый архив dist/theo-roads-pack-vX.Y.Z.zip, который игрок просто
кладёт в папку плагинов TheoTown (или устанавливает через меню плагинов).
"""

from __future__ import annotations

import json
import os
import zipfile

from . import art, decos, roads

# ---------------------------------------------------------------------------
# Метаданные пака
# ---------------------------------------------------------------------------
PACK = {
    "manifest id": "9c1f4a52-7d38-4e9b-9a26-2f0b6d61c7a4",
    "version": 1,
    "title": "Theo Roads Pack[ru]Пак дорог Theo",
    "text": ("Adds 8 road types, road markings and street lights for every "
             "neighbourhood of your city.[ru]Добавляет 8 типов дорог, "
             "дорожную разметку и уличные фонари для любого района города."),
    "author": "sashatyukavin3-star",
    "id prefix": "theoroads",
}

CATEGORIES = [
    dict(id="$theoroads_cat00", parent="$cat_transport00", ordinal=4,
         title="Theo Roads[ru]Дороги Theo", icon="cat_root.png"),
    dict(id="$theoroads_cat_road00", parent="$theoroads_cat00", ordinal=1,
         title="Roads[ru]Дороги", icon="cat_roads.png"),
    dict(id="$theoroads_cat_deco00", parent="$theoroads_cat00", ordinal=2,
         title="Road markings[ru]Разметка и фонари", icon="cat_deco.png"),
]

#: типы дорог: ключ стиля -> параметры игрового баланса
ROAD_DEFS = [
    dict(key="gravel", id="$theoroads_gravel00", ordinal=1,
         title="Gravel road[ru]Гравийная дорога",
         text="Cheap road for the outskirts of your city.[ru]Дешёвая дорога для окраин города.",
         price=15, monthly=1, speed=1.2, level=0, rank=1,
         connectable=False, **{"draw ground": True}),
    dict(key="rural", id="$theoroads_rural00", ordinal=2,
         title="Country road[ru]Загородная дорога",
         text="Two lanes without a sidewalk, with a dashed centre line."
              "[ru]Две полосы без тротуара, с прерывистой осевой линией.",
         price=90, monthly=3, speed=2.0, level=1, rank=1,
         **{"draw ground": True}),
    dict(key="street", id="$theoroads_street00", ordinal=3,
         title="Town street[ru]Городская улица",
         text="A narrow street with a sidewalk.[ru]Узкая улица с тротуаром.",
         price=170, monthly=5, speed=2.3, level=1, rank=2),
    dict(key="street1", id="$theoroads_street100", ordinal=4,
         title="Two-lane street[ru]Двухполосная улица",
         text="Dashed lanes and edge lines.[ru]Прерывистые полосы и краевые линии.",
         price=240, monthly=7, speed=2.5, level=1, rank=3),
    dict(key="avenue", id="$theoroads_avenue00", ordinal=5,
         title="Avenue[ru]Проспект",
         text="Yellow centre line and white edge lines.[ru]Жёлтая осевая и белые краевые линии.",
         price=380, monthly=9, speed=3.0, level=2, rank=4),
    dict(key="avenue1", id="$theoroads_avenue100", ordinal=6,
         title="Divided avenue[ru]Проспект с разделительными полосами",
         text="Two lanes in each direction.[ru]По две полосы в каждую сторону.",
         price=520, monthly=12, speed=3.2, level=2, rank=5),
    dict(key="express", id="$theoroads_express00", ordinal=7,
         title="Expressway[ru]Скоростная магистраль",
         text="Four lanes with a median; buses and cars only."
              "[ru]Четыре полосы с разделителем; только легковые и автобусы.",
         price=900, monthly=20, speed=4.5, level=3, rank=7,
         **{"allow bus stop": False, "flag normal": False, "flag pkw": True,
            "flag lkw": False, "flag bus": True, "pedestrians": False,
            "deco step": 5}),
    dict(key="motorway", id="$theoroads_motorway00", ordinal=8,
         title="Motorway (one way)[ru]Автомагистраль (односторонняя)",
         text="One-way motorway with guard rails. Cars and trucks only."
              "[ru]Односторонняя магистраль с отбойниками. Только автомобили и грузовики.",
         price=1400, monthly=30, speed=5.5, level=3, rank=8, one_way=True,
         **{"allow bus stop": False, "allow crossing": False, "auto join": False,
            "flag normal": False, "flag pkw": True, "flag lkw": True,
            "flag bus": False, "pedestrians": False}),
]


# ---------------------------------------------------------------------------
# вспомогательное
# ---------------------------------------------------------------------------
def scale2(tile):
    """Увеличить пиксель-арт в 2 раза (для thumbnail)."""
    import numpy as np
    return np.kron(tile, np.ones((2, 2, 1), dtype=tile.dtype))


def write_json(path: str, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def _save_frames(out_dir: str, name: str, frames, heights=None):
    """Сохранить кадры как спрайт-лист PNG, вернуть имя файла."""
    from PIL import Image
    if heights:
        maxh = max(f.shape[0] for f in frames)
        width = frames[0].shape[1]
        sheet = Image.new("RGBA", (width * len(frames), maxh), (0, 0, 0, 0))
        for i, f in enumerate(frames):
            sheet.paste(art.to_image(f), (i * width, maxh - f.shape[0]))
    else:
        sheet = art.frames_to_sheet(frames)
    sheet.save(os.path.join(out_dir, name))
    return name


def _frame_json(cfg, count, w=None, h=None):
    cfg = dict(cfg)
    cfg["bmp"] = cfg.pop("bmp")
    if w:
        cfg["w"] = w
    if h:
        cfg["h"] = h
    cfg["count"] = count
    return cfg


# ---------------------------------------------------------------------------
# дороги
# ---------------------------------------------------------------------------
def build_roads(out_dir: str):
    drafts = []
    for d in ROAD_DEFS:
        style = roads.ROAD_STYLES[d["key"]]
        tall = bool(style.get("tall"))
        frames = roads.build_road_frames(style, seed=hash(d["key"]) % 1000)
        bmp = f"road_{d['key']}.png"
        _save_frames(out_dir, bmp, frames)
        w, h = art.TILE_W, frames[0].shape[0]
        n_frames = 16 if not d.get("one_way") else 64

        frame_list = [{"bmp": bmp, "w": w, "h": h, "count": len(frames)}]
        if d.get("one_way"):
            frame_list.append({"bmp": bmp, "w": w, "h": h, "count": len(frames), "copies": 3})

        draft = {
            "id": d["id"],
            "type": "road",
            "author": PACK["author"],
            "title": d["title"],
            "text": d["text"],
            "category": "$theoroads_cat_road00",
            "ordinal": d["ordinal"],
            "level": d["level"],
            "speed": d["speed"],
            "price": d["price"],
            "monthly price": d["monthly"],
            "bridge price": d["price"] * 12,
            "frames": frame_list,
            "requirement": {"requirements": [{"type": "RANK", "data": {"lvl": d["rank"]}}]},
        }
        if d.get("one_way"):
            draft["one way"] = True
            draft["overrunnable"] = True
            draft["one way frames"] = [{"bmp": "oneway_arrows.png", "w": 32, "h": 16, "count": 4}]
        if d.get("connectable") is not None:
            draft["connectable"] = d["connectable"]
        for k in ("draw ground", "allow bus stop", "allow crossing", "auto join",
                  "flag normal", "flag pkw", "flag lkw", "flag bus", "pedestrians"):
            if k in d:
                draft[k] = d[k]
        if d.get("deco step"):
            draft["deco"] = {"draft": "$theoroads_deco_light00", "step": d["deco step"]}
        # светофоры: у всех дорог, кроме магистрали (там развязки)
        if d["key"] not in ("motorway",):
            draft["traffic lights"] = [{"bmp": "traffic_lights.png", "w": 32, "h": 32, "count": 4}]
            draft["green phase"] = 4000 if d["level"] <= 1 else 6000
            draft["yellow phase"] = 600 if d["level"] <= 1 else 1000
        drafts.append(draft)
    return drafts


# ---------------------------------------------------------------------------
# украшения
# ---------------------------------------------------------------------------
def build_decorations(out_dir: str, style_key: str = "street"):
    """Общий набор украшений (разметка + фонарь) для всех дорог пака."""
    style = roads.ROAD_STYLES[style_key]
    drafts = []
    specs = decos.decorations_for(style, PACK["id prefix"], seed=77)
    for spec in specs:
        key = spec["key"]
        bmp = f"deco_{key}.png"
        heights = spec.get("height")
        _save_frames(out_dir, bmp, spec["frames"])
        n = len(spec["frames"])
        anim_ids = [f"$theoroads_anim_{key}{i:02d}" for i in range(n)]
        handle = {"handle y": spec.get("anchor", 8)}
        for i, aid in enumerate(anim_ids):
            frame = {"bmp": bmp, "x": i * art.TILE_W, "w": art.TILE_W, "h": heights or 16}
            frame.update(handle)
            drafts.append({
                "id": aid, "type": "animation",
                "title": f"anim {key} {i}",
                "frames": [frame],
            })

        fg = key == "streetlight"
        index_array = spec["indices"]
        deco = {
            "id": f"$theoroads_deco_{key}00",
            "type": "road decoration",
            "author": PACK["author"],
            "category": "$theoroads_cat_deco00",
            "ordinal": ["crosswalk", "stopline", "speedbump", "streetlight"].index(key) + 1,
            "animation": [{"id": anim_ids[0]}, {"id": anim_ids[1]}],
            "frame animation indices": index_array,
            **spec["draft"],
        }
        if fg:
            deco.pop("animation")
            deco.pop("frame animation indices")
            deco["animation fg"] = [{"id": anim_ids[0]}, {"id": anim_ids[1]}]
            deco["frame animation fg indices"] = index_array
        drafts.append(deco)
    return drafts


def build_categories(out_dir: str):
    """Категории. Иконки рисуем сами (32x32, стрелка/разметка)."""
    import numpy as np
    drafts = []
    for cat in CATEGORIES:
        drafts.append({
            "id": cat["id"],
            "type": "category",
            "title": cat["title"],
            "ordinal": cat["ordinal"],
            "category": cat["parent"],
            "frames": [{"bmp": cat["icon"]}],
        })
        if not os.path.exists(os.path.join(out_dir, cat["icon"])):
            icon = _category_icon(cat["id"])
            art.to_image(icon).save(os.path.join(out_dir, cat["icon"]))
    return drafts


def _category_icon(kind: str):
    """Простые иконки категорий 32x32."""
    import numpy as np
    c = art.new_canvas(32, 32)
    asphalt, white, yellow = art.MATERIALS["asphalt"], art.MATERIALS["white"], art.MATERIALS["yellow"]
    if "road" in kind:
        for y in range(4, 28):
            for x in range(6, 26):
                c[y, x] = (*asphalt, 255)
        for y in range(6, 26, 4):
            for x in range(15, 17):
                c[y:y + 2, x] = (*white, 255)
    elif "deco" in kind:
        for y in range(6, 26):
            for x in range(4, 28):
                c[y, x] = (*asphalt, 255)
        for x in range(6, 26, 4):
            for y in range(9, 23):
                c[y, x:x + 2] = (*white, 255)
        for y in range(2, 9):
            c[y, 24:26] = (*yellow, 255)
    else:
        for y in range(8, 24):
            for x in range(4, 28):
                c[y, x] = (*asphalt, 255)
        for x in range(6, 26, 4):
            for y in range(12, 20):
                c[y, x:x + 2] = (*white, 255)
        for y in range(4, 8):
            for x in range(14, 18):
                c[y, x] = (*yellow, 255)
    return c


#: категории и объекты, которые уже есть в самой игре
GAME_IDS = {
    "$cat_transport00", "$cat_road00", "$cat_roaddeco00", "$cat_intersections00",
    "$cat_bus00", "$cat_train00", "$cat_metro00", "$cat_airport00",
    "$cat_terrain00", "$cat_decoration00", "$cat_public00", "$cat_service00",
}


# ---------------------------------------------------------------------------
# проверка целостности плагина
# ---------------------------------------------------------------------------
def validate_pack(pack_dir: str):
    """Проверить ссылки и графику плагина. Возвращает список предупреждений."""
    warnings = []
    ids = {}
    drafts = []
    for name in sorted(os.listdir(pack_dir)):
        if not name.endswith(".json"):
            continue
        with open(os.path.join(pack_dir, name), encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            data = [data]
        for obj in data:
            drafts.append(obj)
            oid = obj.get("id")
            if not oid:
                warnings.append(f"{name}: объект без id")
                continue
            if oid in ids:
                warnings.append(f"дублирующийся id {oid} ({name} и {ids[oid]})")
            ids[oid] = name

    def check_frames(obj, key, where):
        frames = obj.get(key)
        if frames is None:
            return
        for fr in frames:
            bmp = fr.get("bmp")
            if bmp and not os.path.exists(os.path.join(pack_dir, bmp)):
                warnings.append(f"{where}: не найден файл {bmp}")

    for obj in drafts:
        where = f"{obj.get('type')} {obj.get('id')}"
        for key in ("frames", "preview frames", "bridge frames", "tunnel frames",
                    "slope frames", "traffic lights", "one way frames", "animation"):
            frames = obj.get(key)
            if isinstance(frames, list):
                for fr in frames:
                    if isinstance(fr, dict) and "id" not in fr and "bmp" not in fr:
                        warnings.append(f"{where}: {key} без bmp/id")
        check_frames(obj, "frames", where)
        check_frames(obj, "preview frames", where)
        check_frames(obj, "bridge frames", where)
        check_frames(obj, "tunnel frames", where)
        check_frames(obj, "slope frames", where)
        check_frames(obj, "traffic lights", where)
        check_frames(obj, "one way frames", where)
        for key in ("animation", "animation fg"):
            for ref in obj.get(key, []) or []:
                rid = ref.get("id") if isinstance(ref, dict) else None
                if rid and rid not in ids:
                    warnings.append(f"{where}: {key} ссылается на неизвестный {rid}")
        cat = obj.get("category")
        if cat and cat.startswith("$") and cat not in ids and cat not in GAME_IDS:
            warnings.append(f"{where}: неизвестная категория {cat}")
    if not os.path.exists(os.path.join(pack_dir, "plugin.manifest")):
        warnings.append("нет plugin.manifest")
    return warnings


# ---------------------------------------------------------------------------
# манифест, thumbnail, архив
# ---------------------------------------------------------------------------
def build_manifest(out_dir: str, version: int | None = None):
    manifest = {
        "id": PACK["manifest id"],
        "version": version or PACK["version"],
        "title": PACK["title"],
        "text": PACK["text"],
        "author": PACK["author"],
        "thumbnail": "thumbnail.png",
        "multiplayer": True,
    }
    with open(os.path.join(out_dir, "plugin.manifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")
    return manifest


def build_thumbnail(out_dir: str):
    """Превью плагина: 4 дороги пака на фоне травы 256x128 (в игре 2x)."""
    import numpy as np
    from PIL import Image
    w, h = 128, 64
    img = Image.new("RGBA", (w, h), (96, 140, 64, 255))
    keys = ["gravel", "rural", "street", "street1", "avenue", "avenue1", "express", "motorway"]
    x = 4
    for k in keys[:4]:
        st = roads.ROAD_STYLES[k]
        tile = roads.render_road_frame(10, st)
        sprite = art.to_image(tile)
        img.alpha_composite(sprite, (x, 12 if not st.get("tall") else 0))
        x += 32
    x = 4
    for k in keys[4:8]:
        st = roads.ROAD_STYLES[k]
        tile = roads.render_road_frame(5, st)
        sprite = art.to_image(tile)
        img.alpha_composite(sprite, (x, 40 if not st.get("tall") else 28))
        x += 32
    img.save(os.path.join(out_dir, "thumbnail.png"))
    return img


def zip_pack(pack_dir: str, zip_path: str):
    """Упаковать плагин в zip (можно переименовать в .ttplugin/.plugin)."""
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(pack_dir):
            for name in sorted(files):
                full = os.path.join(root, name)
                rel = os.path.relpath(full, pack_dir)
                z.write(full, rel)
    return zip_path
