@echo off
echo.
echo ================================================================
echo         REGENERATE QR CODES FOR VERIFIED WORKERS
echo ================================================================
echo.
echo This script will generate QR codes for all verified workers
echo who don't have one yet.
echo.
echo Press Ctrl+C to cancel, or
pause

cd /d "%~dp0"
python migrations/regenerate_qr_codes.py

echo.
echo ================================================================
echo                    MIGRATION COMPLETE
echo ================================================================
echo.
echo Now restart your frontend and check:
echo  1. Worker Dashboard - Worker ID should be visible
echo  2. Worker Dashboard - QR Code tab should show the QR code
echo  3. Police Dashboard - QR code visible in worker details
echo.
pause

