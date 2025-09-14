# 전자책 검토자 자동 등록 시스템 실행 스크립트 (PowerShell)
Write-Host "====================================" -ForegroundColor Cyan
Write-Host "전자책 검토자 자동 등록 시스템" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan
Write-Host ""

# 현재 디렉토리로 이동
Set-Location $PSScriptRoot

# Python 설치 확인
try {
    $pythonVersion = python --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python not found"
    }
    Write-Host "Python 버전: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "오류: Python이 설치되어 있지 않습니다." -ForegroundColor Red
    Write-Host "Python 3.7 이상을 설치해주세요." -ForegroundColor Yellow
    Write-Host "다운로드: https://www.python.org/downloads/" -ForegroundColor Yellow
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

# 필요한 패키지 설치
Write-Host ""
Write-Host "필요한 패키지 설치 확인 중..." -ForegroundColor Yellow

try {
    pip install pandas openpyxl selenium webdriver-manager requests beautifulsoup4 --quiet
    if ($LASTEXITCODE -ne 0) {
        throw "Package installation failed"
    }
    Write-Host "패키지 설치 완료!" -ForegroundColor Green
} catch {
    Write-Host "패키지 설치 중 오류가 발생했습니다." -ForegroundColor Red
    Read-Host "아무 키나 눌러 종료"
    exit 1
}

Write-Host ""
Write-Host "전자책 검토자 자동 등록 프로그램을 시작합니다..." -ForegroundColor Cyan
Write-Host ""

# 프로그램 실행
try {
    python "[개발중] 전자책자동등록.py"
} catch {
    Write-Host "프로그램 실행 중 오류가 발생했습니다." -ForegroundColor Red
}

Write-Host ""
Write-Host "프로그램이 종료되었습니다." -ForegroundColor Cyan
Read-Host "아무 키나 눌러 종료"
