# Creates an easy-install source ZIP for machines that may lack Python/PyQt5.
$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot
$VersionSource = Get-Content "src/snote/__init__.py" -Raw
if ($VersionSource -notmatch '__version__\s*=\s*"([^"]+)"') { throw "No sNote version found." }
$Version = $Matches[1]
$ReleaseDir = Join-Path $ProjectRoot "release"
New-Item -ItemType Directory -Force -Path $ReleaseDir | Out-Null
$ZipPath = Join-Path $ReleaseDir "sNote-$Version-source-auto-install.zip"
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
# Explicit allowlist: never package .git, user notes, settings, or build cache.
$Sources = @(
    ".github", "scripts", "src", "tests", ".gitignore", "CHANGELOG.md",
    "CONTRIBUTING.md", "INSTALL_WINDOWS.md", "Install-sNote.cmd", "LICENSE",
    "MANIFEST.in", "pyproject.toml", "README.md", "requirements.txt",
    "run_snote.bat", "SECURITY.md", "Uninstall-sNote.cmd"
)
foreach ($Item in $Sources) { if (-not (Test-Path $Item)) { throw "Missing package file: $Item" } }
Compress-Archive -Path $Sources -DestinationPath $ZipPath -CompressionLevel Optimal
Write-Host "Created $ZipPath"
