# -*- coding: utf-8 -*-
"""Дерево на скрытом столе (msinfo32): путь по узлам, прямоугольник через
память чужого процесса, двойной клик PostMessage, выбор, снимок."""
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import OUT, finish, ok, start  # noqa: E402
from hdkit import HiddenDesktop, controls  # noqa: E402


def main():
    start("msinfo32: дерево, чужая память, двойной клик")
    with HiddenDesktop() as d:
        p = d.launch(r"C:\Windows\System32\msinfo32.exe")
        w = d.wait_window(pid=p.pid, min_size=(300, 200), timeout=40)
        w.set_rect(0, 0, 1100, 700)
        time.sleep(1.0)
        tree = w.find(cls="SysTreeView32")
        ok(tree is not None, "найдено дерево SysTreeView32")
        n0 = controls.tree_count(tree.hwnd)
        ok(n0 >= 1, "узлов в дереве: %d" % n0)
        root = controls.tree_path(tree.hwnd, [0])
        ok(root != 0 and root > 0xFFFFFFFF or root != 0,
           "корневой узел: %s (64-битный дескриптор цел)" % hex(root))
        controls.tree_expand(tree.hwnd, root)
        time.sleep(0.5)
        hk = controls.tree_path(tree.hwnd, [0, 1])
        ok(hk != 0, "второй потомок корня найден")
        rect = controls.tree_item_rect(tree.hwnd, hk)
        ok(rect[2] > rect[0] and rect[3] > rect[1],
           "прямоугольник узла из чужой памяти: %s" % (rect,))
        was = controls.tree_is_expanded(tree.hwnd, hk)
        controls.tree_open(tree.hwnd, [0, 1], double_click=True)
        time.sleep(1.0)
        sel = controls.send(tree.hwnd, controls.TVM_GETNEXTITEM,
                            controls.TVGN_CARET, 0)[1]
        ok(sel == hk, "узел выделен")
        ok(controls.tree_is_expanded(tree.hwnd, hk) != was,
           "двойной клик (PostMessage) переключил раскрытие узла")
        extra = [t for t in d.dialogs() if t != w.title]
        ok(w.alive and not extra, "окно живо, лишних диалогов нет: %s" % extra)
        img = w.capture()
        img.save(os.path.join(OUT, "msinfo32.png"))
        ok(not img.is_blank(), "снимок не пустой")
        dump = w.dump(max_depth=3)
        ok(any("SysTreeView32" in line for line in dump),
           "дамп дерева окон содержит дерево (%d строк)" % len(dump))
    return finish()


if __name__ == "__main__":
    sys.exit(main())
