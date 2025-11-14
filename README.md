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

도서별 세부 규격 사용

- 관리자(혹은 운영자)는 각 도서별 규격(도서명, 도서사이즈, 페이지수)을 엑셀 파일로 만들어 `public/book_specs.xlsx`에 배치하면, 업로드 페이지에서 사용자가 원 도서를 선택했을 때 해당 도서의 규격으로 검사합니다.
- 엑셀 파일의 예상 컬럼: `도서명`, `도서사이즈`, `페이지수`.
	- `도서사이즈`는 `폭x높이` 형식(예: `148x210`) 또는 `폭 높이` 형식도 허용합니다(단위: mm).
	- `페이지수`는 정수로 기재하세요.
