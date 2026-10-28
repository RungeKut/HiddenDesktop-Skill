---
name: hidden-desktop
description: "Оконные программы Windows на СКРЫТОМ рабочем столе (CreateDesktop): окна не видны человеку, его фокус, мышь и клавиатура не трогаются. Снимок окна (PrintWindow), управление сообщениями (текст, кнопки, списки, деревья, прокрутка) без реального ввода. Используй ВСЕГДА, когда нужно снять скриншот или проверить окно GUI-программы, автоматизировать Win32/MFC/WinForms-программу в фоне, «не мешать работе», а также при словах UI automation, CreateDesktop, PrintWindow, hwnd, WM_*, SendMessage, PostMessage, SysTreeView32, ошибка 740."
---

# Скрытый рабочий стол

Корень набора — папка, из которой прочитан этот файл (клон
`RungeKut/HiddenDesktop-Kit`); соседние скиллы — рядом с ней. Библиотека `hdkit`, утилита
`tools/hd.py`, база `knowledge/` (карта и поиск по симптому — `INDEX.md`).

**Первым делом:** `git -C <корень> pull --rebase`; владельцу — ещё
`gh pr list` (40-02).

```python
import sys; sys.path.insert(0, r"<корень>")
from hdkit import HiddenDesktop, controls
with HiddenDesktop() as d:
    d.launch([r"C:\Windows\System32\notepad.exe"])
    w = d.wait_window(cls="Notepad", timeout=20)
    controls.set_text(w.find(cls="Edit"), "привет")
    w.capture().save("shot.png")
```

Одной командой: `python <корень>/tools/hd.py run --class Notepad --shot out.png --dump -- notepad.exe`.

**Порядок:** запуск → `wait_window` (нет окна — `d.dialogs()`) →
`w.dump()` → одно действие `controls.*` → проверка состоянием или снимком →
штатное закрытие. Вызовы — 10-03, снимки — 20-01, новая программа — 20-02.

## Железные правила

1. Только `with HiddenDesktop()` — иначе остаются невидимые процессы.
2. Никакого реального ввода (`SendInput`, `pyautogui`,
   `SetForegroundWindow`) — только сообщения окнам; мышь — только Post (30-01, 30-02).
3. Дескрипторы — только через `hdkit` (30-03).
4. Скрипт — под тайм-аутом, вывод в файл; после аварии — `taskkill` (30-07).
5. Данные человека — на копии; после действия — `d.dialogs()`. UAC (740) не
   обходить, пароли не вводить.
6. Сообщение не гарантирует действия: проверять состоянием или снимком.

## Правка набора

Нашли грабли — запись по `knowledge/00_ПРАВИЛА.md`, строки в `INDEX.md` и
`CHANGELOG.md`, `python tools/check_docs.py --project "<папка проекта>"`,
`git diff`, коммит, push. В набор — ничего о рабочих проектах: ни названий,
ни путей, ни снимков их окон (40-02).
