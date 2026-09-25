#!/usr/bin/env python3
"""Сборка пака дорог TheoTown.

Использование:
    python3 tools/build_pack.py            # собрать пак в dist/
    python3 tools/build_pack.py --preview  # + демонстрационные картинки

Результат:
    dist/TheoRoadsPack/                  -- папка плагина (можно кинуть в TheoTown/plugins)
    dist/theo-roads-pack-v1.0.0.zip      -- готовый архив для установки
    dist/preview_*.png                   -- картинки для описания/форума
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theo_pack import plugins, preview, roads  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")

INSTALL_GUIDE = """ПАК ДОРОГ THEO -- УСТАНОВКА В THEOTOWN
======================================

Файлы:
  TheoRoadsPack-v1.0.0.plugin   -- положить в папку плагинов, распаковывать НЕ надо
  theo-roads-pack-v1.0.0.zip    -- то же самое (если игра не читает .plugin)
  TheoRoadsPack/                -- готовая папка плагина


СПОСОБ 1 (проще всего) -- через файловый менеджер самой игры
-----------------------------------------------------------
1. Скачайте на телефон TheoRoadsPack-v1.0.0.plugin (или .zip) в Загрузки.
2. Запустите TheoTown, выйдите из города в вид региона.
3. Меню (три полоски/шестерёнка) -> Файловый менеджер (File manager).
4. Откройте папку "plugins" внутри игры.
5. Нажмите "Импорт файла(ов)" / Import file(s) и выберите скачанный файл.
6. Полностью закройте игру (смахните из недавних) и запустите заново.


СПОСОБ 2 -- скопировать файл в папку плагинов
--------------------------------------------
Путь на Android:
  Android/data/info.flowersoft.theotown.theotown/files/plugins

На Android 11+ обычный проводник в эту папку не пускает. Используйте
ZArchiver, MiXplorer или "Files by Google": при первом заходе приложение
спросит доступ -> "Разрешить"/"Use this folder".

Положите .plugin или .zip прямо в plugins (распаковывать не нужно).
Если игра архив не увидела -- распакуйте его в plugins, получится папка
TheoRoadsPack. Перезапустите игру.

На старых Android (10 и ниже) папка может быть тут:
  Internal Storage/TheoTown/plugins


СПОСОБ 3 -- установка с компьютера
---------------------------------
Windows: C:/Users/<имя>/TheoTown/plugins
Linux:   ~/TheoTown/plugins
Подключите телефон кабелем (режим передачи файлов), скопируйте туда
файл .plugin или распакованную папку TheoRoadsPack, перезапустите игру.


ПРОВЕРКА
--------
Настройки -> Плагины: в списке локальных плагинов появится
"Theo Roads Pack". В городе новые дороги лежат в разделе транспорта,
категория "Theo Roads".

ВАЖНО
-----
* Не удаляйте плагин из папки, если города уже сохранены с этими дорогами --
  иначе дороги в сохранении не загрузятся.
* Плагин работает и в мультиплеере.
"""



def main():
    ap = argparse.ArgumentParser(description="Сборка пака дорог Theo для TheoTown")
    ap.add_argument("--preview", action="store_true", help="собрать демо-картинки")
    ap.add_argument("--dist", default=DIST)
    args = ap.parse_args()

    pack_name = "TheoRoadsPack"
    pack_dir = os.path.join(args.dist, pack_name)
    if os.path.isdir(pack_dir):
        shutil.rmtree(pack_dir)
    os.makedirs(pack_dir, exist_ok=True)

    # 1. графика и JSON
    road_drafts = plugins.build_roads(pack_dir)
    deco_drafts = plugins.build_decorations(pack_dir)
    cat_drafts = plugins.build_categories(pack_dir)

    # 2. светофоры и стрелки односторонних дорог
    from theo_pack import art
    art.frames_to_sheet(roads.build_traffic_lights()).save(
        os.path.join(pack_dir, "traffic_lights.png"))
    art.frames_to_sheet(roads.build_one_way_frames(roads.ROAD_STYLES["motorway"])).save(
        os.path.join(pack_dir, "oneway_arrows.png"))

    # 3. JSON-файлы (порядок загрузки задаётся именами)
    plugins.write_json(os.path.join(pack_dir, "00_categories.json"), cat_drafts)
    plugins.write_json(os.path.join(pack_dir, "05_decorations.json"), deco_drafts)
    plugins.write_json(os.path.join(pack_dir, "10_roads.json"), road_drafts)

    # 4. манифест и превью
    manifest = plugins.build_manifest(pack_dir)
    plugins.build_thumbnail(pack_dir)

    # 5. архив
    version = f"v{manifest['version']}.0.0"
    zip_path = os.path.join(args.dist, f"theo-roads-pack-{version}.zip")
    plugins.zip_pack(pack_dir, zip_path)
    # тот же архив с расширением .plugin: такие файлы в TheoTown кладут
    # в папку плагинов не распаковывая
    plugin_path = os.path.join(args.dist, f"TheoRoadsPack-{version}.plugin")
    shutil.copyfile(zip_path, plugin_path)

    # краткая инструкция рядом с архивом
    guide = os.path.join(args.dist, "КАК-УСТАНОВИТЬ.txt")
    with open(guide, "w", encoding="utf-8") as f:
        f.write(INSTALL_GUIDE)
    print(f"инструкция: {guide}")

    problems = plugins.validate_pack(pack_dir)
    if problems:
        print("ВНИМАНИЕ:")
        for w in problems:
            print("  -", w)

    print(f"плагин:  {pack_dir}")
    print(f"архив:   {zip_path}")
    print(f"плагин:  {plugin_path}")
    print(f"дорог:   {len(road_drafts)}")
    print(f"украшений: {len([d for d in deco_drafts if d['type'] == 'road decoration'])}")

    if args.preview:
        previews = preview.build_all(pack_dir, args.dist)
        for p in previews:
            print("превью: ", p)


if __name__ == "__main__":
    main()
