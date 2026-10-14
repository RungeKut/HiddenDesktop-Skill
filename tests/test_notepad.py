# -*- coding: utf-8 -*-
"""Блокнот на скрытом столе: запуск, текст, снимок — и главное: стол
человека не изменился (окна, фокус)."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import OUT, finish, ok, start  # noqa: E402
from hdkit import (HiddenDesktop, controls, foreground_window,  # noqa: E402
                   input_desktop_windows)


def main():
    start("notepad на скрытом столе")
    before_fg = foreground_window()
    before = {w[0] for w in input_desktop_windows()}
    with HiddenDesktop() as d:
        d.launch(r"C:\Windows\System32\notepad.exe")
        w = d.wait_window(cls="Notepad", timeout=20)
        ok(w.visible, "окно Блокнота появилось на скрытом столе")
        w.set_rect(0, 0, 900, 500)
        edit = w.find(cls="Edit") or w.find(cls="RichEditD2DPT")
        ok(edit is not None, "найдено поле ввода: %s" % (edit,))
        text = "Hello hidden desktop"
        controls.set_text(edit, text)
        time.sleep(0.5)
        ok(controls.get_text(edit) == text, "текст записан и прочитан")
        img = w.capture()
        path = img.save(os.path.join(OUT, "notepad.png"))
        ok(img.size[0] >= 800 and img.size[1] >= 400,
           "снимок %dx%d" % img.size)
        ok(not img.is_blank(), "снимок не пустой")
        ok(img.dark_fraction() > 0.0005, "на снимке есть текст (тёмные пиксели)")
        ok(os.path.getsize(path) > 1000, "PNG записан: %s" % path)
        crop = img.crop((0, 0, 200, 100))
        ok(crop.size == (200, 100), "вырезка")
    after = {w[0] for w in input_desktop_windows()}
    ok(foreground_window() == before_fg, "активное окно человека не сменилось")
    ok(after == before, "на столе человека нет новых/пропавших окон")
    return finish()


if __name__ == "__main__":
    sys.exit(main())
