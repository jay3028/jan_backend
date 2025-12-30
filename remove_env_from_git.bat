@echo off
echo ========================================
echo Removing .env from Git Tracking
echo ========================================
echo.

echo Step 1: Removing .env from Git (keeping local file)...
git rm --cached .env

if %ERRORLEVEL% EQU 0 (
    echo [OK] .env removed from Git tracking
    echo.
    
    echo Step 2: Committing the change...
    git commit -m "Remove .env from version control - security fix"
    
    if %ERRORLEVEL% EQU 0 (
        echo [OK] Changes committed
        echo.
        
        echo Step 3: Ready to push!
        echo Run this command to push:
        echo   git push origin main
        echo.
        
        echo ========================================
        echo IMPORTANT - ROTATE YOUR AWS CREDENTIALS!
        echo ========================================
        echo.
        echo Your AWS credentials were exposed.
        echo Please IMMEDIATELY:
        echo   1. Go to AWS IAM Console
        echo   2. Delete the exposed access keys
        echo   3. Create new access keys
        echo   4. Update your local .env file
        echo.
        echo Press any key to exit...
        pause >nul
    ) else (
        echo [ERROR] Failed to commit changes
        echo.
        pause
    )
) else (
    echo.
    echo [INFO] .env might already be removed or not found
    echo Checking Git status...
    echo.
    git status
    echo.
    echo If .env is not listed above, you're good!
    echo.
    pause
)

