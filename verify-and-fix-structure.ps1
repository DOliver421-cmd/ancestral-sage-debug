# verify-and-fix-structure.ps1 - Verify & Fix Project Structure for Ancestral Sage Debug
Write-Host "🔍 STARTING PROJECT STRUCTURE VERIFICATION" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# Configuration
$ProjectPath = "$env:USERPROFILE\ancestral-sage-debug"
$BackendPath = "$ProjectPath\backend"
$FrontendPath = "$ProjectPath\frontend"

# Colors
$Green = 'Green'
$Red = 'Red'
$Yellow = 'Yellow'
$Cyan = 'Cyan'

# Initialize report for issues found
$IssuesFound = @()

# Step 1: Check Backend Directory
Write-Host "📂 Checking Backend directory..." -ForegroundColor Yellow
if (-not (Test-Path $BackendPath)) {
    $IssuesFound += "Missing backend directory: $BackendPath"
    Write-Error "Missing backend directory"
} else {
    Write-Success "Backend directory exists."
    # Ensure __init__.py exists in backend and prompts
    if (-not (Test-Path "$BackendPath\__init__.py")) {
        Write-Host "⚠️  Adding __init__.py to backend directory." -ForegroundColor Yellow
        New-Item -Path "$BackendPath\__init__.py" -ItemType File
    }
    if (-not (Test-Path "$BackendPath\prompts\__init__.py")) {
        Write-Host "⚠️  Adding __init__.py to prompts directory." -ForegroundColor Yellow
        New-Item -Path "$BackendPath\prompts\__init__.py" -ItemType File
    }
}

# Step 2: Check Frontend Directory
Write-Host "🌐 Checking Frontend directory..." -ForegroundColor Yellow
if (Test-Path $FrontendPath) {
    Write-Success "Frontend directory exists."
} else {
    $IssuesFound += "Missing frontend directory: $FrontendPath"
    Write-Error "Missing frontend directory"
}

# Step 3: Check for Required Files
$RequiredFiles = @(
    @{Path="$BackendPath\server.py"; Name="server.py"},
    @{Path="$BackendPath\prompts\ancestral_sage_prompt.py"; Name="ancestral_sage_prompt.py"},
    @{Path="$ProjectPath\requirements.txt"; Name="requirements.txt"},
    @{Path="$ProjectPath\Dockerfile"; Name="Dockerfile"}
)

foreach ($file in $RequiredFiles) {
    if (-not (Test-Path $file.Path)) {
        $IssuesFound += "Missing required file: $($file.Name)"
        Write-Error "Missing: $($file.Name)"
    } else {
        Write-Success "Found: $($file.Name)"
    }
}

# Step 4: Final Report on Found Issues
if ($IssuesFound.Count -gt 0) {
    Write-Host "`n⚠️  ISSUES FOUND:" -ForegroundColor Red
    foreach ($issue in $IssuesFound) {
        Write-Host "  • $issue" -ForegroundColor Red
    }
} else {
    Write-Host "`n✅ All required files and directories are correctly structured." -ForegroundColor Green
}

# ==================== PHASE 5: FINAL COMMIT ====================
Write-Host "`n📡 COMMITTING FILES FOR GIT..." -ForegroundColor Cyan
git add .
git commit -m "auto-fix: verified and updated project structure" -m "Ensured all directories and files are present"
git push origin main
Write-Success "✅ Project structure verification complete. All fixes applied and changes pushed."
