$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

python -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "Could not update pip." }
python -m pip install -e ".[build]"
if ($LASTEXITCODE -ne 0) { throw "Could not install build dependencies." }
python -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name sNote `
    --icon "src/snote/resources/snote.ico" `
    --paths "src" `
    --add-data "src/snote/resources;snote/resources" `
    "scripts/snote_launcher.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller build failed." }

$ReleaseDir = Join-Path $ProjectRoot "release"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
$Version = python -c "import sys; sys.path.insert(0, 'src'); import snote; print(snote.__version__)"
$ZipPath = Join-Path $ReleaseDir "sNote-$Version-windows-x64.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
Compress-Archive -Path "dist/sNote/*" -DestinationPath $ZipPath
Write-Host "Created $ZipPath"
