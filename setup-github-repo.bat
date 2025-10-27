@echo off
setlocal

echo 🚀 EMO Options Bot - GitHub Setup Helper
echo.

if "%~1"=="" (
    echo ❌ Error: Please provide your GitHub username
    echo Usage: setup-github-repo.bat your-github-username [repo-name]
    echo Example: setup-github-repo.bat johnsmith
    exit /b 1
)

set USERNAME=%~1
set REPONAME=%~2
if "%REPONAME%"=="" set REPONAME=emo-options-bot

echo 📝 Username: %USERNAME%
echo 📝 Repository: %REPONAME%
echo.

echo 📝 Manual Setup Commands:
echo.
echo 1. Update CODEOWNERS file:
echo    Replace @your-github-handle with @%USERNAME%
echo.
echo 2. Create GitHub repository:
echo    gh repo create %USERNAME%/%REPONAME% --public
echo.
echo 3. Add remote and push:
echo    git remote add origin https://github.com/%USERNAME%/%REPONAME%.git
echo    git branch -M main
echo    git push -u origin main --tags
echo.
echo 4. Visit your repository:
echo    https://github.com/%USERNAME%/%REPONAME%
echo.
echo 🔄 CI/CD will automatically test your code on every push!
echo.
pause