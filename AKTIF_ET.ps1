# Usage: . .\AKTIF_ET.ps1
$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$projectGit = 'C:\Program Files\Git\cmd'
$projectNode = Join-Path $PSScriptRoot '.tools\node'
foreach ($projectDirectory in @($projectGit, $projectNode)) {
    if ((Test-Path -LiteralPath $projectDirectory) -and (($env:Path -split ';') -notcontains $projectDirectory)) {
        $env:Path = $projectDirectory + [IO.Path]::PathSeparator + $env:Path
    }
}
if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot '.venv\Scripts\python.exe'))) {
    throw 'Once KURULUM.cmd dosyasini calistirin.'
}
. (Join-Path $PSScriptRoot '.venv\Scripts\Activate.ps1')
