# 전자책 PDF 업로드 (Flask)

이 프로젝트는 기존 `pages/index.js` (React/Next.js) 페이지를 Python(Flask) 기반으로 변환한 간단한 업로드/검증 서버입니다.

기능
- 업로드된 PDF를 서버에서 검사: 파일 크기, 암호화 여부, 페이지 수, 첫 페이지 크기(밀리미터), 메타데이터 확인
- 규격은 `public/rules.json`에서 관리
- 관리자 페이지(`/admin`)에서 규격(JSON을 직접 편집) 저장 가능

설치 (Windows PowerShell)

```powershell
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

브라우저에서 http://127.0.0.1:5000/ 열어 사용하세요.

노트
- 업로드된 파일은 `uploads/` 폴더에 저장됩니다.
- `public/rules.json`의 기본 구조는 기존 프로젝트의 값과 동일합니다.
