param(
    [Parameter(Mandatory = $true)]
    [string]$Name
)

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$template = Join-Path $root "evals\template"
$runs = Join-Path $root "evals\runs"

$safeName = $Name.Trim() -replace '[^A-Za-z0-9_-]+', '_'
$safeName = $safeName.Trim('_')
if (-not $safeName) {
    throw "Le nom du test ne contient aucun caractere utilisable."
}

$stamp = Get-Date -Format "yyyy-MM-dd_HHmmss"
$destination = Join-Path $runs "${stamp}_${safeName}"

New-Item -ItemType Directory -Path $destination -Force | Out-Null
Copy-Item -Path (Join-Path $template "*") -Destination $destination -Recurse

Write-Host "Essai cree : $destination"
Start-Process explorer.exe -ArgumentList $destination
