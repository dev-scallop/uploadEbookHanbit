## 목적

이 파일은 이 리포지토리에서 자동화 에이전트(예: GitHub Copilot/코드작성 에이전트)가 빠르게 생산적으로 작업할 수 있도록 코드베이스의 핵심 구조, 개발 워크플로우, 규약, 그리고 흔히 편집해야 할 파일/경로를 요약합니다.

## 한눈에 보는 프로젝트 구조(중요한 부분)

- `01_전자책검토자등록/` – 여러 개의 독립형 파이썬 스크립트(자동화, GUI 등). 대부분 단일 파일 실행 방식.
- `02_실사용_프로그램/` – 실사용용으로 이름된 여러 파이썬 스크립트(배포 전용 스크립트).
- `03_테스트_및_개발/` – 실험/서비스별 서브프로젝트가 모여 있음. 특히 관심할 디렉토리:
  - `랜덤상세페이지자동생성프로그램/` — Python 패키지 구조(`src/`), 템플릿, 테스트(`tests/test_generation.py`).
  - `상세페이지제작툴/` — GUI 프로그램(여러 스크립트와 README, requirements.txt).
  - `전자책PDF업로드/` — (중요) 웹 업로드/검증 서비스: `app.py`, `templates/`, `public/rules.json`, `requirements.txt`, `uploads/`.

에이전트는 수정할 대상이 어느 하위 프로젝트인지 먼저 확인하세요. 각 하위 프로젝트는 서로 다른 실행법을 가집니다.

## 핵심 패턴과 규약

- 대부분의 파이썬 코드가 "단일 스크립트 실행" 방식입니다. 즉, `python script.py`로 실행하면 동작합니다.
- 하위 프로젝트별로 `requirements.txt`가 존재할 수 있으니, 변경/테스트 전 해당 폴더에서 가상환경을 만들고 설치하세요.
- 설정/규격은 종종 `public/rules.json` 또는 각 프로젝트의 `README.md`에서 관리됩니다. 예: `전자책PDF업로드/public/rules.json`.
- UI 템플릿(Flask)은 `templates/` 디렉토리에 존재합니다. 서버를 실행할 때 현재 작업 디렉토리가 프로젝트 루트여야 경로가 올바릅니다.
- PDF 처리 라이브러리: `pypdf`(최신) 또는 이전 환경의 `PyPDF2`를 코드에서 호환 처리하고 있습니다. 파싱 오류와 암호화 케이스를 유의하세요.

## 개발/실행 워크플로우 (프로젝트별 예시)

1) `전자책PDF업로드` 빠른 실행 (PowerShell 권장)

```powershell
cd .\03_테스트_및_개발\전자책PDF업로드
python -m venv venv; .\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

- 서버가 `http://127.0.0.1:5000`에서 동작합니다. 업로드 UI: `/`, 규격 편집: `/admin`.
- 서버 실행 시 작업 디렉토리를 위와 같이 맞추지 않으면 `public/rules.json`을 찾지 못하거나 업로드 경로(`uploads/`)가 잘못될 수 있습니다.

2) 업로드 API 테스트 예시

PowerShell (파일 `sample.pdf` 업로드)
```powershell
$file = Get-Item .\sample.pdf
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.SecurityProtocolType]::Tls12
$res = Invoke-RestMethod -Uri http://127.0.0.1:5000/api/upload -Method Post -InFile $file.FullName -ContentType 'application/pdf'
$res | ConvertTo-Json
```

curl 예시
```bash
curl -F "file=@sample.pdf" http://127.0.0.1:5000/api/upload
```

응답은 JSON이며, 오류가 있으면 HTTP 400과 `errors` 배열을 반환합니다.

## 코드 수정 시 주의사항 / 예시 패턴

- PDF 규격 로직: `전자책PDF업로드/app.py`의 `handle_file_from_request` 함수가 핵심입니다. 여기서
  - 파일 크기 검사 (rules.json의 `maxFileSizeMB`)
  - 암호화 확인 (`disallowEncrypted`)
  - 페이지 수 (`minPages`, `maxPages`)
  - 첫 페이지 크기 비교 (`pageSize.widthMm`, `heightMm`, `toleranceMm`)
  - 메타데이터 필드 확인 (`requireMetadata`)

