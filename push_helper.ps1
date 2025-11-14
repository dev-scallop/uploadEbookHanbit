# 간단한 PowerShell 배포 도우미 스크립트
# 사용법: 이 파일을 프로젝트 루트에 두고 내용을 확인한 뒤 실행하세요.

param(
    [string]$RepoUrl = ''
)

if (-not (Test-Path .git)) {
    git init
}

git add .
$commitMsg = Read-Host "커밋 메시지 입력 (기본: 'deploy')"
if (-not $commitMsg) { $commitMsg = 'deploy' }
git commit -m $commitMsg

if ($RepoUrl) {
    git remote remove origin 2>$null
    git remote add origin $RepoUrl
    git branch -M main
    git push -u origin main
} else {
    Write-Host "원격 저장소 URL을 제공하지 않았습니다. 웹에서 리포지토리를 만들고 아래 명령으로 원격을 추가하세요:"
    Write-Host "git remote add origin https://github.com/<username>/<repo>.git"
}
