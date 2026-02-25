#!/usr/bin/env python3
"""
항공편 검색 프로그램 - Amadeus API
김해/대구 → 홍콩/상하이 직항 검색 후 GitHub Pages용 HTML 생성
"""

import json
import os
import sys
from datetime import datetime, timedelta

try:
    from amadeus import Client, ResponseError
    AMADEUS_AVAILABLE = True
except ImportError:
    AMADEUS_AVAILABLE = False

# ============================================================
# 설정 - 여기에 API 키를 입력하세요
# ============================================================
AMADEUS_CLIENT_ID = os.environ.get("AMADEUS_CLIENT_ID", "YOUR_CLIENT_ID")
AMADEUS_CLIENT_SECRET = os.environ.get("AMADEUS_CLIENT_SECRET", "YOUR_CLIENT_SECRET")

# ============================================================
# 검색 조건 정의
# ============================================================
ORIGINS = {
    "PUS": "김해(부산)",
    "TAE": "대구",
}

DESTINATIONS = {
    "HKG": "홍콩",
    "PVG": "상하이(푸동)",
}

# (출발일, 귀국일, 표시용 라벨)
DATE_PAIRS = [
    ("2026-05-01", "2026-05-04", "5/1~5/4 (3박4일)"),
    ("2026-05-01", "2026-05-05", "5/1~5/5 (4박5일)"),
    ("2026-05-22", "2026-05-26", "5/22~5/26 (4박5일)"),
    ("2026-05-23", "2026-05-26", "5/23~5/26 (3박4일)"),
]

MAX_PRICE = 550000          # 1인당 55만원 미만 (KRW)
MAX_PRICE_PER_PERSON = 550000
ADULTS = 4
MAX_RESULTS_PER_ROUTE = 3   # 날짜당 최대 3개 노선
CURRENCY = "KRW"

# ============================================================
# Amadeus API 검색
# ============================================================
def search_flights():
    amadeus = Client(
        client_id=AMADEUS_CLIENT_ID,
        client_secret=AMADEUS_CLIENT_SECRET,
    )
    
    all_results = []
    api_call_count = 0
    
    for dep_date, ret_date, date_label in DATE_PAIRS:
        for orig_code, orig_name in ORIGINS.items():
            for dest_code, dest_name in DESTINATIONS.items():
                route_label = f"{orig_name} → {dest_name}"
                print(f"  검색 중: {route_label} | {date_label}...", end=" ")
                api_call_count += 1
                
                try:
                    response = amadeus.shopping.flight_offers_search.get(
                        originLocationCode=orig_code,
                        destinationLocationCode=dest_code,
                        departureDate=dep_date,
                        returnDate=ret_date,
                        adults=ADULTS,
                        nonStop="true",          # 직항만
                        currencyCode=CURRENCY,
                        max=10,                   # 최대 10개 후보
                    )
                    
                    offers = response.data
                    filtered = []
                    
                    for offer in offers:
                        total_price = float(offer["price"]["grandTotal"])
                        price_per_person = total_price / ADULTS
                        
                        # 1인당 55만원 미만 필터
                        if price_per_person >= MAX_PRICE_PER_PERSON:
                            continue
                        
                        # 잔여석 확인 (numberOfBookableSeats >= 4)
                        seats = offer.get("numberOfBookableSeats", 0)
                        if seats < ADULTS:
                            continue
                        
                        # 출발편 정보
                        go_seg = offer["itineraries"][0]["segments"][0]
                        # 귀국편 정보
                        ret_seg = offer["itineraries"][1]["segments"][0]
                        
                        # 박 수 계산
                        d1 = datetime.strptime(dep_date, "%Y-%m-%d")
                        d2 = datetime.strptime(ret_date, "%Y-%m-%d")
                        nights = (d2 - d1).days
                        
                        filtered.append({
                            "route": route_label,
                            "date_label": date_label,
                            "nights": nights,
                            "days": nights + 1,
                            "origin": orig_code,
                            "destination": dest_code,
                            "dep_date": dep_date,
                            "ret_date": ret_date,
                            # 출발편
                            "go_flight": go_seg["carrierCode"] + go_seg["number"],
                            "go_airline": go_seg["carrierCode"],
                            "go_depart": go_seg["departure"]["at"],
                            "go_arrive": go_seg["arrival"]["at"],
                            # 귀국편
                            "ret_flight": ret_seg["carrierCode"] + ret_seg["number"],
                            "ret_airline": ret_seg["carrierCode"],
                            "ret_depart": ret_seg["departure"]["at"],
                            "ret_arrive": ret_seg["arrival"]["at"],
                            # 가격
                            "total_price": int(total_price),
                            "price_per_person": int(price_per_person),
                            "seats": seats,
                        })
                    
                    # 가격순 정렬 후 상위 3개만
                    filtered.sort(key=lambda x: x["total_price"])
                    filtered = filtered[:MAX_RESULTS_PER_ROUTE]
                    
                    all_results.extend(filtered)
                    print(f"✓ {len(filtered)}건 발견")
                    
                except ResponseError as e:
                    print(f"✗ 오류: {e}")
                except Exception as e:
                    print(f"✗ 예외: {e}")
    
    print(f"\n총 API 호출: {api_call_count}회")
    print(f"총 검색 결과: {len(all_results)}건")
    return all_results, api_call_count


