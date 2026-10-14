# -*- coding: utf-8 -*-
"""Скрытый рабочий стол Windows: программа работает, человек её не видит.

    with HiddenDesktop() as d:
        p = d.launch(r"C:\\Windows\\notepad.exe")
        w = d.wait_window(cls="Notepad", timeout=15)
        w.set_rect(0, 0, 1200, 800)
        w.capture().save("shot.png")

Как это устроено: CreateDesktopW создаёт отдельный рабочий стол в сессии
пользователя. Процесс, запущенный с `STARTUPINFO.lpDesktop` этого стола,
рисует окна на нём, а не на столе пользователя. Ввод пользователя
(мышь, клавиатура, фокус) идёт только на текущий («input») стол, поэтому
скрытый стол не перехватывает управление, а программа на нём не может
украсть фокус. Дочерние процессы наследуют стол.

Ограничения (knowledge/30_ГРАБЛИ): SendInput и глобальные хоткеи сюда не
доходят — управление только сообщениями окнам (hdkit.controls); окна
видеокарты (DirectX/GPU Chromium) могут сниматься чёрными; процесс с
повышенными правами из обычного не запустить; закрывать стол и процессы
обязательно (context manager это делает).
"""
import ctypes
import os
import subprocess
import time
import uuid

from . import _win
from ._win import kernel32, user32, wt


class DesktopError(RuntimeError):
    pass


def _send_text(hwnd, msg, wparam, lparam, timeout_ms=500):
    res = ctypes.c_size_t(0)
    ok = user32.SendMessageTimeoutW(hwnd, msg, wparam, lparam,
                                    _win.SMTO_ABORTIFHUNG, timeout_ms,
                                    ctypes.byref(res))
    return bool(ok), res.value


class Window:
    """Окно или дочерний элемент: все чтения — с тайм-аутом (не виснут на
    зависшей программе)."""

    def __init__(self, hwnd):
        self.hwnd = hwnd

    def __repr__(self):
        return "<Window %s %r %r %s>" % (hex(self.hwnd or 0), self.cls,
                                          self.title, self.rect)

    def __eq__(self, other):
        return isinstance(other, Window) and other.hwnd == self.hwnd

    def __hash__(self):
        return hash(self.hwnd)

    @property
    def alive(self):
        return bool(user32.IsWindow(self.hwnd))

    @property
    def cls(self):
        b = ctypes.create_unicode_buffer(256)
        user32.GetClassNameW(self.hwnd, b, 256)
        return b.value

    @property
    def title(self):
        buf = ctypes.create_unicode_buffer(512)
        ok, _ = _send_text(self.hwnd, _win.WM_GETTEXT, 512,
                           ctypes.addressof(buf))
        return buf.value if ok else ""

    @property
    def rect(self):
        r = wt.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(r))
        return (r.left, r.top, r.right - r.left, r.bottom - r.top)

    @property
    def client_size(self):
        r = wt.RECT()
        user32.GetClientRect(self.hwnd, ctypes.byref(r))
        return (r.right, r.bottom)

    @property
    def visible(self):
        return bool(user32.IsWindowVisible(self.hwnd))

    @property
    def pid(self):
        p = wt.DWORD()
        user32.GetWindowThreadProcessId(self.hwnd, ctypes.byref(p))
        return p.value

    @property
    def ctrl_id(self):
        return user32.GetDlgCtrlID(self.hwnd)

    @property
    def parent(self):
        h = user32.GetParent(self.hwnd)
        return Window(h) if h else None

    def children(self):
        """Прямые дочерние окна (порядок Z, сверху вниз)."""
        out = []
        h = user32.GetWindow(self.hwnd, 5)
        while h:
            out.append(Window(h))
            h = user32.GetWindow(h, 2)
        return out

    def descendants(self):
        out = []
        cb = _win.WNDENUMPROC(lambda h, _l: out.append(Window(h)) or True)
        user32.EnumChildWindows(self.hwnd, cb, 0)
        return out

    def find_all(self, cls=None, title=None, ctrl_id=None, visible=None):
        """Потомки по классу (точно), подстроке заголовка, id элемента."""
        res = []
        for w in self.descendants():
            if cls is not None and w.cls != cls:
                continue
            if ctrl_id is not None and w.ctrl_id != ctrl_id:
                continue
            if title is not None and title.lower() not in w.title.lower():
                continue
            if visible is not None and w.visible != visible:
                continue
            res.append(w)
        return res

    def find(self, **kw):
        found = self.find_all(**kw)
        return found[0] if found else None

    @property
    def maximized(self):
        return bool(user32.IsZoomed(self.hwnd))

    def set_rect(self, x, y, w, h):
        """Положение и размер. Размер ограничен max_window_size().
        Развёрнутое окно сначала возвращается в обычное состояние: иначе
        рамка растёт, а содержимое не перерисовывается (30-09)."""
        if self.maximized:
            user32.ShowWindow(self.hwnd, _win.SW_RESTORE)
            time.sleep(0.3)
        user32.SetWindowPos(self.hwnd, None, x, y, w, h,
                            _win.SWP_NOZORDER | _win.SWP_NOACTIVATE
                            | _win.SWP_SHOWWINDOW)

    def show(self):
        user32.ShowWindow(self.hwnd, _win.SW_SHOWNORMAL)

    def redraw(self):
        """Заставить окно и все дочерние перерисоваться сейчас
        (RDW_INVALIDATE | RDW_ALLCHILDREN | RDW_UPDATENOW | RDW_ERASE).
        Нужно перед снимком после изменения размера, масштаба, открытия
        документа: иначе PrintWindow получает старое содержимое."""
        user32.RedrawWindow(self.hwnd, None, None, 0x1 | 0x4 | 0x80 | 0x100)

    def capture(self, flags=_win.PW_RENDERFULLCONTENT, redraw=True):
        from .capture import capture
        if redraw:
            self.redraw()
            time.sleep(0.3)
        return capture(self.hwnd, flags)

    def dump(self, depth=0, max_depth=8, out=None):
        """Дерево окон текстом: класс, id, заголовок, прямоугольник."""
        out = out if out is not None else []
        out.append("%s%s id=%s %r %s%s" % (
            "  " * depth, self.cls, self.ctrl_id, self.title[:60],
            self.rect, "" if self.visible else " (скрыто)"))
        if depth < max_depth:
            for c in self.children():
                c.dump(depth + 1, max_depth, out)
        return out


