param(
  [string]$Root = (Resolve-Path (Join-Path $PSScriptRoot ".."))
)

$ErrorActionPreference = 'SilentlyContinue'
$ProgressPreference = 'SilentlyContinue'

Write-Host "Branding rename root: $Root" -ForegroundColor Cyan

$includeExt = @('*.md','*.py','*.toml','*.yaml','*.yml','*.txt','*.ps1','*.bat','*.ini')
$excludePattern = '\\__pycache__\\|\\data\\|\\exports\\|\\reports\\|\\.pytest_cache\\|\\DataGenie_AI\\.egg-info\\'

$files = Get-ChildItem -LiteralPath $Root -Recurse -File -Include $includeExt -Force -ErrorAction SilentlyContinue |
  Where-Object { $_.FullName -notmatch $excludePattern }

# Include env files explicitly
$env1 = Get-Item -LiteralPath (Join-Path $Root '.env') -ErrorAction SilentlyContinue
$env2 = Get-Item -LiteralPath (Join-Path $Root '.env.example') -ErrorAction SilentlyContinue
if ($env1) { $files += $env1 }
if ($env2) { $files += $env2 }

$files = $files | Sort-Object FullName -Unique

$repls = @(
  @{ Old = 'DataGenie AI';   New = 'Autonomous Multi-Agent Business Intelligence System' },
  @{ Old = 'DataGenie 2.0';  New = 'Autonomous Multi-Agent Business Intelligence System' },
  @{ Old = 'DataGenie-AI';   New = 'autonomous-multi-agent-business-intelligence-system' },
  @{ Old = 'DataGenie Team'; New = 'YOUR_NAME' },
  @{ Old = 'DATAGENIE 2.0';  New = 'AUTONOMOUS MULTI-AGENT BUSINESS INTELLIGENCE SYSTEM' },
  @{ Old = 'datagenie-ai';   New = 'autonomous-multi-agent-bi-system' },
  @{ Old = 'sql generator_AI-main'; New = 'autonomous-multi-agent-bi-system' }
)

$changed = 0
foreach ($f in $files) {
  try {
    $content = Get-Content -LiteralPath $f.FullName -Raw -ErrorAction Stop
  } catch {
    Write-Host "Skip (read failed): $($f.FullName)" -ForegroundColor DarkYellow
    continue
  }

  if ($null -eq $content) {
    $content = ""
  }

  $original = $content
  foreach ($r in $repls) {
    $content = $content.Replace($r.Old, $r.New)
  }

  if ($content -ne $original) {
    try {
      Set-Content -LiteralPath $f.FullName -Value $content -Encoding utf8 -ErrorAction Stop
      $changed++
    } catch {
      Write-Host "Skip (write failed): $($f.FullName)" -ForegroundColor DarkYellow
    }
  }
}

Write-Host "Updated $changed file(s)." -ForegroundColor Green
return $changed
