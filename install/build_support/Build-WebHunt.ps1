$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Push-Location $root
try {
    $python = Join-Path $root '.venv\Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python -PathType Leaf)) {
        & python -m venv .venv
        if ($LASTEXITCODE -ne 0) { throw 'Could not prepare Python build environment.' }
    }
    & $python -m pip install -q -r build_support\requirements-dev.txt
    if ($LASTEXITCODE -ne 0) { throw 'Could not install build dependencies.' }

    & $python -m PyInstaller --noconfirm --clean --distpath dist\app build_support\WebHunt__.spec
    if ($LASTEXITCODE -ne 0) { throw 'Application build failed.' }
    & $python -m PyInstaller --noconfirm --clean --distpath dist\install build_support\WebHunt__Setup.spec
    if ($LASTEXITCODE -ne 0) { throw 'Installer build failed.' }

    $built = Join-Path $root 'dist\install\WebHunt__Setup.exe'
    $destination = Join-Path $root 'Setup\WebHunt__Setup.exe'
    if (-not (Test-Path -LiteralPath $built -PathType Leaf)) { throw 'Installer output is missing.' }
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $destination) | Out-Null
    Copy-Item -LiteralPath $built -Destination $destination -Force
    if ((Get-Item -LiteralPath $destination).Length -lt 1MB) { throw 'Installer output is unexpectedly small.' }
    $oldRootInstaller = Join-Path $root 'WebHunt__Setup.exe'
    if (Test-Path -LiteralPath $oldRootInstaller) { Remove-Item -LiteralPath $oldRootInstaller -Force }

    foreach ($relative in @('build','dist','appstart','uninstaller')) {
        $target = [IO.Path]::GetFullPath((Join-Path $root $relative))
        if (-not $target.StartsWith($root + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove path outside project: $target"
        }
        if (Test-Path -LiteralPath $target) { Remove-Item -LiteralPath $target -Recurse -Force }
    }
    Write-Host "Done: $destination"
} finally {
    Pop-Location
}
