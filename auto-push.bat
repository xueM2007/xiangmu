@echo off
chcp 65001 >nul
title Git Push
cd /d "E:\项目"

echo.
echo Cleaning stale locks...
del /f .git\index.lock 2>nul
del /f .git\HEAD.lock 2>nul

echo Adding files...
git add .

echo Committing...
git commit -m "Update site"

echo.
echo Pushing to GitHub...
git push origin main

echo.
echo Pushing to Gitee...
git push gitee main

echo.
echo ========================================
echo Push complete!
echo GitHub: https://xuem2007.github.io/xiangmu/
echo Gitee:   https://xuem.gitee.io/xiangmu/
echo ========================================
echo.
pause
