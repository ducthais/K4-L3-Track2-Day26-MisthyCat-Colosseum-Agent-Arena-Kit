param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$ArgsList
)

$venvPy = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $venvPy) {
    & $venvPy (Join-Path $PSScriptRoot "make.py") @ArgsList
} else {
    python (Join-Path $PSScriptRoot "make.py") @ArgsList
}
