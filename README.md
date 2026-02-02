## 프로젝트 소개

`DATAPROJECT`는 닭(육계) 생산·건강·환경·출하 데이터를 통합 관리하고, 이를 **웹 대시보드 형태로 분석/시각화**하는 Flask 기반 애플리케이션입니다.  
게시판 기능과 함께 **FMS(농장 관리 시스템) 데이터 조회, 분석, 지도 시각화**를 한 곳에서 확인할 수 있도록 설계되었습니다.

- **제작 방식**: 바이브코딩(Vibe Coding) 스타일로, IDE와 AI 코딩 에이전트를 적극 활용해 인터랙티브하게 설계·구현했습니다.

---

## 사용 기술 스택

- **Backend**
  - Python 3
  - Flask
  - psycopg2 (PostgreSQL 연동)
  - python-dotenv (환경 변수 관리)
  - Folium (지도 시각화)
  - Azure Webapp

- **Database**
  - PostgreSQL
  - 주요 스키마/테이블
    - `fms.total_result` (통합 결과 뷰)
    - `fms.chick_info`, `fms.health_cond`, `fms.prod_result`, `fms.env_cond`, `fms.ship_result` 등
    - `board.posts`, `board.comments`, `board.likes` (게시판용)

- **Frontend**
  - HTML5, Jinja2 템플릿
  - Tailwind CSS (CDN)
  - Font Awesome Icons (CDN)
  - Chart.js (CDN, 파스텔톤 차트)

---

## 주요 기능

### 게시판

- **글 목록 / 상세 조회 / 작성 / 수정 / 삭제**
- 조회수, 좋아요(토글), 댓글 기능 제공
- Tailwind 기반의 반응형 UI

### FMS 통합 결과 카드뷰 (`/fms/result`)

- `fms.total_result` 뷰 데이터를 **카드형 리스트**로 표시
- 각 카드에 다음 정보 표시:
  - 육계번호, 품종, 종란무게, 체온, 호흡수, 호수
  - 주문번호, 고객사, 도착일, 도착지
- **부적합 여부(합격/Fail)** 를
  - 초록/핑크 파스텔톤 **캡슐 배지 + 이모지(✅ / ⚠️)** 로 직관적으로 표현
- 상단 우측 버튼으로 분석 대시보드(`/fms/analytics`)로 이동

### FMS 분석 & 시각화 대시보드 (`/fms/analytics`)

- **품종별 출하 비율**
  - 도넛 차트(Chart.js)로 각 품종이 차지하는 비율 시각화
  - 파스텔 팔레트 사용으로 가독성과 포트폴리오용 미관 강화

- **품종별 Pass / Fail 분포**
  - 스택 막대 차트로 품종별 합격/부적합 물량 비교

- **날짜별 출하 추이**
  - 도착일 기준 일별 출하 마릿수를 라인 차트로 표현
  - 면적 그래프 + 포인트 마커로 트렌드 파악 용이

- **고객사별 출하량 Top 5**
  - 상위 5개 고객사 기준 출하량을 막대 차트로 표현
  - 어떤 고객사와 거래 비중이 큰지 한눈에 파악 가능

- **배송 현황 지도 (Folium)**
  - 고객사/도착지 기준 배송 건수를 **파스텔톤 버블 맵**으로 표현
  - 한국 주요 도시 좌표를 미리 매핑하여, 출하량에 따라 버블 크기를 조절
  - `.env`에 `KOREAN_TILE_URL`을 설정하면 한국어 지명을 제공하는 타일 서버를 사용할 수 있도록 확장 가능

### 네비게이션 흐름

- 헤더 탭바의 **FMS 결과** 캡슐 버튼 → `/fms/result`
- `/fms/result` 상단 버튼 → **분석 대시보드 보기** (`/fms/analytics`)
- `/fms/analytics` 상단 버튼 → **통합 결과 테이블(카드뷰)로 돌아가기**

---

## 실행 방법
https://3dt016-webapp-gfhaghgya6eggabf.koreacentral-01.azurewebsites.net/
---

## 폴더 구조 (요약)

```text
DATAPROJECT/
  ├─ myboard/
  │   ├─ app.py                # Flask 메인 애플리케이션
  │   ├─ templates/
  │   │   ├─ base.html         # 공통 레이아웃 및 헤더/푸터
  │   │   ├─ index.html        # 게시판 목록
  │   │   ├─ view.html         # 게시글 상세
  │   │   ├─ create.html       # 게시글 작성
  │   │   ├─ edit.html         # 게시글 수정
  │   │   ├─ fms_result.html   # FMS 통합 결과 카드뷰
  │   │   ├─ fms_analytics.html# FMS 분석 & 시각화 대시보드
  │   │   ├─ fms_map.html      # (선택) 지도 단독 페이지
  │   ├─ .env                  # DB 및 지도 타일 설정
  │   └─  requirements.txt  
  └─ README.md

```

---

## 포인트

- **데이터 모델링 이해도**  
  - 건강 상태·환경·생산·출하·마스터 코드 등 다수의 테이블을 `total_result` 뷰로 통합하여, 분석 친화적인 형태로 가공

- **엔드 투 엔드 파이프라인 경험**  
  - PostgreSQL → Flask API/뷰 → Tailwind & Chart.js & Folium 프런트엔드까지 하나의 흐름으로 구현

- **UX / UI 감각**  
  - 파스텔톤 컬러, 캡슐 배지, 카드뷰 구성으로 실서비스 수준의 친숙한 UI 지향

- **바이브코딩(Vibe Coding) 기반 개발**  
  - AI 코딩 어시스턴트와 함께 대화형으로 설계·코드를 다듬어 가며 제작한 프로젝트로,  
  - 문제 정의 → 데이터 모델 이해 → API/뷰 설계 → 시각화/UX 개선의 반복 사이클을 경험했습니다.

