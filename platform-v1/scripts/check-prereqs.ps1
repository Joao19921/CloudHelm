$ErrorActionPreference = "SilentlyContinue"

Write-Host "CloudHelm - Verificacao de pre-requisitos" -ForegroundColor Cyan
Write-Host "-----------------------------------------" -ForegroundColor Cyan

function Check-Cmd {
  param(
    [string]$Name,
    [string]$VersionCmd
  )

  $cmd = Get-Command $Name
  if (-not $cmd) {
    Write-Host "[FAIL] $Name nao encontrado no PATH." -ForegroundColor Red
    return $false
  }

  $version = Invoke-Expression $VersionCmd
  Write-Host "[ OK ] $Name encontrado -> $version" -ForegroundColor Green
  return $true
}

$gitOk = Check-Cmd -Name "git" -VersionCmd "git --version"
$dockerOk = Check-Cmd -Name "docker" -VersionCmd "docker --version"
$composeOk = Check-Cmd -Name "docker" -VersionCmd "docker compose version"
$pythonOk = Check-Cmd -Name "python" -VersionCmd "python --version"

Write-Host ""
Write-Host "Portas recomendadas:" -ForegroundColor Cyan
Write-Host "- 8000 (CloudHelm App)"
Write-Host "- 3307 (MySQL local)"

Write-Host ""
if ($gitOk -and $dockerOk -and $composeOk) {
  Write-Host "Ambiente pronto para execucao com Docker." -ForegroundColor Green
  Write-Host "Proximo passo: docker compose up --build"
} else {
  Write-Host "Ambiente incompleto para Docker. Instale os itens em [FAIL]." -ForegroundColor Yellow
}

if ($pythonOk) {
  Write-Host "Python disponivel para modo sem Docker e jobs." -ForegroundColor Green
} else {
  Write-Host "Python ausente: necessario para modo sem Docker e scripts de job." -ForegroundColor Yellow
}
