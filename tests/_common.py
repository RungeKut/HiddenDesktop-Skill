# -*- coding: utf-8 -*-
"""Общее для проверок hdkit: путь к набору, счётчик ошибок."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "tests", "vyvod")
FAILS = []


def start(name):
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    os.makedirs(OUT, exist_ok=True)
    print("== %s" % name)


def ok(cond, what):
    print(("OK    " if cond else "ОШИБКА") + "  " + what)
    if not cond:
        FAILS.append(what)
    return bool(cond)


def finish():
    print("\nитог: %s" % ("все проверки пройдены" if not FAILS
                         else "ОШИБОК: %d" % len(FAILS)))
    return 1 if FAILS else 0
