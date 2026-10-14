# Установка HiddenDesktop-Kit на машине.
#
#     powershell -ExecutionPolicy Bypass -File tools\setup.ps1
#
# 1. junction ~\.claude\skills\hidden-desktop и ~\.kimi-code\skills\hidden-desktop
#    -> <корень>\skill (скилл виден Claude Code и Kimi Code);
# 2. переменная HDKIT_HOME в профиле пользователя;
# 3. проверка Python 64-bit и прогон tests\test_notepad.py (скрытый стол).
#
# Прав администратора не требует. Файл в UTF-8 с BOM: без него Windows
# PowerShell 5.1 читает кириллицу в ANSI.

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Write-Host "Корень набора: $root"
if (-not (Test-Path (Join-Path $root "hdkit"))) {
    throw "В $root нет папки hdkit — скрипт запущен не из репозитория."
}

$target = Join-Path $root "skill"
foreach ($skills in @(
    (Join-Path $env:USERPROFILE ".claude\skills"),
    (Join-Path $env:USERPROFILE ".kimi-code\skills"))) {
    if (-not (Test-Path $skills)) {
        New-Item -ItemType Directory -Path $skills -Force | Out-Null
    }
    $link = Join-Path $skills "hidden-desktop"
    if (Test-Path $link) {
        $item = Get-Item $link -Force
        $current = $null
        if ($item.LinkType) { $current = $item.Target | Select-Object -First 1 }
        if ($current -eq $target) {
            Write-Host "OK   junction уже указывает куда нужно: $link"
            continue
        }
        if (-not $item.LinkType) {
            throw "$link — обычная папка, а не ссылка. Уберите её вручную и повторите."
        }
        cmd /c rmdir "$link" | Out-Null
    }
    cmd /c mklink /J "$link" "$target" | Out-Null
    Write-Host "OK   junction создан: $link -> $target"
}

[Environment]::SetEnvironmentVariable("HDKIT_HOME", $root, "User")
$env:HDKIT_HOME = $root
Write-Host "OK   HDKIT_HOME = $root"

$py = $null
foreach ($c in @(
    "$env:LOCALAPPDATA\Programs\Python\Python313\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
    "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe")) {
    if (Test-Path $c) { $py = $c; break }
}
if (-not $py) {
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd) { $py = $cmd.Source }
}
if (-not $py) {
    Write-Host "НЕТ  Python не найден: winget install --id Python.Python.3.13 --scope user --silent"
    exit 1
}
$arch = & $py -c "import platform; print(platform.architecture()[0])"
if ($arch -ne "64bit") { Write-Host "НЕТ  нужен Python 64bit, найден $arch"; exit 1 }
Write-Host "OK   Python: $py"

& $py (Join-Path $root "tests\test_notepad.py")
if ($LASTEXITCODE -ne 0) {
    Write-Host "НЕТ  проверка на скрытом столе не прошла — см. вывод выше"
    exit 1
}
Write-Host ""
Write-Host "Готово. Перезапустите Claude Code и Kimi Code, чтобы они увидели скилл."
