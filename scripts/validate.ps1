$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$KujoRuntime = if ($env:KUJO_BIN) { $env:KUJO_BIN } else { Join-Path $Root "..\kujo\target\release\kujo.exe" }
if (-not (Test-Path -PathType Leaf $KujoRuntime)) {
    Write-Error "SiteProbe validation: Kujo runtime not found. Set KUJO_BIN."
    exit 2
}
Push-Location $Root
try { & $KujoRuntime run scripts/validate.kujo -- $KujoRuntime; exit $LASTEXITCODE }
finally { Pop-Location }
