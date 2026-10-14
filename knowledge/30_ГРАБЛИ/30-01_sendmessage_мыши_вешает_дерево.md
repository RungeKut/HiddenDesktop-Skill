---
id: 30-01
title: SendMessage с WM_LBUTTONDOWN на дерево вешает и дерево, и скрипт: клики посылать только PostMessage
tags: [SendMessage, DragDetect, дерево, зависание, мышь]
applies_to: Windows 10 Pro 10.0.19045, Python 3.13 64-bit
status: проверено
verified: 2026-10-14 — зависание воспроизведено (скрипт убит по тайм-ауту), затем PostMessage сработал
source: эксперимент в Designer (дерево проекта), msinfo32
---

# Клик по дереву

## Что происходит
`SendMessage(tree, WM_LBUTTONDOWN, …)` не возвращается: дерево на нажатие
входит в цикл DragDetect и ждёт настоящее движение/отпускание мыши, которого
нет на скрытом столе. Скрипт висит до тайм-аута, программа — тоже.

## Как правильно
`controls.click(tree, x, y, double=True)` — все сообщения PostMessage с
паузами 0,15 с (DOWN, UP, DBLCLK, UP). Перед этим узел можно выделить
`controls.tree_select` (TVM_SELECTITEM — не мышь, безопасно).

## Как неправильно
```python
SendMessage(tree, WM_LBUTTONDOWN, 1, lparam)   # зависнет
```
Нажатие Enter на дереве (WM_KEYDOWN VK_RETURN) в проверенной программе
узел НЕ открывало — для «открыть» нужен двойной клик.

## Чем подтверждено
Designer: после замены SendMessage на PostMessage двойной клик открыл
диаграмму региона; msinfo32: двойной клик переключил раскрытие узла
(tests/test_tree.py).
