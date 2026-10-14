# -*- coding: utf-8 -*-
"""Управление окнами скрытого стола сообщениями, без мыши и клавиатуры.

Реальный ввод (SendInput, хоткеи, SetForegroundWindow) на скрытый стол не
попадает — и не должен: это защита человека. Управление — оконными
сообщениями: чтение/запись текста, клики кнопкам, выбор в списках и
деревьях, прокрутка, вставка символов.

Правила (за каждым — потерянный час, см. knowledge/30_ГРАБЛИ):
  * чтение и ожидание ответа — только SendMessageTimeout (`send`), никогда
    голый SendMessage: зависшее окно подвесит скрипт;
  * мышиные сообщения — только PostMessage (`click`): SendMessage с
    WM_LBUTTONDOWN на дерево/список вешает его в DragDetect;
  * 64-битные дескрипторы (HWND, HTREEITEM) — только через эти функции.
"""
import ctypes
import struct
import time

from . import _win
from ._win import kernel32, user32, wt

WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x100, 0x101, 0x102
WM_COMMAND = 0x111
WM_HSCROLL, WM_VSCROLL = 0x114, 0x115
WM_LBUTTONDOWN, WM_LBUTTONUP, WM_LBUTTONDBLCLK = 0x201, 0x202, 0x203
WM_RBUTTONDOWN, WM_RBUTTONUP = 0x204, 0x205
WM_MOUSEWHEEL = 0x20A
BM_CLICK = 0x00F5
CB_GETCOUNT, CB_GETLBTEXT, CB_GETLBTEXTLEN = 0x146, 0x148, 0x149
CB_SETCURSEL, CB_GETCURSEL = 0x14E, 0x147
CBN_SELCHANGE, CBN_SELENDOK = 1, 9
LB_SETCURSEL, LB_GETCOUNT = 0x186, 0x18B
TVM_GETITEMRECT, TVM_GETCOUNT, TVM_GETNEXTITEM, TVM_SELECTITEM = \
    0x1104, 0x1105, 0x110A, 0x110B
TVGN_ROOT, TVGN_NEXT, TVGN_PARENT, TVGN_CHILD, TVGN_CARET = 0, 1, 3, 4, 9
TVM_EXPAND = 0x1102
TVE_EXPAND = 2
SB_HORZ, SB_VERT = 0, 1
SB_LINEUP, SB_LINEDOWN, SB_PAGEUP, SB_PAGEDOWN = 0, 1, 2, 3
VK_RETURN, VK_ESCAPE, VK_TAB, VK_DOWN, VK_UP = 0x0D, 0x1B, 0x09, 0x28, 0x26


def _h(w):
    return getattr(w, "hwnd", w)


def send(w, msg, wparam=0, lparam=0, timeout_ms=2000):
    """SendMessageTimeout: (получилось, результат). Не виснет на зависшем
    окне — возвращает (False, 0)."""
    res = ctypes.c_size_t(0)
    ok = user32.SendMessageTimeoutW(_h(w), msg, wparam, lparam,
                                    _win.SMTO_ABORTIFHUNG, timeout_ms,
                                    ctypes.byref(res))
    return bool(ok), res.value


def post(w, msg, wparam=0, lparam=0):
    return bool(user32.PostMessageW(_h(w), msg, wparam, lparam))


def _lp(x, y):
    return ((y & 0xFFFF) << 16) | (x & 0xFFFF)


def get_text(w):
    n = send(w, _win.WM_GETTEXTLENGTH)[1]
    buf = ctypes.create_unicode_buffer(n + 2)
    send(w, _win.WM_GETTEXT, n + 1, ctypes.addressof(buf))
    return buf.value


def set_text(w, text):
    """Записать текст в поле (WM_SETTEXT)."""
    buf = ctypes.create_unicode_buffer(text)
    return send(w, _win.WM_SETTEXT, 0, ctypes.addressof(buf))[0]


def type_text(w, text, delay=0.0):
    """Вставить символы в окно с фокусом ввода (WM_CHAR по одному)."""
    for ch in text:
        post(w, WM_CHAR, ord(ch), 1)
        if delay:
            time.sleep(delay)


def press(w, vk, hold=0.0):
    """Нажать клавишу сообщением (Enter, Esc, Tab, стрелки)."""
    post(w, WM_KEYDOWN, vk, 1)
    if hold:
        time.sleep(hold)
    post(w, WM_KEYUP, vk, 0xC0000001)


def click(w, x, y, double=False, right=False, pause=0.15):
    """Клик в клиентских координатах окна w — ТОЛЬКО PostMessage."""
    down, up = (WM_RBUTTONDOWN, WM_RBUTTONUP) if right else \
        (WM_LBUTTONDOWN, WM_LBUTTONUP)
    lp = _lp(x, y)
    post(w, down, 1, lp)
    time.sleep(pause)
    post(w, up, 0, lp)
    if double:
        time.sleep(pause)
        post(w, WM_LBUTTONDBLCLK, 1, lp)
        time.sleep(pause)
        post(w, up, 0, lp)


def button_click(w):
    """Нажать кнопку (BM_CLICK) — надёжнее клика по координатам."""
    return post(w, BM_CLICK)


def command(parent, ctrl_id, notify=0, ctrl=None):
    """WM_COMMAND родителю: как будто элемент сообщил о событии."""
    return send(parent, WM_COMMAND, (notify << 16) | (ctrl_id & 0xFFFF),
                _h(ctrl) if ctrl is not None else 0)[0]


