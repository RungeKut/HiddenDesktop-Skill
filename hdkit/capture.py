# -*- coding: utf-8 -*-
"""Снимок окна без показа на экране: PrintWindow(PW_RENDERFULLCONTENT).

Окно рисует себя само в память — человек ничего не видит, фокус и мышь
не затрагиваются. Работает для программ на GDI/MFC/WinForms/Win32/Qt и
большинства WPF; не работает для окон, которые рисует видеокарта в обход
GDI (DirectX/OpenGL-полноэкранное, часть Chromium/Electron без
`--disable-gpu`): снимок получается чёрным — проверять `Image.is_blank()`.

    img = capture(hwnd)
    img.save("shot.png")            # PNG без зависимостей
    img.crop((x0, y0, x1, y1)).save("part.png")
    img.is_blank()                  # True — снимок пустой/чёрный/белый
"""
import ctypes
import struct
import zlib

from . import _win
from ._win import gdi32, user32, wt


class CaptureError(RuntimeError):
    pass


class Image:
    """Растровое изображение BGRA (как отдаёт DIB), без внешних модулей."""

    def __init__(self, width, height, bgra):
        self.width, self.height, self.bgra = width, height, bytes(bgra)

    @property
    def size(self):
        return (self.width, self.height)

    def crop(self, box):
        x0, y0, x1, y1 = [int(v) for v in box]
        x0, y0 = max(x0, 0), max(y0, 0)
        x1, y1 = min(x1, self.width), min(y1, self.height)
        if x1 <= x0 or y1 <= y0:
            raise CaptureError("пустая область %r" % (box,))
        row = self.width * 4
        out = bytearray()
        for y in range(y0, y1):
            out += self.bgra[y * row + x0 * 4:y * row + x1 * 4]
        return Image(x1 - x0, y1 - y0, out)

    def is_blank(self, tolerance=0):
        """True, если все пиксели одного цвета (кроме допуска)."""
        b = self.bgra
        if not b:
            return True
        first = b[0:3]
        step = max(4, len(b) // 4000 // 4 * 4)
        for i in range(0, len(b), step):
            px = b[i:i + 3]
            if max(abs(px[k] - first[k]) for k in range(3)) > tolerance:
                return False
        return True

    def dark_fraction(self, level=128):
        """Доля тёмных пикселей — грубая проверка, что на снимке есть текст."""
        b = self.bgra
        n = dark = 0
        for i in range(0, len(b), 4 * 7):
            n += 1
            if (b[i] + b[i + 1] + b[i + 2]) // 3 < level:
                dark += 1
        return dark / n if n else 0.0

    def to_png(self):
        w, h = self.width, self.height
        rgb = bytearray(w * h * 3)
        rgb[0::3] = self.bgra[2::4]
        rgb[1::3] = self.bgra[1::4]
        rgb[2::3] = self.bgra[0::4]
        raw = bytearray()
        row = w * 3
        for y in range(h):
            raw.append(0)
            raw += rgb[y * row:(y + 1) * row]

        def chunk(tag, data):
            body = tag + data
            return (struct.pack(">I", len(data)) + body
                    + struct.pack(">I", zlib.crc32(body) & 0xFFFFFFFF))
        return (b"\x89PNG\r\n\x1a\n"
                + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(bytes(raw), 6))
                + chunk(b"IEND", b""))

    def save(self, path):
        path = str(path)
        if path.lower().endswith(".bmp"):
            row = self.width * 4
            hdr = struct.pack("<2sIHHI", b"BM", 54 + row * self.height,
                              0, 0, 54)
            dib = struct.pack("<IiiHHIIiiII", 40, self.width, -self.height,
                              1, 32, 0, row * self.height, 2835, 2835, 0, 0)
            data = hdr + dib + self.bgra
        else:
            data = self.to_png()
        with open(path, "wb") as f:
            f.write(data)
        return path

    def to_pil(self):
        from PIL import Image as PI
        return PI.frombuffer("RGBA", (self.width, self.height), self.bgra,
                             "raw", "BGRA", 0, 1).convert("RGB")


def capture(hwnd, flags=_win.PW_RENDERFULLCONTENT):
    """Снимок всего окна hwnd (рамка и заголовок входят)."""
    r = wt.RECT()
    user32.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        raise CaptureError("у окна пустой прямоугольник %dx%d" % (w, h))
    bi = _win.BITMAPINFOHEADER()
    bi.biSize = ctypes.sizeof(bi)
    bi.biWidth, bi.biHeight, bi.biPlanes, bi.biBitCount = w, -h, 1, 32
    dc = gdi32.CreateCompatibleDC(None)
    bits = ctypes.c_void_p()
    bm = gdi32.CreateDIBSection(dc, ctypes.byref(bi), 0,
                                ctypes.byref(bits), None, 0)
    if not bm:
        gdi32.DeleteDC(dc)
        raise CaptureError("CreateDIBSection не создал bitmap %dx%d" % (w, h))
    old = gdi32.SelectObject(dc, bm)
    ok = user32.PrintWindow(hwnd, dc, flags)
    data = ctypes.string_at(bits.value, w * h * 4) if ok else b""
    gdi32.SelectObject(dc, old)
    gdi32.DeleteObject(bm)
    gdi32.DeleteDC(dc)
    if not ok:
        raise CaptureError("PrintWindow вернул 0 (окно не поддерживает?)")
    return Image(w, h, data)
