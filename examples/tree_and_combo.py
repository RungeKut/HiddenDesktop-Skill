# -*- coding: utf-8 -*-
"""Дерево: найти узел по пути, выделить, раскрыть двойным кликом
(PostMessage), прочитать состояние. Выпадающий список — в
combo_items/combo_select (пример в vskit/shot.py набора VisualState-Kit)."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from hdkit import HiddenDesktop, controls  # noqa: E402


def main():
    with HiddenDesktop() as d:
        p = d.launch([r"C:\Windows\System32\msinfo32.exe"])
        w = d.wait_window(pid=p.pid, min_size=(300, 200), timeout=40)
        w.set_rect(0, 0, 1200, 800)
        time.sleep(1)
        tree = w.find(cls="SysTreeView32")
        node = controls.tree_path(tree.hwnd, [0, 1])
        print("раскрыт до:", controls.tree_is_expanded(tree.hwnd, node))
        controls.tree_open(tree.hwnd, [0, 1], double_click=True)
        time.sleep(1)
        print("раскрыт после:", controls.tree_is_expanded(tree.hwnd, node))
        w.capture().save("tree_demo.png")


if __name__ == "__main__":
    main()
