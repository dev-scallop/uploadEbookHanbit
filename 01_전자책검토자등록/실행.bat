@echo off
echo ====================================
echo 전자책 검토자 자동 등록 시스템
echo ====================================
echo.

REM 현재 디렉토리로 이동
cd /d "%~dp0"

REM Python 설치 확인
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 오류: Python이 설치되어 있지 않습니다.
    echo Python 3.7 이상을 설치해주세요.
    echo https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Python 버전 확인 중...
python --version

REM 필요한 패키지 설치 확인
echo.
echo 필요한 패키지 설치 확인 중...
pip install pandas openpyxl selenium webdriver-manager requests beautifulsoup4 --quiet

if %errorlevel% neq 0 (
    echo 패키지 설치 중 오류가 발생했습니다.
    pause
    exit /b 1
)

echo 패키지 설치 완료!
echo.

REM 프로그램 실행
echo 전자책 검토자 자동 등록 프로그램을 시작합니다...
echo.
python "[개발중] 전자책자동등록.py"

REM 실행 완료 후 대기
echo.
echo 프로그램이 종료되었습니다.
pause
