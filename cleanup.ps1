# ========================================
# Project Cleanup Script - PowerShell
# Google Ads Campaign Simulator
# ========================================

# Navigate to script directory
$scriptPath = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptPath

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   PROJECT CLEANUP - POWERSHELL" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This script will clean:" -ForegroundColor White
Write-Host "  1. Python __pycache__ directories" -ForegroundColor Gray
Write-Host "  2. Duplicate optimized source files" -ForegroundColor Gray
Write-Host "  3. Old backup files" -ForegroundColor Gray
Write-Host "  4. Test/helper files" -ForegroundColor Gray
Write-Host ""
Write-Host "WARNING: This will NOT delete:" -ForegroundColor Yellow
Write-Host "  - backup_pre_optimization/ (safety backup)" -ForegroundColor Gray
Write-Host "  - rollback_optimization.bat (restore script)" -ForegroundColor Gray
Write-Host ""

# Ask for confirmation
$confirmation = Read-Host "Continue? (Y/N)"
if ($confirmation -ne 'Y' -and $confirmation -ne 'y') {
    Write-Host "Cleanup cancelled" -ForegroundColor Red
    exit
}

Write-Host ""

# ========================================
# Phase 1: Clean Python Cache
# ========================================
Write-Host "[1/4] Cleaning Python cache..." -ForegroundColor Yellow
$pycacheDirs = Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory -ErrorAction SilentlyContinue
$pycacheCount = 0
if ($pycacheDirs) {
    $pycacheCount = ($pycacheDirs | Measure-Object).Count
    $pycacheDirs | ForEach-Object { 
        Remove-Item $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
    }
    Write-Host "  Removed $pycacheCount __pycache__ directories" -ForegroundColor Green
} else {
    Write-Host "  No __pycache__ directories found" -ForegroundColor Gray
}
Write-Host ""

# ========================================
# Phase 2: Remove Duplicate Source Files
# ========================================
Write-Host "[2/4] Removing duplicate source files..." -ForegroundColor Yellow
$duplicateFiles = @(
    "main_optimized.py",
    "app\navigation_optimized.py",
    "services\google_ads_client_optimized.py",
    "services\gemini_client_optimized.py",
    "requirements_optimized.txt"
)

$deletedCount = 0
foreach ($file in $duplicateFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  Deleted: $file" -ForegroundColor Gray
        $deletedCount++
    }
}

if ($deletedCount -gt 0) {
    Write-Host "  Removed $deletedCount duplicate files" -ForegroundColor Green
} else {
    Write-Host "  No duplicate files found" -ForegroundColor Gray
}
Write-Host ""

# ========================================
# Phase 3: Remove Old Backup Files
# ========================================
Write-Host "[3/4] Removing old backup files..." -ForegroundColor Yellow
$backupFiles = @(
    "app\admin_dashboard_OLD_BACKUP.py",
    "app\campaign_wizard_backup.py",
    "app\signup_page_old.py"
)

$deletedBackups = 0
foreach ($file in $backupFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  Deleted: $file" -ForegroundColor Gray
        $deletedBackups++
    }
}

if ($deletedBackups -gt 0) {
    Write-Host "  Removed $deletedBackups backup files" -ForegroundColor Green
} else {
    Write-Host "  No backup files found" -ForegroundColor Gray
}
Write-Host ""

# ========================================
# Phase 4: Remove Test/Helper Files
# ========================================
Write-Host "[4/4] Removing test/helper files..." -ForegroundColor Yellow
$testFiles = @(
    "test_logging.py",
    "tokencheck.py",
    "cleanup_docs.bat",
    "apply_optimization.bat"
)

$deletedTests = 0
foreach ($file in $testFiles) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "  Deleted: $file" -ForegroundColor Gray
        $deletedTests++
    }
}

if ($deletedTests -gt 0) {
    Write-Host "  Removed $deletedTests test files" -ForegroundColor Green
} else {
    Write-Host "  No test files found" -ForegroundColor Gray
}
Write-Host ""

# ========================================
# Summary
# ========================================
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "   CLEANUP COMPLETE!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Summary:" -ForegroundColor White
Write-Host "  Python cache: $pycacheCount directories cleaned" -ForegroundColor Gray
Write-Host "  Duplicate files: $deletedCount removed" -ForegroundColor Gray
Write-Host "  Old backups: $deletedBackups removed" -ForegroundColor Gray
Write-Host "  Test files: $deletedTests removed" -ForegroundColor Gray
Write-Host ""
Write-Host "KEPT for safety:" -ForegroundColor Green
Write-Host "  - backup_pre_optimization/ folder" -ForegroundColor Gray
Write-Host "  - rollback_optimization.bat script" -ForegroundColor Gray
Write-Host ""
Write-Host "Your project is now optimized and clean!" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor White
Write-Host "  1. Test the app: streamlit run main.py" -ForegroundColor Gray
Write-Host "  2. Uninstall heavy ML (optional):" -ForegroundColor Gray
Write-Host "     pip uninstall sentence-transformers keybert -y" -ForegroundColor Gray
Write-Host ""

Read-Host "Press Enter to exit"
