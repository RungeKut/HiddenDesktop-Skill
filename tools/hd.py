# -*- coding: utf-8 -*-
r"""Запустить программу на скрытом рабочем столе, снять окно, вывести дерево.

    python tools/hd.py run --shot out.png -- C:\Windows\notepad.exe
    python tools/hd.py run --class Notepad --size 1200x800 --dump -- notepad.exe
    python tools/hd.py info

Ключи run:
  --title ПОДСТРОКА   ждать окно с такой подстрокой в заголовке
  --class КЛАСС       ждать окно этого класса (точно)
  --wait СЕК          сколько ждать окно (по умолчанию 20)
  --size WxH          растянуть окно (не больше `info`)
  --settle СЕК        пауза перед снимком (по умолчанию 1.0)
  --shot ФАЙЛ         сохранить снимок окна (.png или .bmp)
  --crop x0,y0,x1,y1  вырезать область снимка (в пикселях снимка)
  --dump              напечатать дерево окон
  --keep СЕК          подержать программу ещё столько секунд (отладка)

Всё, что запустили, завершается при выходе (даже при ошибке).
Код возврата: 0 — окно нашлось и снято; 1 — окно не появилось;
2 — снимок пустой.
"""
import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hdkit import DesktopError, HiddenDesktop, max_window_size  # noqa: E402


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    argv = sys.argv[1:]
    if argv and argv[0] == "info":
        print("максимальный размер окна: %dx%d" % max_window_size())
        return 0
    ap = argparse.ArgumentParser(prog="hd.py run")
    ap.add_argument("cmd", choices=["run"])
    ap.add_argument("--title")
    ap.add_argument("--class", dest="cls")
    ap.add_argument("--wait", type=float, default=20.0)
    ap.add_argument("--size")
    ap.add_argument("--settle", type=float, default=1.0)
    ap.add_argument("--shot")
    ap.add_argument("--crop")
    ap.add_argument("--dump", action="store_true")
    ap.add_argument("--keep", type=float, default=0.0)
    if "--" not in argv:
        ap.error("программа указывается после --")
    cut = argv.index("--")
    a = ap.parse_args(argv[:cut])
    prog = argv[cut + 1:]
    if not prog:
        ap.error("после -- укажите программу")
    with HiddenDesktop() as d:
        p = d.launch(prog)
        try:
            w = d.wait_window(title=a.title, cls=a.cls,
                              pid=None if (a.title or a.cls) else p.pid,
                              timeout=a.wait, min_size=(100, 60))
        except DesktopError as e:
            print(e)
            return 1
        if a.size:
            ww, hh = map(int, a.size.lower().split("x"))
            w.set_rect(0, 0, ww, hh)
        time.sleep(a.settle)
        print("окно: %r %r %s" % (w.cls, w.title, w.rect))
        if a.dump:
            print("\n".join(w.dump()))
        rc = 0
        if a.shot:
            img = w.capture()
            if a.crop:
                img = img.crop([int(v) for v in a.crop.split(",")])
            img.save(a.shot)
            print("снимок: %s %dx%d%s" % (a.shot, img.width, img.height,
                                          " (ПУСТОЙ)" if img.is_blank() else ""))
            rc = 2 if img.is_blank() else 0
        if a.keep:
            time.sleep(a.keep)
        return rc


if __name__ == "__main__":
    sys.exit(main())
