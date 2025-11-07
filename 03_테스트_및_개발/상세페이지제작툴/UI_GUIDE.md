# Toss 스타일 UI 가이드 📱

## 🎨 디자인 시스템

### 컬러 팔레트

```python
COLORS = {
    'primary': '#0064FF',        # Toss 블루 - 주요 액션 버튼
    'primary_dark': '#0050CC',   # 호버 상태
    'bg_main': '#F9FAFB',        # 메인 배경
    'bg_card': '#FFFFFF',        # 카드 배경
    'text_primary': '#191F28',   # 주요 텍스트
    'text_secondary': '#4E5968', # 보조 텍스트
    'text_tertiary': '#8B95A1',  # 비활성 텍스트
    'border': '#E5E8EB',         # 테두리
    'success': '#0ECC5E',        # 성공 상태
    'warning': '#FFAE0D',        # 경고 상태
    'error': '#FF4747',          # 오류 상태
    'divider': '#F2F4F6',        # 구분선
}
```

## 📐 레이아웃 구조

### 좌측 패널 (40%)
```
┌─────────────────────────────┐
│ 📌 헤더                      │
│   - 제목                     │
│   - 부제                     │
├─────────────────────────────┤
│ 🔑 API 설정 카드             │
│   - OpenAI API Key           │
│   - HCTI User ID             │
│   - HCTI API Key             │
│   - Apps Script URL          │
├─────────────────────────────┤
│ 📊 Google Sheets 설정 카드   │
│   - Watch Spreadsheet ID     │
│   - Watch Sheet Name         │
│   - Target Spreadsheet ID    │
│   - Target Sheet Name        │
│   - Poll Interval            │
│   - 저장 폴더                │
├─────────────────────────────┤
│ ⚡ 실행 버튼 카드             │
│   - 💾 설정 저장 | ▶ 한 번 실행 │
│   - 🔄 시작(연속) | ⏸ 중지     │
└─────────────────────────────┘
```

### 우측 패널 (60%)
```
┌─────────────────────────────┐
│ 📊 상태 카드 (2열)            │
│  ┌──────────┐ ┌──────────┐  │
│  │ ● 실행상태│ │ ✓ 처리완료│  │
│  │  대기 중  │ │   0건     │  │
│  └──────────┘ └──────────┘  │
├─────────────────────────────┤
│ 📋 실행 로그 카드             │
│                              │
│  [지우기 버튼]               │
│  ┌──────────────────────┐   │
│  │ 2025-01-06 14:30:22  │   │
│  │ INFO 처리 시작...     │   │
│  │ INFO OpenAI 호출 완료 │   │
│  │ ✅ 처리 완료: 원본 2   │   │
│  │                       │   │
│  └──────────────────────┘   │
└─────────────────────────────┘
```

## 🖱️ 인터랙션

### ModernButton 컴포넌트
- **기본 상태**: 명확한 둥근 버튼
- **호버**: 10% 어두워짐 + hand2 커서
- **클릭**: 즉시 반응

### ModernEntry 컴포넌트
- **기본**: 회색 테두리 (1px)
- **포커스**: 파란색 테두리 (2px) - Toss 특유의 강조
- **비밀번호**: `show="●"` 옵션으로 동그라미 표시

### StatusCard 컴포넌트
- **아이콘**: 이모지 기반 직관적 표현
- **타이틀**: 작은 회색 라벨
- **값**: 큰 굵은 텍스트
- **동적 색상**: 상태에 따라 색상 변경

## ✨ 주요 기능

### 1. 설정 저장 (💾)
```python
def _save_to_env(self):
    # UI 입력값 → .env 파일 저장
    # python-dotenv의 set_key() 사용
```

**사용자 플로우:**
1. 폼에 API 키 입력
2. "설정 저장" 버튼 클릭
3. `.env` 파일에 암호화 없이 평문 저장 (로컬 전용)
4. 성공 메시지 표시

### 2. 한 번 실행 (▶)
```python
def run_once(self):
    # 1회만 새 행 처리
    # 상태 카드 업데이트: 실행 중 → 완료/대기
```

**상태 전환:**
- 대기 중 → 실행 중... (주황) → 완료 (초록) / 대기 중 (회색)

### 3. 시작(연속) (🔄)
```python
def start_loop(self):
    # 백그라운드 스레드 시작
    # poll_interval마다 체크
```

**상태 카드 표시:**
- "실행 중 (최근: 행2)" - 실시간 업데이트
- "대기 중 (신규 없음)" - 신규 행 없을 때

### 4. 중지 (⏸)
```python
def stop_loop(self):
    # stop_event.set()
    # 부드러운 종료
```

## 🎯 사용자 경험 개선

### Toss 스타일 특징

1. **명확한 계층 구조**
   - 카드 기반 레이아웃
   - 그림자 최소화 (1px border)
   - 넉넉한 여백 (20px padding)

2. **즉각적 피드백**
   - 버튼 호버 시 즉시 반응
   - 입력 포커스 시 파란 테두리
   - 상태 카드 색상 변경

3. **읽기 쉬운 타이포그래피**
   - Segoe UI (Windows 최적화)
   - 명확한 폰트 크기 차이
   - 적절한 행간 (line-height)

4. **단계별 안내**
   - 이모지로 직관적 구분
   - 힌트 텍스트 (회색 작은 글씨)
   - 로그 메시지에 아이콘 (✅, ❌, ℹ️)

## 🔄 상태 관리

### 상태 카드 색상 매핑

| 상태 | 텍스트 | 색상 |
|------|--------|------|
| 대기 중 | "대기 중" | text_primary (#191F28) |
| 실행 중 | "실행 중..." | warning (#FFAE0D) |
| 완료 | "완료" | success (#0ECC5E) |
| 오류 | "오류" | error (#FF4747) |
| 중지됨 | "중지됨" | text_tertiary (#8B95A1) |

### 처리 완료 카운터

```python
processed_count = 0  # 세션 내 누적
self.processed_card.set_value(f"{processed_count}건", COLORS['success'])
```

## 📱 반응형 고려사항

현재는 1200x800 고정 크기이지만, 추후 반응형 확장 가능:

```python
# 창 크기 변경 허용
self.root.resizable(True, True)

# 최소 크기 설정
self.root.minsize(1000, 700)
```

## 🎨 커스터마이징

### 색상 변경
`COLORS` 딕셔너리에서 hex 코드 변경:

```python
COLORS = {
    'primary': '#FF6B6B',  # 빨강 테마
    # ...
}
```

### 버튼 크기 조정
`ModernButton` 인스턴스 생성 시:

```python
ModernButton(parent, "텍스트", command, 
            width=200, height=60)  # 더 큰 버튼
```

### 폰트 변경
```python
font=('나눔고딕', 10, 'bold')  # 한글 폰트
```

## 🐛 알려진 제한사항

1. **스크롤 성능**: 설정이 많아지면 스크롤이 느려질 수 있음
   - 해결: Canvas 기반 스크롤 사용 중

2. **창 크기 고정**: 현재 1200x800 고정
   - 해결: resizable(True, True) 추가 가능

3. **다크모드 미지원**: 라이트 모드만 지원
   - 해결: COLORS_DARK 딕셔너리 추가 가능

## 📚 참고 자료

- [Toss Design System](https://toss.im/career/article/next-product)
- [토스 컬러 시스템](https://blog.toss.im/article/color-system)
- [Python Tkinter 공식 문서](https://docs.python.org/3/library/tkinter.html)

---

**UI 디자인 원칙:**
> "사용자가 생각할 필요 없이, 직관적으로 알 수 있어야 한다." - Toss
