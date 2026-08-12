$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
$KujoRuntime = if ($env:KUJO_BIN) { $env:KUJO_BIN } else { Join-Path $Root "..\kujo\target\release\kujo.exe" }
if (-not (Test-Path -PathType Leaf $KujoRuntime)) {
    Write-Error "SiteProbe: Kujo runtime not found. Set KUJO_BIN."
    exit 2
}
if (-not $env:SITEPROBE_PYTHON) { $env:SITEPROBE_PYTHON = (Get-Command python -ErrorAction Stop).Source }
Push-Location $Root
try { & $KujoRuntime run src/main.kujo -- @args; exit $LASTEXITCODE }
finally { Pop-Location }
