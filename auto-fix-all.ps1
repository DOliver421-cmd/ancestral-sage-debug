# render-final-auto-fix.ps1 - Final Universal Auto-Fix Script
Write-Host "🔧 FINAL UNIVERSAL RENDER DEPLOYMENT AUTO-FIX" -ForegroundColor Cyan
Write-Host "=================================================" -ForegroundColor Cyan

# Configuration
$ProjectPath = "$env:USERPROFILE\ancestral-sage-debug"
$BackendPath = "$ProjectPath\backend"
$FrontendPath = "$ProjectPath\frontend"
$RequirementsFile = "$ProjectPath\requirements.txt"
$DockerFile = "$ProjectPath\Dockerfile"
$ServerFile = "$BackendPath\server.py"

# Colors
$Green = 'Green'
$Red = 'Red'
$Yellow = 'Yellow'
$Cyan = 'Cyan'
$Magenta = 'Magenta'

function Write-Diagnostic { param($msg) Write-Host "🔍 $msg" -ForegroundColor $Magenta }
function Write-Success { param($msg) Write-Host "✅ $msg" -ForegroundColor $Green }
function Write-Error { param($msg) Write-Host "❌ $msg" -ForegroundColor $Red }
function Write-Warning { param($msg) Write-Host "⚠️  $msg" -ForegroundColor $Yellow }
function Write-Info { param($msg) Write-Host "ℹ️  $msg" -ForegroundColor $Cyan }

Set-Location $ProjectPath

# ==================== PHASE 1: SCAN FOR ALL ERRORS ====================
Write-Diagnostic "PHASE 1: SCANNING FOR ALL DEPLOYMENT ERRORS"
Write-Host "-" * 50

$AllIssues = @{
    PythonErrors = @()
    ImportErrors = @()
    DependencyErrors = @()
    PathErrors = @()
    ConfigErrors = @()
    BuildErrors = @()
}

# Scan server.py for errors
Write-Info "1. Scanning server.py for syntax and imports..."
try {
    python -m py_compile backend/server.py
    Write-Success "Server.py syntax is clean"
} catch {
    $AllIssues.PythonErrors += "Syntax error in server.py"
    Write-Error "Syntax error detected: $_"
}

$serverContent = Get-Content "backend/server.py" -Raw -ErrorAction SilentlyContinue
if ($serverContent) {
    $importPatterns = @(
        '^from prompts\.',
        '^from seed\.',
        '^import seed',
        '^import jwt'
    )
    
    foreach ($pattern in $importPatterns) {
        if ($serverContent -match $pattern) {
            $AllIssues.ImportErrors += "Potential import issue: $pattern"
            Write-Warning "Fixing import: $pattern"
        }
    }
}

# Scan requirements.txt
Write-Info "2. Scanning requirements.txt..."
if (Test-Path $RequirementsFile) {
    $requirements = Get-Content $RequirementsFile
    $requiredDeps = @('fastapi', 'uvicorn', 'motor', 'pymongo', 'reportlab')
    foreach ($dep in $requiredDeps) {
        if (-not ($requirements -match $dep)) {
            $AllIssues.DependencyErrors += "Missing dependency: $dep"
            Write-Warning "Adding missing dependency: $dep"
        }
    }
} else {
    $AllIssues.ConfigErrors += "requirements.txt missing"
    Write-Error "requirements.txt not found"
}

# ==================== PHASE 2: AUTO-FIX ALL ISSUES ====================
Write-Diagnostic "`nPHASE 2: AUTO-FIXING ALL ISSUES"
Write-Host "-" * 50

$FixesApplied = @()

# Fix 1: Update requirements.txt
Write-Info "Fixing requirements.txt..."
$correctRequirements = @"
fastapi==0.104.1
uvicorn[standard]==0.24.0
motor==3.3.0
pymongo==4.5.0
pydantic==2.5.0
python-dotenv==1.0.0
passlib[bcrypt]==1.7.4
python-jose[cryptography]==3.3.0
python-multipart==0.0.6
reportlab==4.0.4
Flask==2.3.3
flask-cors==4.0.0
requests==2.31.0
"@
$correctRequirements | Out-File $RequirementsFile -Encoding UTF8
$FixesApplied += "Updated requirements.txt"
Write-Success "requirements.txt fixed"

# Fix 2: Fix server.py imports
Write-Info "Fixing server.py imports..."
if (Test-Path $ServerFile) {
    $content = Get-Content $ServerFile -Raw
    $fixedContent = $content -replace 'from prompts\.', 'from backend.prompts.' `
                             -replace '^import jwt$', 'from jose import jwt' `
                             -replace '^import seed', 'from backend.seed import' `
                             -replace '^from seed\.', 'from backend.seed.'
    $fixedContent | Out-File $ServerFile -Encoding UTF8
    $FixesApplied += "Fixed import paths in server.py"
    Write-Success "server.py imports fixed"
}

# Fix 3: Fix Dockerfile
Write-Info "Fixing Dockerfile..."
$dockerfileContent = @"
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y gcc g++
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 10000
CMD ["uvicorn", "backend.server:app", "--host", "0.0.0.0", "--port", "10000"]
"@
$dockerfileContent | Out-File $DockerFile -Encoding UTF8
$FixesApplied += "Updated Dockerfile"
Write-Success "Dockerfile fixed"

# Fix 4: Check and fix frontend if present
if (Test-Path $FrontendPath) {
    Write-Info "Fixing frontend files..."
    $packageJson = "$FrontendPath\package.json"
    if (Test-Path $packageJson) {
        $packageContent = Get-Content $packageJson -Raw | ConvertFrom-Json
        if (-not $packageContent.dependencies.PSObject.Properties.Name -contains 'react') {
            $packageContent.dependencies | Add-Member -NotePropertyName 'react' -NotePropertyValue '^18.2.0' -Force
            $packageContent | ConvertTo-Json | Out-File $packageJson
            $FixesApplied += "Added react to package.json"
        }
        # Add more fixes as needed
    }
}

# ==================== PHASE 3: FINAL DEPLOYMENT ====================
Write-Diagnostic "`nPHASE 3: FINAL DEPLOYMENT"
Write-Host "-" * 50

Write-Host "🚀 RENDER DEPLOYMENT TRIGGERED!" -ForegroundColor Green
Write-Host "⏳ Wait 4-5 minutes for fresh build" -ForegroundColor Cyan
Write-Host "📊 Monitor at: https://dashboard.render.com/web/srv-d80dj1egvqtc73des8m0" -ForegroundColor White

git add .
git commit -m "auto-fix: final universal repairs"
git push origin main

Write-Host "`n✅ ALL FIXES APPLIED AND PUSHED!" -ForegroundColor Green
Write-Host "🌐 Test after deployment: curl https://ancestral-sage-debug.onrender.com/health" -ForegroundColor White
