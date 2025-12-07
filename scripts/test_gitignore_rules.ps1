# Test .gitignore rules
# Verify which files should be ignored and which should be tracked

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "GitIgnore Rules Verification Test" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test cases: files that should be tracked or ignored
$testFiles = @(
    # Files that should be tracked (English scripts)
    @{ File = "deploy/fix_and_deploy_frontend_complete.sh"; ShouldIgnore = $false; Reason = "English deployment script" },
    @{ File = "deploy/check_and_fix_frontend.sh"; ShouldIgnore = $false; Reason = "English check script" },
    @{ File = "deploy/deploy_frontend_complete.sh"; ShouldIgnore = $false; Reason = "English deployment script" },
    @{ File = "deploy/docker-compose.yaml"; ShouldIgnore = $false; Reason = "Configuration file" },
    @{ File = "deploy/repo_config.sh"; ShouldIgnore = $false; Reason = "Explicitly preserved script" },
    
    # Files that should be ignored (Chinese scripts)
    @{ File = "deploy/修复構建錯誤並部署.sh"; ShouldIgnore = $true; Reason = "Chinese fix script" },
    @{ File = "deploy/一键修复.sh"; ShouldIgnore = $true; Reason = "Chinese one-click script" },
    @{ File = "deploy/全自动修复.sh"; ShouldIgnore = $true; Reason = "Chinese auto script" },
    @{ File = "修复前端.sh"; ShouldIgnore = $true; Reason = "Root directory Chinese script" },
    
    # Files that should be ignored (temp and sensitive files)
    @{ File = ".env"; ShouldIgnore = $true; Reason = "Environment variable file" },
    @{ File = "node_modules/"; ShouldIgnore = $true; Reason = "Node modules" },
    @{ File = ".venv/"; ShouldIgnore = $true; Reason = "Python virtual environment" },
    @{ File = "app.log"; ShouldIgnore = $true; Reason = "Log file" },
    @{ File = "sessions/"; ShouldIgnore = $true; Reason = "Session files" }
)

$passed = 0
$failed = 0
$results = @()

foreach ($test in $testFiles) {
    $result = git check-ignore -v $test.File 2>&1
    $isIgnored = $result -match "\.gitignore"
    
    $testResult = @{
        File = $test.File
        ExpectedIgnore = $test.ShouldIgnore
        ActualIgnore = $isIgnored
        Match = ($isIgnored -eq $test.ShouldIgnore)
        Reason = $test.Reason
        GitOutput = $result
    }
    
    $results += $testResult
    
    if ($testResult.Match) {
        Write-Host "PASS" -ForegroundColor Green -NoNewline
        Write-Host " - $($test.File) " -ForegroundColor White -NoNewline
        Write-Host "($($test.Reason))" -ForegroundColor Gray
        $passed++
    } else {
        Write-Host "FAIL" -ForegroundColor Red -NoNewline
        Write-Host " - $($test.File) " -ForegroundColor White -NoNewline
        Write-Host "($($test.Reason))" -ForegroundColor Gray
        if ($test.ShouldIgnore) {
            Write-Host "  Expected: Ignored, Actual: NOT Ignored" -ForegroundColor Yellow
        } else {
            Write-Host "  Expected: NOT Ignored, Actual: Ignored" -ForegroundColor Yellow
            if ($result -match "\.gitignore") {
                Write-Host "  Ignored by rule: $result" -ForegroundColor Red
            }
        }
        $failed++
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Results: $passed Passed, $failed Failed" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host "========================================" -ForegroundColor Cyan

# Show detailed results if there are failures
if ($failed -gt 0) {
    Write-Host ""
    Write-Host "Failed Tests Details:" -ForegroundColor Yellow
    foreach ($result in $results) {
        if (-not $result.Match) {
            Write-Host ""
            Write-Host "File: $($result.File)" -ForegroundColor White
            Write-Host "  Expected: $(if ($result.ExpectedIgnore) { 'IGNORED' } else { 'TRACKED' })" -ForegroundColor Gray
            Write-Host "  Actual: $(if ($result.ActualIgnore) { 'IGNORED' } else { 'TRACKED' })" -ForegroundColor Gray
            if ($result.GitOutput -and $result.GitOutput -match "\.gitignore") {
                Write-Host "  Git Rule: $($result.GitOutput)" -ForegroundColor Red
            }
        }
    }
}

Write-Host ""

if ($failed -gt 0) {
    exit 1
} else {
    Write-Host "All tests passed! .gitignore rules are working correctly." -ForegroundColor Green
}