def max_window_size():
    """Наибольший размер окна верхнего уровня (SM_CXMAXTRACK/SM_CYMAXTRACK):
    больше оно не растёт, сколько ни проси SetWindowPos."""
    return (user32.GetSystemMetrics(_win.SM_CXMAXTRACK),
            user32.GetSystemMetrics(_win.SM_CYMAXTRACK))


def input_desktop_windows():
    """Видимые окна верхнего уровня на столе человека: (hwnd, класс,
    заголовок). Для проверки, что скрытая работа его не меняет."""
    out = []

    def cb(h, _l):
        if user32.IsWindowVisible(h):
            w = Window(h)
            out.append((h, w.cls, w.title))
        return True
    user32.EnumWindows(_win.WNDENUMPROC(cb), 0)
    return out


def foreground_window():
    return user32.GetForegroundWindow()


class Process:
    def __init__(self, handle, pid):
        self.handle, self.pid = handle, pid

    @property
    def running(self):
        return kernel32.WaitForSingleObject(self.handle, 0) == 0x102

    @property
    def exit_code(self):
        c = wt.DWORD()
        kernel32.GetExitCodeProcess(self.handle, ctypes.byref(c))
        return None if c.value == 259 else c.value

    def terminate(self):
        if self.handle:
            kernel32.TerminateProcess(self.handle, 1)
            kernel32.WaitForSingleObject(self.handle, 3000)
            kernel32.CloseHandle(self.handle)
            self.handle = None