# ============================================================
# 항공사 코드 → 한글 이름 매핑
# ============================================================
AIRLINE_NAMES = {
    "KE": "대한항공",
    "OZ": "아시아나",
    "7C": "제주항공",
    "TW": "티웨이항공",
    "LJ": "진에어",
    "BX": "에어부산",
    "ZE": "이스타항공",
    "RS": "에어서울",
    "4V": "플라이강원",
    "HX": "홍콩항공",
    "CX": "캐세이퍼시픽",
    "UO": "홍콩익스프레스",
    "CA": "중국국제항공",
    "MU": "중국동방항공",
    "CZ": "중국남방항공",
    "HO": "준야오항공",
    "9C": "스프링항공",
    "FM": "상하이항공",
}

def get_airline_name(code):
    return AIRLINE_NAMES.get(code, code)


# ============================================================
# 스카이스캐너 링크 생성
# ============================================================
SKYSCANNER_CITY = {
    "PUS": "PUS",
    "TAE": "TAE",
    "HKG": "HKG",
    "PVG": "PVGA",
}

def make_skyscanner_url(origin, destination, dep_date, ret_date, adults=4):
    """스카이스캐너 검색 URL 생성"""
    o = SKYSCANNER_CITY.get(origin, origin)
    d = SKYSCANNER_CITY.get(destination, destination)
    # 날짜 형식: YYMMDD
    dep = datetime.strptime(dep_date, "%Y-%m-%d").strftime("%y%m%d")
    ret = datetime.strptime(ret_date, "%Y-%m-%d").strftime("%y%m%d")
    return f"https://www.skyscanner.co.kr/transport/flights/{o}/{d}/{dep}/{ret}/?adults={adults}&adultsv2={adults}&cabinclass=economy&childrenv2=&ref=home&rtn=1&preferdirects=true"


