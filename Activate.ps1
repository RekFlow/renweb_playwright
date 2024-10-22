# Log the current directory
Write-Host "Current directory: $(Get-Location)"

# Attempt to change directory
try {
    Set-Location "I:\My Drive\Big Horse Solutions\Companies\Big Horse Strategy\AI\Education App\renweb_playwright"
    Write-Host "Successfully changed directory to: $(Get-Location)"
}
catch {
    Write-Host "Error changing directory: $_"
}

# Log the new current directory
Write-Host "New current directory: $(Get-Location)"
