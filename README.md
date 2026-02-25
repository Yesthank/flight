# ✈️ 5월 항공편 자동 검색

Amadeus API로 김해/대구 출발 직항 항공편을 자동 검색하고, GitHub Pages에 결과를 게시합니다.

## 검색 조건

| 항목 | 내용 |
|------|------|
| 출발지 | 김해(부산), 대구 |
| 도착지 | 홍콩, 상하이, 베이징, 칭다오, 도쿄, 삿포로 |
| 날짜 | 5/1~4, 5/1~5, 5/22~25, 5/22~26, 5/23~26 |
| 조건 | 직항, 4인 좌석 확보, 1인당 55만원 미만 |
| 표시 | 노선당 최저가 3개 |

## 사용법

### 로컬 실행
```bash
pip install amadeus
export AMADEUS_CLIENT_ID=your_key
export AMADEUS_CLIENT_SECRET=your_secret
python flight_search.py
```
실행하면 `index.html`이 생성됩니다.

### GitHub Actions 자동화
1. Repository → Settings → Secrets and variables → Actions에 시크릿 등록:
   - `AMADEUS_CLIENT_ID`
   - `AMADEUS_CLIENT_SECRET`
2. Settings → Pages → Source: **gh-pages** 브랜치, **/ (root)**
3. Settings → Actions → General → Workflow permissions → **Read and write permissions**

매일 한국시간 오전 9시, 오후 9시에 자동 실행됩니다.  
Actions 탭에서 수동 실행(Run workflow)도 가능합니다.

## API 호출량

1회 실행당 약 **60회** (출발 2 × 도착 6 × 날짜 5)

Amadeus 무료 플랜 기준으로 월 호출 한도를 고려해서 하루 1~2회 실행을 권장합니다.

## 파일 구조

```
├── flight_search.py                  # 검색 + HTML 생성 스크립트
├── .github/workflows/search_flights.yml  # GitHub Actions 워크플로우
└── README.md
```
