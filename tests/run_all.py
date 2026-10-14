# -*- coding: utf-8 -*-
"""Прогнать все проверки набора; код возврата 0 — всё прошло."""
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    bad = 0
    for name in ("test_notepad.py", "test_tree.py"):
        r = subprocess.run([sys.executable, os.path.join(HERE, name)])
        bad += r.returncode != 0
    r = subprocess.run([sys.executable,
                        os.path.join(os.path.dirname(HERE), "tools",
                                     "check_docs.py")])
    bad += r.returncode != 0
    print("\nИТОГО: %s" % ("всё прошло" if not bad else "упало: %d" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
