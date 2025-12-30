@echo off
echo.
echo ================================================================
echo         WORKER ACTIVITY TRACKING FEATURE SETUP
echo ================================================================
echo.
echo This script will:
echo   1. Create worker_activities table
echo   2. Populate with realistic dummy data
echo   3. Show you the results
echo.
pause

cd /d "%~dp0"

echo.
echo Running migration...
python migrations/create_worker_activities_table.py

echo.
echo ================================================================
echo                    SETUP COMPLETE!
echo ================================================================
echo.
echo Next steps:
echo   1. Restart your backend server
echo   2. Test the API endpoints:
echo      - GET /api/workers/activities (worker view)
echo      - GET /api/police/workers/1/activities (police view)
echo   3. Implement frontend UI (see WORKER_ACTIVITY_TRACKING_FEATURE.md)
echo.
pause

