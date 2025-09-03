Write-Host "Starting CPU Monitor & App Restarter..." -ForegroundColor Green
Write-Host ""
Write-Host "Make sure you have Python installed and dependencies are installed." -ForegroundColor Yellow
Write-Host "If you haven't installed dependencies yet, run: pip install -r requirements.txt" -ForegroundColor Yellow
Write-Host ""

try {
    python cpu_monitor.py
} catch {
    Write-Host "Error running the application. Make sure Python is installed and in your PATH." -ForegroundColor Red
    Write-Host "Press any key to continue..."
    $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
}
