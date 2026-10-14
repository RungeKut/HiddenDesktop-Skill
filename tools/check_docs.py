# -*- coding: utf-8 -*-
r"""Проверка целостности базы знаний HiddenDesktop-Kit.

  * у каждого файла базы шапка YAML с id, title, status;
  * каждый файл есть в INDEX.md и наоборот;
  * id уникальны и совпадают с именем файла;
  * status: проверено требует verified и applies_to;
  * относительные ссылки ведут на существующие файлы;
  * стоп-слова из tools/stoplist.txt (локальный файл, не в git) не
    встречаются в файлах набора.

    python tools/check_docs.py
"""
import io
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KNOWLEDGE = os.path.join(ROOT, "knowledge")
INDEX = os.path.join(KNOWLEDGE, "INDEX.md")
STOP = os.path.join(ROOT, "tools", "stoplist.txt")
TEXT = (".md", ".py", ".ps1", ".txt", ".bat")
VALID = ("проверено", "не проверено", "устарело", "действует")


def read(p):
    return io.open(p, encoding="utf-8").read()


def header(text):
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).splitlines():
        k, _, v = line.partition(":")
        out[k.strip()] = v.strip().strip('"')
    return out


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    errs = []
    files = []
    for dp, _d, fn in os.walk(KNOWLEDGE):
        for f in fn:
            if f.endswith(".md") and f not in ("INDEX.md", "00_ПРАВИЛА.md"):
                files.append(os.path.join(dp, f))
    ids = {}
    for p in sorted(files):
        rel = os.path.relpath(p, KNOWLEDGE).replace("\\", "/")
        h = header(read(p))
        if h is None:
            errs.append("%s: нет шапки" % rel)
            continue
        for k in ("id", "title", "status"):
            if not h.get(k):
                errs.append("%s: нет поля %s" % (rel, k))
        if h.get("status") and h["status"] not in VALID:
            errs.append("%s: status %r" % (rel, h["status"]))
        if h.get("status") == "проверено" and not (
                h.get("verified") and h.get("applies_to")):
            errs.append("%s: проверено без verified/applies_to" % rel)
        if h.get("id") and not os.path.basename(p).startswith(h["id"]):
            errs.append("%s: id %s не совпадает с именем" % (rel, h["id"]))
        if h.get("id") in ids:
            errs.append("%s: дубликат id %s" % (rel, h["id"]))
        ids[h.get("id")] = rel
        for link in re.findall(r"\]\(([^)#]+\.md)(?:#[^)]*)?\)", read(p)):
            if not os.path.exists(os.path.normpath(
                    os.path.join(os.path.dirname(p), link))):
                errs.append("%s: битая ссылка %s" % (rel, link))
    idx = read(INDEX)
    listed = set(re.findall(r"\]\(([^)]+\.md)\)", idx))
    have = {os.path.relpath(p, KNOWLEDGE).replace("\\", "/") for p in files}
    for x in sorted(have - listed):
        errs.append("INDEX.md: нет строки для %s" % x)
    for x in sorted(listed - have - {"00_ПРАВИЛА.md"}):
        errs.append("INDEX.md: файла нет: %s" % x)
    if os.path.exists(STOP):
        words = [w.strip().lower() for w in read(STOP).splitlines()
                 if w.strip() and not w.startswith("#")]
        for dp, dn, fn in os.walk(ROOT):
            dn[:] = [d for d in dn if d not in (".git", "vyvod", "__pycache__")]
            for f in fn:
                if f.endswith(TEXT) and f != "stoplist.txt":
                    t = read(os.path.join(dp, f)).lower()
                    for w in words:
                        if w in t:
                            errs.append("%s: стоп-слово %r"
                                        % (os.path.relpath(os.path.join(dp, f), ROOT), w))
    else:
        print("ВНИМАНИЕ: нет tools/stoplist.txt — проверка стоп-слов пропущена")
    for e in errs:
        print("ОШИБКА  " + e)
    print("файлов базы: %d; ошибок: %d" % (len(files), len(errs)))
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
