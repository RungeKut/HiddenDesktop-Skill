# -*- coding: utf-8 -*-
"""Минимальный сквозной пример: Блокнот на скрытом столе, текст, снимок."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hdkit import HiddenDesktop, controls  # noqa: E402


def main(out="notepad_demo.png"):
    with HiddenDesktop() as d:
        d.launch([r"C:\Windows\System32\notepad.exe"])
        w = d.wait_window(cls="Notepad", timeout=20)
        w.set_rect(0, 0, 1000, 600)
        edit = w.find(cls="Edit")
        controls.set_text(edit, "Скрытый рабочий стол: человек этого окна не видит")
        time.sleep(0.5)
        img = w.capture()
        img.save(out)
        print("снимок %s %dx%d, пустой: %s" % (out, img.width, img.height,
                                                img.is_blank()))
        print("\n".join(w.dump()))


if __name__ == "__main__":
    main(*sys.argv[1:2])
