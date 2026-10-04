#!/usr/bin/env python3
"""Собрать стартовый сектор российских жилых зданий для TheoTown.

Запуск из корня репозитория:
    python3 tools/build_residential.py

Результат:
    dist/TheoRussianHomesStarter/                 # папка плагина
    dist/TheoRussianHomesStarter-v1.0.0.plugin   # архив для импорта в игру
    dist/theo-russian-homes-starter-v1.0.0.zip   # тот же архив в ZIP
    dist/preview_residential_ru.png              # каталог-превью
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import zipfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from theo_pack import residential  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_DIST = os.path.join(ROOT, "dist")

INSTALL_GUIDE = """ЖИЛЫЕ ДОМА РФ — НАЧАЛЬНЫЙ СЕКТОР
====================================

Файлы:
  TheoRussianHomesStarter-v1.0.0.plugin -- готовый пакет TheoTown
  theo-russian-homes-starter-v1.0.0.zip -- тот же пакет в формате ZIP
  TheoRussianHomesStarter/              -- распакованная папка плагина

Установка:
1. Скопируйте .plugin в папку TheoTown/plugins либо импортируйте файл
   через файловый менеджер игры в разделе региона.
2. Полностью перезапустите TheoTown.
3. Запустите город и выделите жилую зону. Все здания набора относятся
   к жилому уровню 1 и могут появляться по мере застройки зоны.

В наборе три здания: деревянный дом в селе (1x1), кирпичная дача (1x1)
и пятиэтажный панельный дом (2x2). ID объектов постоянны — не меняйте их,
если уже сохранили город с этим плагином.
"""


def _write_archive(pack_dir: str, zip_path: str) -> None:
    root_name = os.path.basename(os.path.normpath(pack_dir))
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
        for current, _dirs, files in os.walk(pack_dir):
            for filename in sorted(files):
                full_path = os.path.join(current, filename)
                relative = os.path.relpath(full_path, pack_dir)
                archive.write(full_path, os.path.join(root_name, relative))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Собрать стартовый сектор жилых зданий РФ для TheoTown"
    )
    parser.add_argument("--dist", default=DEFAULT_DIST,
                        help="папка для результатов (по умолчанию dist/)")
    args = parser.parse_args()

    dist_dir = os.path.abspath(args.dist)
    os.makedirs(dist_dir, exist_ok=True)
    pack_dir = os.path.join(dist_dir, residential.PACK_DIRNAME)

    # Пересобираем только свой модуль; пак дорог и остальные файлы dist не трогаем.
    if os.path.isdir(pack_dir):
        shutil.rmtree(pack_dir)
    os.makedirs(pack_dir, exist_ok=True)

    drafts = residential.build_starter_sector(pack_dir)
    problems = residential.validate_pack(pack_dir)
    if problems:
        print("ОШИБКИ В ПАКЕ:")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    preview_path = os.path.join(dist_dir, "preview_residential_ru.png")
    residential.build_preview(pack_dir, preview_path)

    version = residential.PACK_VERSION
    zip_path = os.path.join(dist_dir, f"theo-russian-homes-starter-v{version}.zip")
    plugin_path = os.path.join(dist_dir, f"TheoRussianHomesStarter-v{version}.plugin")
    _write_archive(pack_dir, zip_path)
    shutil.copyfile(zip_path, plugin_path)

    guide_path = os.path.join(dist_dir, "КАК-УСТАНОВИТЬ-ЖИЛЬЁ.txt")
    with open(guide_path, "w", encoding="utf-8") as guide:
        guide.write(INSTALL_GUIDE)

    print("Проверка пройдена: JSON, манифест, PNG и ссылки кадров корректны.")
    print(f"зданий:   {len(drafts)} (все — residential level 1)")
    print(f"папка:    {pack_dir}")
    print(f"плагин:   {plugin_path}")
    print(f"архив:    {zip_path}")
    print(f"превью:   {preview_path}")
    print(f"инструкция: {guide_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
