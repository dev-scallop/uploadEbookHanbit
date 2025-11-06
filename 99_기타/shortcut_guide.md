# 아이폰 단축어 JSON 파일 사용 가이드

## 단축어 JSON 파일을 아이폰에서 사용하는 방법

1. **단축어 JSON을 .shortcut 파일로 변환**
   - JSON 파일을 .shortcut 파일로 변환하려면 도구가 필요합니다
   - [ShortcutsCatalyst](https://github.com/BluesubaruWRXSTI/ShortcutsCatalyst)와 같은 오픈 소스 도구를 사용할 수 있습니다
   - 또는 Mac에서 [Shortcuts JS](https://github.com/joshfarrant/shortcuts-js)와 같은 라이브러리 사용 가능

2. **단축어 공유 URL 생성 방법**
   - .shortcut 파일을 iCloud 또는 다른 파일 공유 서비스에 업로드
   - 링크를 생성하고 이 링크를 아이폰에서 열면 자동으로 단축어 앱으로 연결됨

3. **JSON 구조 이해하기**
   - `WFWorkflowClientVersion`: 단축어 클라이언트 버전
   - `WFWorkflowActions`: 단축어의 실제 동작을 정의하는 배열
   - `WFWorkflowActionIdentifier`: 각 동작의 고유 식별자
   - `WFWorkflowActionParameters`: 각 동작의 매개변수

4. **직접 만들기**
   - 기존 단축어를 내보내고 JSON 구조를 분석하면 쉽게 이해할 수 있음
   - 아이폰에서 단축어를 만든 후 공유 -> 파일 형식으로 저장하여 JSON 구조 확인 가능

5. **일반적인 Identifier 예시**
   - `is.workflow.actions.showresult`: 결과 표시
   - `is.workflow.actions.gettext`: 텍스트 가져오기
   - `is.workflow.actions.getcurrentdate`: 현재 날짜 가져오기
   - `is.workflow.actions.runshortcut`: 다른 단축어 실행
   - `is.workflow.actions.conditional`: 조건문
   - `is.workflow.actions.getwebpagecontents`: 웹 페이지 내용 가져오기

## 변환 도구
- [ShortcutsGallery](https://shortcutsgallery.com/) - 다양한 단축어 공유 및 탐색
- [RoutineHub](https://routinehub.co/) - 단축어 공유 플랫폼

## 주의사항
- JSON 구조는 복잡하고 단축어 앱 버전에 따라 달라질 수 있음
- 직접 작성한 JSON은 버전 호환성 문제가 발생할 수 있음
- 중요한 단축어의 경우 백업 권장
