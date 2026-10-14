# -*- coding: utf-8 -*-
r"""hdkit — работа с программами на скрытом рабочем столе Windows.

Программа запускается на отдельном рабочем столе (CreateDesktop): окна
не появляются у человека, фокус, мышь и клавиатура остаются его. Снимок —
PrintWindow, управление — оконными сообщениями.

    from hdkit import HiddenDesktop, controls

    with HiddenDesktop() as d:
        d.launch(r"C:Windows\notepad.exe")
        w = d.wait_window(cls="Notepad")
        edit = w.find(cls="Edit")
        controls.set_text(edit, "привет")
        w.capture().save("shot.png")

Подробно — knowledge/INDEX.md и skill/SKILL.md.
"""
__version__ = "0.1.0"

from . import controls
from .capture import CaptureError, Image, capture
from .desktop import (DesktopError, HiddenDesktop, Process, Window,
                      foreground_window, input_desktop_windows,
                      max_window_size)