def combo_items(combo):
    n = send(combo, CB_GETCOUNT)[1]
    items = []
    for i in range(n):
        ln = send(combo, CB_GETLBTEXTLEN, i)[1]
        buf = ctypes.create_unicode_buffer(ln + 2)
        send(combo, CB_GETLBTEXT, i, ctypes.addressof(buf))
        items.append(buf.value)
    return items


def combo_select(combo, index, notify=True):
    """Выбрать пункт списка и сообщить родителю (иначе программа не узнает
    о выборе: CB_SETCURSEL сам уведомления не шлёт)."""
    send(combo, CB_SETCURSEL, index, 0)
    if notify:
        parent = user32.GetParent(_h(combo))
        cid = user32.GetDlgCtrlID(_h(combo))
        command(parent, cid, CBN_SELENDOK, combo)
        command(parent, cid, CBN_SELCHANGE, combo)


def scroll_info(w, bar=SB_VERT):
    si = _win.SCROLLINFO()
    si.cbSize = ctypes.sizeof(si)
    si.fMask = 0x17
    user32.GetScrollInfo(_h(w), bar, ctypes.byref(si))
    return {"min": si.nMin, "max": si.nMax, "page": si.nPage, "pos": si.nPos}


def scroll(w, code=SB_PAGEDOWN, times=1, bar=SB_VERT):
    """Прокрутка окна сообщением WM_VSCROLL/WM_HSCROLL (SB_PAGEDOWN и т. п.).
    Окну, а не его полосе: полосу рисует окно-владелец."""
    msg = WM_VSCROLL if bar == SB_VERT else WM_HSCROLL
    for _ in range(times):
        send(w, msg, code, 0)


class RemoteBuffer:
    """Память в ЧУЖОМ процессе — для сообщений, где lParam указывает на
    структуру (TVM_GETITEMRECT, LVM_GETITEMTEXT…). Адрес из нашего процесса
    чужому не годится."""

    def __init__(self, hwnd, size=256):
        pid = wt.DWORD()
        user32.GetWindowThreadProcessId(_h(hwnd), ctypes.byref(pid))
        self.proc = kernel32.OpenProcess(_win.PROCESS_ALL_FOR_MEMORY, False,
                                         pid.value)
        if not self.proc:
            raise OSError("OpenProcess: нет доступа к процессу %d" % pid.value)
        self.addr = kernel32.VirtualAllocEx(self.proc, None, size, 0x3000, 4)
        self.size = size

    def write(self, data):
        n = _win.SIZE_T(0)
        kernel32.WriteProcessMemory(self.proc, self.addr, data, len(data),
                                    ctypes.byref(n))

    def read(self, size):
        buf = ctypes.create_string_buffer(size)
        n = _win.SIZE_T(0)
        kernel32.ReadProcessMemory(self.proc, self.addr, buf, size,
                                   ctypes.byref(n))
        return buf.raw

    def close(self):
        if self.addr:
            kernel32.VirtualFreeEx(self.proc, self.addr, 0, 0x8000)
            self.addr = None
        if self.proc:
            kernel32.CloseHandle(self.proc)
            self.proc = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()


def tree_count(tree):
    return send(tree, TVM_GETCOUNT)[1]


def tree_root(tree):
    return send(tree, TVM_GETNEXTITEM, TVGN_ROOT, 0)[1]


def tree_child(tree, item):
    return send(tree, TVM_GETNEXTITEM, TVGN_CHILD, item)[1]


def tree_next(tree, item):
    return send(tree, TVM_GETNEXTITEM, TVGN_NEXT, item)[1]


def tree_path(tree, indexes):
    """Узел дерева по пути индексов: [0, 1, 2] — первый корневой, его
    второй потомок, у него третий. Возвращает HTREEITEM или 0."""
    item = tree_root(tree)
    for depth, idx in enumerate(indexes):
        if depth:
            item = tree_child(tree, item)
        for _ in range(idx):
            item = tree_next(tree, item)
        if not item:
            return 0
    return item


def tree_select(tree, item):
    return send(tree, TVM_SELECTITEM, TVGN_CARET, item)[0]


def tree_expand(tree, item):
    return send(tree, TVM_EXPAND, TVE_EXPAND, item)[0]


def tree_is_expanded(tree, item):
    """Раскрыт ли узел (TVM_GETITEMSTATE, бит TVIS_EXPANDED)."""
    return bool(send(tree, 0x1127, item, 0x20)[1] & 0x20)


def tree_item_rect(tree, item):
    """Прямоугольник узла в клиентских координатах дерева (left, top,
    right, bottom); (0,0,0,0), если узел не виден."""
    with RemoteBuffer(tree, 64) as rb:
        rb.write(struct.pack("<Q", item))
        ok, res = send(tree, TVM_GETITEMRECT, 1, rb.addr)
        data = rb.read(16)
    rect = struct.unpack("<4i", data)
    return rect if res else (0, 0, 0, 0)


def tree_open(tree, indexes, double_click=True):
    """Выделить узел и «открыть» его двойным кликом (PostMessage).
    Для деревьев, где двойной клик открывает документ/окно."""
    item = tree_path(tree, indexes)
    if not item:
        raise LookupError("нет узла %r" % (indexes,))
    tree_select(tree, item)
    l, t, r, b = tree_item_rect(tree, item)
    if r == l:
        raise LookupError("узел %r не виден (раскрыть родителей)" % indexes)
    click(tree, (l + r) // 2, (t + b) // 2, double=double_click)
    return item
