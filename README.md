# HiddenDesktop-Kit

Работа с оконными программами Windows на **скрытом рабочем столе**: человек
продолжает работать, а ИИ (или скрипт) запускает программу невидимо, снимает
её окна и управляет ими, не перехватывая ни мышь, ни клавиатуру, ни фокус.

```
hidden-desktop/             клон лежит прямо в папке скиллов агента
├── SKILL.md                точка входа для ИИ (скилл hidden-desktop)
├── hdkit/                  библиотека Python (только стандартная библиотека)
│   ├── desktop.py          HiddenDesktop, Window, Process
│   ├── capture.py          снимок PrintWindow, PNG без Pillow
│   ├── controls.py         управление сообщениями: текст, кнопки, список, дерево, прокрутка
│   └── _win.py             объявления WinAPI с 64-битными типами
├── tools/                  hd.py (запустить-снять-вывести), check_docs.py, хук commit-msg
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
git clone https://github.com/RungeKut/HiddenDesktop-Kit.git "$env:USERPROFILE\.claude\skills\hidden-desktop"
```
Установщика, переменных окружения и junction нет: репозиторий и есть папка
скилла, обновление — `git pull`. Настройка клона (хук, автор, стоп-лист) —
`knowledge/40_СРЕДА/40-01`.

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

## Работа с нескольких машин

В начале — `git pull --rebase`; после каждой правки набора — `git diff`,
`python tools/check_docs.py --project "<папка проекта>"`, коммит, `git
push`. Без права записи правка уходит pull request'ом из своего форка;
владелец разбирает открытые PR при каждом pull (`gh pr list`). Порядок —
`knowledge/40_СРЕДА/40-02`. **В набор не попадает ничего о рабочих
проектах** — ни в файлы, ни в текст коммита, ни снимки окон их программ.
Приметы — в `tools/stoplist.txt`: он локальный (`.gitignore`), заводится
при клонировании. Автор коммитов задаётся для клона публичным именем.

## Лицензия
MIT.
