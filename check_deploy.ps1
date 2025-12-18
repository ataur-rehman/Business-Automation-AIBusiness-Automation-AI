# Quick Deploy Script
# Run this before pushing to GitHub

Write-Host "🚀 Preparing Deployment Package..." -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "Checking Python version..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
if ($pythonVersion -match "3.11") {
    Write-Host "✅ Python 3.11 detected: $pythonVersion" -ForegroundColor Green
} else {
    Write-Host "⚠️  Warning: Python $pythonVersion detected. Railway requires Python 3.11" -ForegroundColor Red
    Write-Host "   Update runtime.txt if needed" -ForegroundColor Red
}
Write-Host ""

# Clean cache
Write-Host "Cleaning cache folders..." -ForegroundColor Yellow
Get-ChildItem -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
Get-ChildItem -Recurse -File -Filter "*.pyc" | Remove-Item -Force -ErrorAction SilentlyContinue
Write-Host "✅ Cache cleaned" -ForegroundColor Green
Write-Host ""

# Check .env
Write-Host "Checking environment setup..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "⚠️  .env file found - Make sure it's in .gitignore!" -ForegroundColor Yellow
    $envContent = Get-Content ".env" -Raw
    if ($envContent -match "your_groq_api_key_here") {
        Write-Host "⚠️  Remember to add your actual GROQ_API_KEY in Railway!" -ForegroundColor Yellow
    } else {
        Write-Host "✅ .env configured (don't commit this file!)" -ForegroundColor Green
    }
} else {
    Write-Host "✅ No .env file (good - use .env.example as template)" -ForegroundColor Green
}
Write-Host ""

# Test backend
Write-Host "Testing backend..." -ForegroundColor Yellow
$backendRunning = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -Method Get -TimeoutSec 2 -ErrorAction Stop
    if ($response.status -eq "healthy") {
        Write-Host "✅ Backend running and healthy" -ForegroundColor Green
        $backendRunning = $true
    }
} catch {
    Write-Host "ℹ️  Backend not running (optional for deployment prep)" -ForegroundColor Gray
}
Write-Host ""

# Check required files
Write-Host "Verifying required files..." -ForegroundColor Yellow
$requiredFiles = @(
    "requirements-backend.txt",
    "requirements-frontend.txt",
    "Procfile",
    "railway.json",
    "runtime.txt",
    "README.md",
    ".gitignore",
    ".env.example",
    "backend/main_minimal.py",
    "backend/__init__.py",
    "ui/shopify_platform.py",
    "ui/__init__.py",
    "ui/components/__init__.py",
    ".streamlit/config.toml"
)

$allPresent = $true
foreach ($file in $requiredFiles) {
    if (Test-Path $file) {
        Write-Host "  ✅ $file" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file MISSING!" -ForegroundColor Red
        $allPresent = $false
    }
}
Write-Host ""

# Summary
Write-Host "=======================================" -ForegroundColor Cyan
if ($allPresent) {
    Write-Host "READY TO DEPLOY!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Push to GitHub:" -ForegroundColor White
    Write-Host "   git init" -ForegroundColor Gray
    Write-Host "   git add ." -ForegroundColor Gray
    Write-Host "   git commit -m 'Initial deployment'" -ForegroundColor Gray
    Write-Host "   git push origin main" -ForegroundColor Gray
    Write-Host ""
    Write-Host "2. Deploy to Railway:" -ForegroundColor White
    Write-Host "   https://railway.app - New Project - GitHub" -ForegroundColor Gray
    Write-Host ""
    Write-Host "3. Deploy to Streamlit:" -ForegroundColor White
    Write-Host "   https://streamlit.io/cloud - New app" -ForegroundColor Gray
    Write-Host ""
    Write-Host "4. See DEPLOYMENT_CHECKLIST.md for details" -ForegroundColor White
} else {
    Write-Host "MISSING FILES - Fix issues above" -ForegroundColor Red
}
Write-Host "=======================================" -ForegroundColor Cyan