# ============================================================
# HTML 리포트 생성
# ============================================================
def generate_html(results, api_call_count):
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # 날짜별로 그룹핑
    groups = {}
    for r in results:
        key = r["date_label"]
        if key not in groups:
            groups[key] = []
        groups[key].append(r)
    
    # 각 그룹 내 가격순 정렬
    for key in groups:
        groups[key].sort(key=lambda x: x["price_per_person"])
    
    # 카드 HTML 생성
    cards_html = ""
    
    if not results:
        cards_html = """
        <div class="empty-state">
            <div class="empty-icon">✈️</div>
            <p>조건에 맞는 항공편이 없습니다.</p>
            <p class="empty-sub">가격 조건을 완화하거나 다른 날짜를 시도해보세요.</p>
        </div>
        """
    else:
        for date_label, flights in groups.items():
            cards_html += f'<div class="date-group">\n'
            cards_html += f'  <h2 class="date-header"><span class="date-icon">📅</span> {date_label}</h2>\n'
            cards_html += f'  <div class="flight-grid">\n'
            
            for i, f in enumerate(flights):
                airline_name = get_airline_name(f["go_airline"])
                ret_airline_name = get_airline_name(f["ret_airline"])
                
                go_dep_time = f["go_depart"][11:16]
                go_arr_time = f["go_arrive"][11:16]
                ret_dep_time = f["ret_depart"][11:16]
                ret_arr_time = f["ret_arrive"][11:16]
                
                price_display = f"{f['total_price']:,}"
                price_pp = f"{f['price_per_person']:,}"
                
                badge_class = "badge-cheap" if f["price_per_person"] < 400000 else "badge-mid" if f["price_per_person"] < 500000 else "badge-normal"
                
                sky_url = make_skyscanner_url(f["origin"], f["destination"], f["dep_date"], f["ret_date"])
                
                cards_html += f"""
    <a href="{sky_url}" target="_blank" rel="noopener" class="flight-card-link" style="animation-delay: {i * 0.08}s">
    <div class="flight-card">
      <div class="card-top">
        <div class="route-badge">{f['route']}</div>
        <div class="nights-badge">{f['nights']}박{f['days']}일</div>
      </div>
      <div class="card-body">
        <div class="flight-row">
          <div class="direction-label">가는편</div>
          <div class="flight-info">
            <span class="flight-num">{f['go_flight']}</span>
            <span class="airline-name">{airline_name}</span>
          </div>
          <div class="time-block">
            <span class="time">{go_dep_time}</span>
            <span class="arrow">→</span>
            <span class="time">{go_arr_time}</span>
          </div>
        </div>
        <div class="flight-row">
          <div class="direction-label">오는편</div>
          <div class="flight-info">
            <span class="flight-num">{f['ret_flight']}</span>
            <span class="airline-name">{ret_airline_name}</span>
          </div>
          <div class="time-block">
            <span class="time">{ret_dep_time}</span>
            <span class="arrow">→</span>
            <span class="time">{ret_arr_time}</span>
          </div>
        </div>
      </div>
      <div class="card-bottom">
        <div class="price-section">
          <div class="price-total">₩{price_display} <span class="price-label">4인 합계</span></div>
          <div class="price-pp">1인당 ₩{price_pp}</div>
        </div>
        <div class="card-bottom-right">
          <div class="seats-badge {badge_class}">잔여 {f['seats']}석</div>
          <div class="sky-link">스카이스캐너에서 보기 ↗</div>
        </div>
      </div>
    </div>
    </a>
"""
            cards_html += "  </div>\n</div>\n"
    
    html = f"""<!DOCTYPE html>
<html lang="ko">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>✈️ 5월 항공편 검색 결과</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
  :root {{
    --bg: #0a0e17;
    --surface: #121929;
    --surface2: #1a2338;
    --border: #243049;
    --text: #e2e8f0;
    --text-dim: #8b9cc0;
    --accent: #60a5fa;
    --accent-glow: rgba(96, 165, 250, 0.15);
    --green: #34d399;
    --amber: #fbbf24;
    --orange: #fb923c;
    --pink: #f472b6;
    --radius: 14px;
  }}

  * {{ margin: 0; padding: 0; box-sizing: border-box; }}

  body {{
    font-family: 'Noto Sans KR', sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    line-height: 1.6;
  }}

  /* 배경 효과 */
  body::before {{
    content: '';
    position: fixed;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 30% 20%, rgba(96,165,250,0.04) 0%, transparent 50%),
                radial-gradient(circle at 70% 80%, rgba(244,114,182,0.03) 0%, transparent 50%);
    z-index: -1;
    animation: bgShift 20s ease-in-out infinite alternate;
  }}

  @keyframes bgShift {{
    0% {{ transform: translate(0, 0); }}
    100% {{ transform: translate(-5%, -3%); }}
  }}

  .container {{
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem 1.5rem;
  }}

  /* 헤더 */
  .header {{
    text-align: center;
    margin-bottom: 3rem;
    padding: 2.5rem 2rem;
    background: linear-gradient(135deg, var(--surface) 0%, var(--surface2) 100%);
    border: 1px solid var(--border);
    border-radius: 20px;
    position: relative;
    overflow: hidden;
  }}

  .header::after {{
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, var(--accent), var(--pink), var(--amber));
  }}

  .header h1 {{
    font-size: 2rem;
    font-weight: 900;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
    background: linear-gradient(135deg, var(--accent), var(--pink));
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
  }}

  .header .subtitle {{
    color: var(--text-dim);
    font-size: 0.95rem;
    font-weight: 300;
  }}

  .meta-bar {{
    display: flex;
    justify-content: center;
    gap: 2rem;
    margin-top: 1.2rem;
    flex-wrap: wrap;
  }}

  .meta-item {{
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.8rem;
    color: var(--text-dim);
    background: var(--bg);
    padding: 0.4rem 1rem;
    border-radius: 20px;
    border: 1px solid var(--border);
  }}

  .meta-item span {{ color: var(--accent); font-weight: 600; }}

  /* 조건 요약 */
  .conditions {{
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: 0.8rem;
    margin-bottom: 2.5rem;
  }}

  .cond-chip {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.8rem 1rem;
    text-align: center;
    font-size: 0.85rem;
  }}

  .cond-chip .cond-label {{
    color: var(--text-dim);
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.2rem;
  }}

  .cond-chip .cond-value {{
    font-weight: 700;
    color: var(--text);
  }}

  /* 날짜 그룹 */
  .date-group {{
    margin-bottom: 2.5rem;
  }}

  .date-header {{
    font-size: 1.3rem;
    font-weight: 700;
    margin-bottom: 1.2rem;
    padding-bottom: 0.8rem;
    border-bottom: 2px solid var(--border);
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}

  .date-icon {{ font-size: 1.1rem; }}

  /* 항공편 그리드 */
  .flight-grid {{
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(340px, 1fr));
    gap: 1rem;
  }}

  /* 항공편 카드 */
  .flight-card {{
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    overflow: hidden;
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
    animation: cardIn 0.5s ease-out both;
  }}

  .flight-card:hover {{
    /* hover는 .flight-card-link에서 처리 */
  }}

  @keyframes cardIn {{
    from {{ opacity: 0; transform: translateY(20px); }}
    to {{ opacity: 1; transform: translateY(0); }}
  }}

  .card-top {{
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.9rem 1.1rem;
    background: var(--surface2);
    border-bottom: 1px solid var(--border);
  }}

  .route-badge {{
    font-weight: 700;
    font-size: 0.95rem;
    color: var(--accent);
  }}

  .nights-badge {{
    font-size: 0.78rem;
    font-weight: 600;
    background: rgba(96,165,250,0.12);
    color: var(--accent);
    padding: 0.25rem 0.7rem;
    border-radius: 20px;
  }}

  .card-body {{
    padding: 1rem 1.1rem;
    display: flex;
    flex-direction: column;
    gap: 0.7rem;
  }}

  .flight-row {{
    display: grid;
    grid-template-columns: 52px 1fr auto;
    align-items: center;
    gap: 0.6rem;
  }}

  .direction-label {{
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-dim);
    background: var(--bg);
    padding: 0.2rem 0.5rem;
    border-radius: 4px;
    text-align: center;
  }}

  .flight-info {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
  }}

  .flight-num {{
    font-family: 'JetBrains Mono', monospace;
    font-weight: 600;
    font-size: 0.9rem;
    color: var(--text);
  }}

  .airline-name {{
    font-size: 0.78rem;
    color: var(--text-dim);
  }}

  .time-block {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    font-family: 'JetBrains Mono', monospace;
  }}

  .time {{
    font-size: 0.9rem;
    font-weight: 600;
    color: var(--text);
  }}

  .arrow {{
    color: var(--text-dim);
    font-size: 0.8rem;
  }}

  .card-bottom {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    padding: 0.9rem 1.1rem;
    border-top: 1px solid var(--border);
    background: var(--surface2);
  }}

  .price-total {{
    font-size: 0.82rem;
    font-weight: 600;
    color: var(--text-dim);
  }}

  .price-label {{
    font-size: 0.7rem;
    font-weight: 400;
    color: var(--text-dim);
    margin-left: 0.3rem;
  }}

  .price-pp {{
    font-size: 1.2rem;
    font-weight: 900;
    color: var(--green);
    margin-top: 0.15rem;
  }}

  .seats-badge {{
    font-size: 0.75rem;
    font-weight: 600;
    padding: 0.3rem 0.8rem;
    border-radius: 20px;
    white-space: nowrap;
  }}

  /* 카드 링크 래퍼 */
  .flight-card-link {{
    text-decoration: none;
    color: inherit;
    display: block;
    animation: cardIn 0.5s ease-out both;
  }}

  .flight-card-link:hover .flight-card {{
    transform: translateY(-4px);
    box-shadow: 0 12px 40px rgba(0,0,0,0.3);
    border-color: var(--accent);
  }}

  .flight-card-link:hover .sky-link {{
    opacity: 1;
    color: var(--accent);
  }}

  .card-bottom-right {{
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.4rem;
  }}

  .sky-link {{
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--text-dim);
    opacity: 0.6;
    transition: opacity 0.2s, color 0.2s;
    white-space: nowrap;
  }}

  /* 카드 hover 제거 (링크 래퍼에서 처리) */
  .flight-card {{
    transition: transform 0.2s, box-shadow 0.2s, border-color 0.2s;
  }}

  .badge-cheap {{
    background: rgba(52,211,153,0.12);
    color: var(--green);
  }}

  .badge-mid {{
    background: rgba(251,191,36,0.12);
    color: var(--amber);
  }}

  .badge-normal {{
    background: rgba(251,146,60,0.12);
    color: var(--orange);
  }}

  /* 빈 상태 */
  .empty-state {{
    text-align: center;
    padding: 4rem 2rem;
    color: var(--text-dim);
  }}

  .empty-icon {{
    font-size: 3rem;
    margin-bottom: 1rem;
    opacity: 0.5;
  }}

  .empty-sub {{
    font-size: 0.85rem;
    margin-top: 0.5rem;
    opacity: 0.7;
  }}

  /* 푸터 */
  .footer {{
    text-align: center;
    padding: 2rem 0;
    margin-top: 2rem;
    border-top: 1px solid var(--border);
    color: var(--text-dim);
    font-size: 0.78rem;
  }}

  /* 반응형 */
  @media (max-width: 640px) {{
    .container {{ padding: 1rem; }}
    .header h1 {{ font-size: 1.5rem; }}
    .flight-grid {{ grid-template-columns: 1fr; }}
    .meta-bar {{ gap: 0.5rem; }}
    .flight-row {{ grid-template-columns: 48px 1fr; }}
    .time-block {{ grid-column: 2; }}
  }}
</style>
</head>
<body>
<div class="container">
  <div class="header">
    <h1>✈️ 5월 항공편 검색</h1>
    <p class="subtitle">김해·대구 출발 → 홍콩·상하이 직항 | 4인 기준</p>
    <div class="meta-bar">
      <div class="meta-item">🕐 업데이트 <span>{now}</span></div>
      <div class="meta-item">🔍 API 호출 <span>{api_call_count}회</span></div>
      <div class="meta-item">📋 결과 <span>{len(results)}건</span></div>
    </div>
  </div>

  <div class="conditions">
    <div class="cond-chip">
      <div class="cond-label">출발지</div>
      <div class="cond-value">김해 · 대구</div>
    </div>
    <div class="cond-chip">
      <div class="cond-label">도착지</div>
      <div class="cond-value">홍콩 · 상하이</div>
    </div>
    <div class="cond-chip">
      <div class="cond-label">조건</div>
      <div class="cond-value">직항 · 4인석</div>
    </div>
    <div class="cond-chip">
      <div class="cond-label">예산</div>
      <div class="cond-value">1인 55만원 미만</div>
    </div>
  </div>

  {cards_html}

  <div class="footer">
    <p>Amadeus API 기반 자동 검색 | 가격은 검색 시점 기준이며 변동될 수 있습니다</p>
  </div>
</div>
</body>
</html>"""
    
    return html


