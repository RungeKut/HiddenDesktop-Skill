# -*- coding: utf-8 -*-
"""Объявления WinAPI для hdkit: типы аргументов заданы явно.

Без argtypes/restype ctypes считает дескрипторы 32-битными и молча
обрезает 64-битные значения (HWND, HTREEITEM, указатели): сообщение уходит
не тому окну или не тому узлу дерева. Поэтому все вызовы hdkit идут через
эти объявления, а не через голый ctypes.windll.
"""
import ctypes
import ctypes.wintypes as wt

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
gdi32 = ctypes.WinDLL("gdi32", use_last_error=True)

HANDLE = ctypes.c_void_p
HWND = ctypes.c_void_p
SIZE_T = ctypes.c_size_t
LRESULT = ctypes.c_ssize_t

WNDENUMPROC = ctypes.WINFUNCTYPE(wt.BOOL, HWND, wt.LPARAM)

GENERIC_ALL = 0x10000000
PROCESS_ALL_FOR_MEMORY = 0x0038 | 0x0400 | 0x1000
SMTO_ABORTIFHUNG = 0x0002
SMTO_BLOCK = 0x0001
WM_GETTEXT = 0x000D
WM_GETTEXTLENGTH = 0x000E
WM_SETTEXT = 0x000C
PW_RENDERFULLCONTENT = 0x00000002
SWP_NOZORDER = 0x0004
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SW_SHOWNORMAL = 1
SW_RESTORE = 9
SM_CXMAXTRACK = 59
SM_CYMAXTRACK = 60