- 규칙(규격) 변경은 `public/rules.json`을 수정하거나 `/admin`에서 JSON을 편집해 저장하면 적용됩니다.
- 파일 저장 경로는 `uploads/`에 상대 경로로 작성됩니다. 충돌 처리가 필요하면 파일 이름에 타임스탬프나 UUID를 덧붙이세요.

## 테스트와 정적 검사

- 일부 서브프로젝트에 테스트가 존재합니다(예: `랜덤상세페이지자동생성프로그램/tests`). 테스트 실행은 해당 디렉토리에서 `pytest`를 권장합니다.
- 린트/타입체크는 리포지토리에 통일된 설정 파일이 없으므로, 변경 시 프로젝트 컨벤션에 맞춰 `flake8`/`black`/`mypy`를 부분 도입하세요.

## 통합 포인트 / 외부 의존성

- 외부 라이브러리: 주요 파이썬 의존성은 각 프로젝트의 `requirements.txt`에 기록되어 있습니다. 예: `03_테스트_및_개발/전자책PDF업로드/requirements.txt`.
- 일부 프로젝트(웹 템플릿/프론트엔드)에서는 `package.json`이 존재할 수 있습니다. 필요 시 해당 디렉토리에서 `npm install` 후 빌드를 실행하세요.

## 변경 제안 시 에이전트 행동 규칙

- 변경 범위가 작으면(디렉토리 하나/스크립트 하나) 단일 PR을 만드세요. PR 설명에 "어떤 문제를 어떻게 해결했고, 수동 테스트는 어떻게 했는가"를 간단히 적습니다.
- 파일 IO 경로는 로컬 OneDrive/절대경로 이슈가 자주 발생합니다. 테스트는 가능한 한 상대 경로(프로젝트 루트 기준)로 수행하세요.

## 빠른 체크리스트 (수정/디버깅 시)

1. 해당 하위 프로젝트 폴더로 이동
2. 가상환경 생성 및 `pip install -r requirements.txt`
3. 서버/스크립트 실행(예: `python app.py`) — 로그 확인
4. API/기능 수동 테스트 (브라우저 또는 curl/PowerShell)
5. 실패 시: 파일 경로(`public/rules.json`, `uploads/`)와 현재 작업 디렉토리 확인

---
## 개인 채팅 지침 (공개)

다음 지침을 이 리포지토리에서 작업하는 자동화 에이전트가 항상 따르도록 합니다. 이 섹션은 공개 문서이므로 민감한 정보를 포함하지 마세요.

- 항상 한국어로 응답하세요.
- 사용자는 초보자 수준의 코딩 실력을 가지고 있습니다. 코드를 수정하거나 새 파일을 생성할 때는 "왜 이렇게 해야 하는지"를 간단하고 친절한 교육자 관점으로 설명하세요. 예를 들어: "이 코드를 이렇게 나눠야 하는 이유는 테스트하기 쉽고, 오류가 발생했을 때 위치를 빨리 찾을 수 있기 때문입니다."
- 변경사항을 적용할 때는 변경 파일 목록과 각 변경의 의도(무엇을 고쳤고, 왜 고쳤는지)를 함께 제공하세요. 가능한 경우 실행/검증 방법(Windows PowerShell 명령 예시 포함)을 덧붙이세요.
- 절대 경로나 비밀(토큰, 비밀번호)을 코드에 하드코딩하지 마세요. 민감 정보는 환경변수나 설정 파일(그리고 `.gitignore`)을 사용하라고 안내하세요.
- 사용자가 요청한 수정이 불분명하면 1-2개의 합리적 추정을 제안하고 그 중 하나를 선택해 진행한 뒤, 변경한 가정(assumption)을 명확히 기록하세요.

피드백 요청: 이 내용에서 더 상세히 다루길 원하는 서브프로젝트(예: `상세페이지제작툴`의 실행/테스트, `랜덤상세페이지자동생성프로그램`의 CI 명세 등)를 알려주시면 해당 부분을 확장해 업데이트하겠습니다.