# ============================================================
# 데모 모드 (API 키 없이 HTML 구조 확인용)
# ============================================================
def generate_demo():
    """API 키 없이 샘플 데이터로 HTML 미리보기"""
    demo_results = [
        {
            "route": "김해(부산) → 홍콩", "date_label": "5/1~5/4 (3박4일)",
            "nights": 3, "days": 4, "origin": "PUS", "destination": "HKG",
            "dep_date": "2026-05-01", "ret_date": "2026-05-04",
            "go_flight": "7C2301", "go_airline": "7C",
            "go_depart": "2026-05-01T08:30", "go_arrive": "2026-05-01T11:20",
            "ret_flight": "7C2302", "ret_airline": "7C",
            "ret_depart": "2026-05-04T12:30", "ret_arrive": "2026-05-04T17:10",
            "total_price": 1720000, "price_per_person": 430000, "seats": 9,
        },
        {
            "route": "대구 → 홍콩", "date_label": "5/1~5/4 (3박4일)",
            "nights": 3, "days": 4, "origin": "TAE", "destination": "HKG",
            "dep_date": "2026-05-01", "ret_date": "2026-05-04",
            "go_flight": "TW721", "go_airline": "TW",
            "go_depart": "2026-05-01T09:15", "go_arrive": "2026-05-01T12:05",
            "ret_flight": "TW722", "ret_airline": "TW",
            "ret_depart": "2026-05-04T13:20", "ret_arrive": "2026-05-04T18:00",
            "total_price": 1880000, "price_per_person": 470000, "seats": 5,
        },
        {
            "route": "김해(부산) → 상하이(푸동)", "date_label": "5/1~5/5 (4박5일)",
            "nights": 4, "days": 5, "origin": "PUS", "destination": "PVG",
            "dep_date": "2026-05-01", "ret_date": "2026-05-05",
            "go_flight": "MU5042", "go_airline": "MU",
            "go_depart": "2026-05-01T14:00", "go_arrive": "2026-05-01T15:10",
            "ret_flight": "MU5043", "ret_airline": "MU",
            "ret_depart": "2026-05-05T16:20", "ret_arrive": "2026-05-05T19:30",
            "total_price": 1560000, "price_per_person": 390000, "seats": 12,
        },
        {
            "route": "대구 → 상하이(푸동)", "date_label": "5/22~5/26 (4박5일)",
            "nights": 4, "days": 5, "origin": "TAE", "destination": "PVG",
            "dep_date": "2026-05-22", "ret_date": "2026-05-26",
            "go_flight": "CZ3088", "go_airline": "CZ",
            "go_depart": "2026-05-22T10:00", "go_arrive": "2026-05-22T11:00",
            "ret_flight": "CZ3089", "ret_airline": "CZ",
            "ret_depart": "2026-05-26T12:00", "ret_arrive": "2026-05-26T15:10",
            "total_price": 1400000, "price_per_person": 350000, "seats": 7,
        },
        {
            "route": "김해(부산) → 홍콩", "date_label": "5/23~5/26 (3박4일)",
            "nights": 3, "days": 4, "origin": "PUS", "destination": "HKG",
            "dep_date": "2026-05-23", "ret_date": "2026-05-26",
            "go_flight": "BX733", "go_airline": "BX",
            "go_depart": "2026-05-23T07:45", "go_arrive": "2026-05-23T10:35",
            "ret_flight": "BX734", "ret_airline": "BX",
            "ret_depart": "2026-05-26T11:45", "ret_arrive": "2026-05-26T16:30",
            "total_price": 1640000, "price_per_person": 410000, "seats": 6,
        },
    ]
    return demo_results


