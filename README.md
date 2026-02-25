# ✈️ 5월 항공편 자동 검색

Amadeus API로 김해/대구 출발 직항 항공편을 자동 검색하고, GitHub Pages에 결과를 게시합니다.  
카드를 클릭하면 스카이스캐너 검색 페이지로 바로 이동합니다.

---

## 검색 조건

| 항목 | 내용 |
|------|------|
| 출발지 | 김해(부산), 대구 |
| 도착지 | 홍콩, 상하이, 베이징, 칭다오, 도쿄, 삿포로 |
| 날짜 | 5/1~4, 5/1~5, 5/22~25, 5/22~26, 5/23~26 |
| 조건 | 직항, 4인 좌석 확보, 1인당 55만원 미만 |
| 표시 | 노선당 최저가 3개 |

---

## 1. Amadeus API 가입 및 키 발급

1. [Amadeus for Developers](https://developers.amadeus.com/) 접속
2. 우측 상단 **Register** 클릭 → 이메일로 회원가입
3. 로그인 후 **My Self-Service** → **Create new app** 클릭
4. 앱 이름 아무거나 입력 (예: `flight-search`) → **Create**
5. 생성된 앱 페이지에서 두 가지 값을 확인:
   - **API Key** → 이게 `AMADEUS_CLIENT_ID`
   - **API Secret** → 이게 `AMADEUS_CLIENT_SECRET`

> ⚠️ **API Secret은 앱 생성 직후에만 보입니다.** 놓쳤다면 앱을 삭제하고 새로 만드세요.

> ⚠️ 무료(Test) 환경 기준 월 호출 한도가 있습니다. 1회 실행당 약 60회 호출이므로 하루 1~2회 실행을 권장합니다.

---

## 2. 로컬 실행

```bash
pip install amadeus

export AMADEUS_CLIENT_ID=발급받은_API_Key
export AMADEUS_CLIENT_SECRET=발급받은_API_Secret

python flight_search.py
```

실행하면 `index.html`이 생성됩니다. 브라우저로 열어서 확인할 수 있습니다.

> API 키 없이 실행하면 데모(샘플) 데이터로 HTML이 생성됩니다.

---

## 3. GitHub Actions 자동화

### 3-1. 시크릿 등록

Repository → **Settings** → **Secrets and variables** → **Actions** → **New repository secret**

| Name | Value |
|------|-------|
| `AMADEUS_CLIENT_ID` | 발급받은 API Key |
| `AMADEUS_CLIENT_SECRET` | 발급받은 API Secret |

### 3-2. Pages 설정

**Settings** → **Pages** → Source를 **Deploy from a branch** → Branch: **gh-pages** / **/ (root)** → **Save**

### 3-3. Actions 권한

**Settings** → **Actions** → **General** → Workflow permissions → **Read and write permissions** 체크 → **Save**

### 3-4. 실행

- **자동**: 매일 한국시간 오전 9시, 오후 9시에 실행
- **수동**: Actions 탭 → `✈️ 항공편 검색` → **Run workflow** 클릭

---

## 4. 검색 조건 수정하기

`flight_search.py` 상단의 설정값을 수정하면 됩니다.

### 출발지 추가/삭제

```python
ORIGINS = {
    "PUS": "김해(부산)",
    "TAE": "대구",
    # "ICN": "인천",    ← 이렇게 추가
}
```

### 도착지 추가/삭제

```python
DESTINATIONS = {
    "HKG": "홍콩",
    "PVG": "상하이(푸동)",
    "PEK": "베이징",
    "TAO": "칭다오",
    "NRT": "도쿄(나리타)",
    "CTS": "삿포로",
    # "KIX": "오사카(간사이)",  ← 이렇게 추가
}
```

> 공항 코드는 [IATA 공항 코드](https://www.iata.org/en/publications/directories/code-search/) 에서 검색할 수 있습니다.

### 날짜 변경

```python
DATE_PAIRS = [
    ("2026-05-01", "2026-05-04", "5/1~5/4 (3박4일)"),
    # (출발일, 귀국일, 표시용 라벨) 형식으로 추가/수정
]
```

### 가격 조건

```python
MAX_PRICE_PER_PERSON = 550000   # 1인당 최대 금액 (KRW)
```

### 인원 수

```python
ADULTS = 4   # 검색 인원
```

### 노선당 표시 개수

```python
MAX_RESULTS_PER_ROUTE = 3   # 노선별 최대 표시 수
```

### 도착지 추가 시 추가 작업

도착지를 새로 추가하면 아래 두 곳도 같이 수정해야 합니다.

**1) 스카이스캐너 도시 코드** — 카드 클릭 시 스카이스캐너 링크에 사용

```python
SKYSCANNER_CITY = {
    ...
    "KIX": "OSAA",   # 스카이스캐너 URL에서 쓰는 코드
}
```

> 스카이스캐너에서 해당 노선을 직접 검색한 뒤 URL에 나오는 도시 코드를 확인하세요.

**2) 컬러맵** — `generate_html` 함수 내 `color_map`에 새 조합 추가

```python
color_map = {
    ...
    "PUS-KIX": ("origin-pus", "dest-kix"),
    "TAE-KIX": ("origin-tae", "dest-kix"),
}
```

그리고 HTML CSS 부분에 새 도착지 색상 클래스도 추가해주세요.

---

## API 호출량 참고

| 항목 | 계산 |
|------|------|
| 1회 실행 | 출발지 2 × 도착지 6 × 날짜 5 = **60회** |
| 하루 1회 × 7일 | 420회 |
| 하루 2회 × 7일 | 840회 |

무료 플랜 한도를 고려해서 실행 빈도를 조절하세요.

---

## 파일 구조

```
├── flight_search.py                      # 검색 + HTML 생성 스크립트
├── .github/workflows/search_flights.yml  # GitHub Actions 워크플로우
└── README.md
```