class STARTUPINFOW(ctypes.Structure):
    _fields_ = [("cb", wt.DWORD), ("lpReserved", wt.LPWSTR),
                ("lpDesktop", wt.LPWSTR), ("lpTitle", wt.LPWSTR),
                ("dwX", wt.DWORD), ("dwY", wt.DWORD),
                ("dwXSize", wt.DWORD), ("dwYSize", wt.DWORD),
                ("dwXCountChars", wt.DWORD), ("dwYCountChars", wt.DWORD),
                ("dwFillAttribute", wt.DWORD), ("dwFlags", wt.DWORD),
                ("wShowWindow", wt.WORD), ("cbReserved2", wt.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", HANDLE),
                ("hStdOutput", HANDLE), ("hStdError", HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", HANDLE), ("hThread", HANDLE),
                ("dwProcessId", wt.DWORD), ("dwThreadId", wt.DWORD)]


class SCROLLINFO(ctypes.Structure):
    _fields_ = [("cbSize", wt.UINT), ("fMask", wt.UINT),
                ("nMin", ctypes.c_int), ("nMax", ctypes.c_int),
                ("nPage", wt.UINT), ("nPos", ctypes.c_int),
                ("nTrackPos", ctypes.c_int)]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [("biSize", wt.DWORD), ("biWidth", ctypes.c_long),
                ("biHeight", ctypes.c_long), ("biPlanes", wt.WORD),
                ("biBitCount", wt.WORD), ("biCompression", wt.DWORD),
                ("biSizeImage", wt.DWORD), ("biXPelsPerMeter", ctypes.c_long),
                ("biYPelsPerMeter", ctypes.c_long), ("biClrUsed", wt.DWORD),
                ("biClrImportant", wt.DWORD)]


def _sig(fn, res, *args):
    fn.restype = res
    fn.argtypes = list(args)


_sig(user32.CreateDesktopW, HANDLE, wt.LPCWSTR, wt.LPCWSTR, ctypes.c_void_p,
     wt.DWORD, wt.DWORD, ctypes.c_void_p)
_sig(user32.CloseDesktop, wt.BOOL, HANDLE)
_sig(user32.EnumDesktopWindows, wt.BOOL, HANDLE, WNDENUMPROC, wt.LPARAM)
_sig(user32.EnumChildWindows, wt.BOOL, HWND, WNDENUMPROC, wt.LPARAM)
_sig(user32.GetClassNameW, ctypes.c_int, HWND, wt.LPWSTR, ctypes.c_int)
_sig(user32.GetWindowRect, wt.BOOL, HWND, ctypes.POINTER(wt.RECT))
_sig(user32.GetClientRect, wt.BOOL, HWND, ctypes.POINTER(wt.RECT))
_sig(user32.IsWindow, wt.BOOL, HWND)
_sig(user32.IsWindowVisible, wt.BOOL, HWND)
_sig(user32.IsZoomed, wt.BOOL, HWND)
_sig(user32.GetWindowThreadProcessId, wt.DWORD, HWND,
     ctypes.POINTER(wt.DWORD))
_sig(user32.GetParent, HWND, HWND)
_sig(user32.GetWindow, HWND, HWND, wt.UINT)
_sig(user32.GetDlgCtrlID, ctypes.c_int, HWND)
_sig(user32.SetWindowPos, wt.BOOL, HWND, HWND, ctypes.c_int, ctypes.c_int,
     ctypes.c_int, ctypes.c_int, wt.UINT)
_sig(user32.ShowWindow, wt.BOOL, HWND, ctypes.c_int)
_sig(user32.PrintWindow, wt.BOOL, HWND, HANDLE, wt.UINT)
_sig(user32.PostMessageW, wt.BOOL, HWND, wt.UINT, wt.WPARAM, wt.LPARAM)
_sig(user32.SendMessageTimeoutW, LRESULT, HWND, wt.UINT, wt.WPARAM,
     wt.LPARAM, wt.UINT, wt.UINT, ctypes.POINTER(ctypes.c_size_t))
_sig(user32.RedrawWindow, wt.BOOL, HWND, ctypes.c_void_p, ctypes.c_void_p,
     wt.UINT)
_sig(user32.GetScrollInfo, wt.BOOL, HWND, ctypes.c_int,
     ctypes.POINTER(SCROLLINFO))
_sig(user32.GetSystemMetrics, ctypes.c_int, ctypes.c_int)
_sig(user32.GetForegroundWindow, HWND)
_sig(user32.EnumWindows, wt.BOOL, WNDENUMPROC, wt.LPARAM)

_sig(kernel32.CreateProcessW, wt.BOOL, wt.LPCWSTR, wt.LPWSTR,
     ctypes.c_void_p, ctypes.c_void_p, wt.BOOL, wt.DWORD, ctypes.c_void_p,
     wt.LPCWSTR, ctypes.POINTER(STARTUPINFOW),
     ctypes.POINTER(PROCESS_INFORMATION))
_sig(kernel32.TerminateProcess, wt.BOOL, HANDLE, wt.UINT)
_sig(kernel32.WaitForSingleObject, wt.DWORD, HANDLE, wt.DWORD)
_sig(kernel32.GetExitCodeProcess, wt.BOOL, HANDLE, ctypes.POINTER(wt.DWORD))
_sig(kernel32.OpenProcess, HANDLE, wt.DWORD, wt.BOOL, wt.DWORD)
_sig(kernel32.CloseHandle, wt.BOOL, HANDLE)
_sig(kernel32.VirtualAllocEx, ctypes.c_void_p, HANDLE, ctypes.c_void_p,
     SIZE_T, wt.DWORD, wt.DWORD)
_sig(kernel32.VirtualFreeEx, wt.BOOL, HANDLE, ctypes.c_void_p, SIZE_T,
     wt.DWORD)
_sig(kernel32.WriteProcessMemory, wt.BOOL, HANDLE, ctypes.c_void_p,
     ctypes.c_void_p, SIZE_T, ctypes.POINTER(SIZE_T))
_sig(kernel32.ReadProcessMemory, wt.BOOL, HANDLE, ctypes.c_void_p,
     ctypes.c_void_p, SIZE_T, ctypes.POINTER(SIZE_T))
_sig(kernel32.GetCurrentProcessId, wt.DWORD)

_sig(gdi32.CreateCompatibleDC, HANDLE, HANDLE)
_sig(gdi32.CreateDIBSection, HANDLE, HANDLE, ctypes.c_void_p, wt.UINT,
     ctypes.POINTER(ctypes.c_void_p), HANDLE, wt.DWORD)
_sig(gdi32.SelectObject, HANDLE, HANDLE, HANDLE)
_sig(gdi32.DeleteObject, wt.BOOL, HANDLE)
_sig(gdi32.DeleteDC, wt.BOOL, HANDLE)