class HiddenDesktop:
    """Отдельный рабочий стол. Только через `with` или с close() в finally:
    без закрытия остаются процессы, которых человек не видит."""

    def __init__(self, name=None):
        self.name = name or "hdkit_%s" % uuid.uuid4().hex[:8]
        self.handle = user32.CreateDesktopW(self.name, None, None, 0,
                                            _win.GENERIC_ALL, None)
        if not self.handle:
            raise DesktopError("CreateDesktopW: ошибка %d"
                               % ctypes.get_last_error())
        self.procs = []
        self._si_name = None

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

    def launch(self, cmd, cwd=None, env=None):
        """Запустить программу на этом столе. cmd — строка или список.
        Возвращает Process. Кавычки вокруг путей с пробелами —
        subprocess.list2cmdline."""
        if not isinstance(cmd, str):
            cmd = subprocess.list2cmdline([str(c) for c in cmd])
        si = _win.STARTUPINFOW()
        si.cb = ctypes.sizeof(si)
        self._si_name = ctypes.create_unicode_buffer(self.name)
        si.lpDesktop = ctypes.cast(self._si_name, wt.LPWSTR)
        pi = _win.PROCESS_INFORMATION()
        buf = ctypes.create_unicode_buffer(cmd)
        envp = None
        if env is not None:
            blk = "\0".join("%s=%s" % kv for kv in env.items()) + "\0\0"
            envp = ctypes.create_unicode_buffer(blk, len(blk))
        ok = kernel32.CreateProcessW(
            None, buf, None, None, False, 0x00000400 if envp else 0,
            ctypes.cast(envp, ctypes.c_void_p) if envp else None, cwd,
            ctypes.byref(si), ctypes.byref(pi))
        if not ok:
            err = ctypes.get_last_error()
            hint = (" — программа требует повышенных прав (UAC): из обычного "
                    "процесса её не запустить, ни на скрытом столе, ни на "
                    "обычном без согласия человека") if err == 740 else ""
            raise DesktopError("CreateProcess(%s): ошибка %d%s"
                               % (cmd, err, hint))
        kernel32.CloseHandle(pi.hThread)
        p = Process(pi.hProcess, pi.dwProcessId)
        self.procs.append(p)
        return p

    def windows(self, visible_only=False):
        """Окна верхнего уровня этого стола."""
        out = []

        def cb(h, _l):
            w = Window(h)
            if not visible_only or w.visible:
                out.append(w)
            return True
        user32.EnumDesktopWindows(self.handle, _win.WNDENUMPROC(cb), 0)
        return out

    def find_window(self, title=None, cls=None, pid=None, min_size=(0, 0),
                    visible=None):
        for w in self.windows():
            if cls is not None and w.cls != cls:
                continue
            if pid is not None and w.pid != pid:
                continue
            if visible is not None and w.visible != visible:
                continue
            x, y, ww, hh = w.rect
            if ww < min_size[0] or hh < min_size[1]:
                continue
            if title is not None and title.lower() not in w.title.lower():
                continue
            return w
        return None

    def wait_window(self, title=None, cls=None, pid=None, timeout=15.0,
                    min_size=(0, 0), stable=0.4, visible=True):
        """Ждать окно с признаками и устойчивым размером (программы
        собирают окно не сразу: сначала заготовка 40x40)."""
        t0 = time.time()
        last, since = None, 0.0
        while time.time() - t0 < timeout:
            w = self.find_window(title, cls, pid, min_size, visible)
            if w is not None:
                key = (w.hwnd, w.rect)
                if key == last and time.time() - since >= stable:
                    return w
                if key != last:
                    last, since = key, time.time()
            else:
                last = None
            time.sleep(0.1)
        raise DesktopError(
            "окно не появилось за %.0f с (title=%r cls=%r). Есть: %s"
            % (timeout, title, cls,
               [(w.cls, w.title[:30]) for w in self.windows()]))

    def dialogs(self):
        """Видимые стандартные диалоги (#32770) стола: заголовки. Любой
        диалог — повод остановиться и разобраться, а не нажимать вслепую."""
        return [w.title for w in self.windows(visible_only=True)
                if w.cls == "#32770"]

    def close(self):
        """Завершить процессы стола (запущенные и владельцы его окон)
        и закрыть стол. Безопасно вызывать повторно."""
        if not self.handle:
            return
        me = kernel32.GetCurrentProcessId()
        pids = {p.pid for p in self.procs}
        for w in self.windows():
            if w.pid != me:
                pids.add(w.pid)
        for p in self.procs:
            p.terminate()
        for pid in pids:
            h = kernel32.OpenProcess(0x0001, False, pid)
            if h:
                kernel32.TerminateProcess(h, 1)
                kernel32.CloseHandle(h)
        time.sleep(0.2)
        user32.CloseDesktop(self.handle)
        self.handle = None
