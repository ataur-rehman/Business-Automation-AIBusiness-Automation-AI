# Quick Deployment Check
Write-Host "Preparing Deployment Package..." -ForegroundColor Cyan
Write-Host ""

# Check required files
Write-Host "Verifying required files..." -ForegroundColor Yellow
$required = @(
    "requirements-backend.txt",
    "requirements-frontend.txt",
    "Procfile",
    "railway.json",
    "runtime.txt",
    "README.md",
    ".gitignore",
    "backend/main_minimal.py",
    "ui/shopify_platform.py"
)

$ok = $true
foreach ($f in $required) {
    if (Test-Path $f) {
        Write-Host "  OK: $f" -ForegroundColor Green
    } else {
        Write-Host "  MISSING: $f" -ForegroundColor Red
        $ok = $false
    }
}

Write-Host ""
if ($ok) {
    Write-Host "READY TO DEPLOY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next: Push to GitHub and deploy to Railway + Streamlit" -ForegroundColor Cyan
    Write-Host "See: DEPLOYMENT_CHECKLIST.md" -ForegroundColor Cyan
} else {
    Write-Host "Fix missing files first" -ForegroundColor Red
}
