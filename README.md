# HiddenDesktop-Kit

Работа с оконными программами Windows на **скрытом рабочем столе**: человек
продолжает работать, а ИИ (или скрипт) запускает программу невидимо, снимает
её окна и управляет ими, не перехватывая ни мышь, ни клавиатуру, ни фокус.

```
HiddenDesktop-Kit/
├── skill/SKILL.md          точка входа для ИИ (подключён как скилл hidden-desktop)
├── hdkit/                  библиотека Python (только стандартная библиотека)
│   ├── desktop.py          HiddenDesktop, Window, Process
│   ├── capture.py          снимок PrintWindow, PNG без Pillow
│   ├── controls.py         управление сообщениями: текст, кнопки, список, дерево, прокрутка
│   └── _win.py             объявления WinAPI с 64-битными типами
├── tools/                  hd.py (запустить-снять-вывести), setup.ps1, check_docs.py
├── examples/               notepad_demo.py, tree_and_combo.py
├── knowledge/              база знаний (INDEX.md — карта)
└── tests/                  test_notepad.py, test_tree.py, run_all.py
```

## Идея
`CreateDesktop` создаёт второй рабочий стол в сессии пользователя. Программа,
запущенная с `STARTUPINFO.lpDesktop` этого стола, рисует окна на нём; человек
их не видит, его ввод идёт только на его стол. Окно снимается в память
(`PrintWindow`), управляется оконными сообщениями (`SendMessageTimeout`,
`PostMessage`).

## Установка
```powershell
powershell -ExecutionPolicy Bypass -File tools\setup.ps1
```
Прав администратора не требует. Подробно — `knowledge/40_СРЕДА/40-01`.

## Пример
```python
from hdkit import HiddenDesktop, controls
with HiddenDesktop() as d:
    d.launch([r"C:\Windows\System32\notepad.exe"])
    w = d.wait_window(cls="Notepad")
    controls.set_text(w.find(cls="Edit"), "привет")
    w.capture().save("shot.png")
```

Или одной командой: `python tools/hd.py run --shot out.png -- notepad.exe`.

## Проверено
Блокнот, msinfo32 (дерево, чужая память, двойной клик), IAR Visual State
Designer (MDI, панели BCG, выпадающий список зума, открытие диаграммы).
Windows 10 Pro 10.0.19045, Python 3.13 64-bit. Не проверено: GPU-окна
(DirectX/Chromium), программы с правами администратора.

## Лицензия
MIT.