# ============================================================
# 메인
# ============================================================
def main():
    output_path = "index.html"
    
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    
    demo_mode = AMADEUS_CLIENT_ID == "YOUR_CLIENT_ID" or not AMADEUS_AVAILABLE
    
    if demo_mode:
        print("=" * 50)
        print("⚠️  데모 모드 (API 키 미설정)")
        print("   환경변수 설정 후 실행하세요:")
        print("   export AMADEUS_CLIENT_ID=your_id")
        print("   export AMADEUS_CLIENT_SECRET=your_secret")
        print("=" * 50)
        print("\n샘플 데이터로 HTML을 생성합니다...\n")
        results = generate_demo()
        api_call_count = 0
    else:
        print("=" * 50)
        print("✈️  항공편 검색 시작")
        print("=" * 50)
        print(f"출발지: 김해, 대구")
        print(f"도착지: 홍콩, 상하이")
        print(f"조건: 직항, 4인, 1인 55만원 미만")
        print(f"예상 API 호출: 16회\n")
        results, api_call_count = search_flights()
    
    # HTML 생성
    html = generate_html(results, api_call_count)
    
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    
    print(f"\n✅ HTML 생성 완료: {output_path}")
    print(f"   GitHub Pages에 push하면 바로 확인 가능!")


if __name__ == "__main__":
    main()
