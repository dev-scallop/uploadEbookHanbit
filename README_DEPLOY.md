배포 가이드

이 문서는 GitHub에 커밋/푸시하고 Vercel(프론트) 및 Render(Flask 백엔드)로 배포하는 방법을 단계별로 적어둡니다.

1) Git 준비 및 커밋
- 프로젝트 폴더로 이동:
  cd "c:\Users\taejin\Desktop\OneDrive\1_코드\03_테스트_및_개발\tasks\03_테스트_및_개발\전자책PDF업로드"

- .gitignore가 이미 설정되어 있습니다. (uploads/ 등 제외)

- 깃 초기화/커밋:
  git init
  git add .
  git commit -m "Add Flask PDF upload/validation app"

- 원격 리포지토리 생성 (GitHub 웹 또는 gh CLI 사용):
  gh repo create <your-username>/<repo-name> --public --source=. --remote=origin --push
  # 또는 웹에서 생성 후 아래 명령으로 원격 추가
  git remote add origin https://github.com/<username>/<repo>.git
  git branch -M main
  git push -u origin main

2) Vercel (프론트 전용) 연결
- 목적: 템플릿/정적 파일(전달용 UI 등)을 Vercel에서 호스팅.
- Vercel 설정에서 GitHub 리포지토리를 연동하고, 빌드 명령과 출력 디렉터리를 지정합니다.
- 주의: Flask API는 Vercel에 올리지 말고 별도 백엔드(아래 Render)에 둡니다.

3) Render에 Flask 백엔드 배포 (권장)
- Render.com에 가입 후 GitHub 계정 연결
- New -> Web Service -> Repository 선택
- Branch: main
- Build Command: (보통 비워둬도 무방) pip install -r requirements.txt
- Start Command: gunicorn -w 2 -b 0.0.0.0:$PORT app:app
- Environment: 추가로 FLASK_SECRET_KEY 와 ADMIN_PASSWORD 값을 설정
- Create and Deploy

4) 프론트에서 API 호출 주소 변경
- Vercel에 프론트를 올리고 Render에서 백엔드를 배포하면 Render가 제공하는 URL(예: https://my-backend.onrender.com)을 프론트의 API 엔드포인트로 사용하세요.

5) 권장 추가
- GitHub Actions 또는 Render의 자동 배포 기능을 이용해 main 브랜치에 푸시하면 자동 배포되도록 설정하세요.

문제가 생기면 에러 로그와 함께 알려주시면 도와드리겠습니다.