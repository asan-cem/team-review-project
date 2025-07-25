# 서울아산병원 협업평가 시스템

> AI 기반 의료진 협업 피드백 분석 및 대시보드 시스템

## 프로젝트 개요

이 시스템은 서울아산병원의 부서간 협업 평가 설문 데이터를 AI로 분석하고, 인터랙티브 대시보드로 시각화합니다.

### 주요 기능
- **데이터 전처리**: 설문 원본 데이터 정제 및 표준화
- **AI 텍스트 분석**: Google Gemini를 활용한 감정 분석 및 키워드 추출
- **대시보드 생성**: 인터랙티브 HTML 대시보드 자동 생성
- **부서별 리포트**: 각 부서별 상세 분석 리포트 제공

## 프로젝트 구조

```
team-review-project/
│
├── 핵심 처리 스크립트/
│   ├── 0. setup.py                    # 초기 환경 설정 스크립트
│   ├── 1. data_processor.py           # 설문 데이터 전처리
│   ├── 2. text_processor.py           # AI 텍스트 분석 (Google Vertex AI)
│   ├── 3. build_dashboard_html.py     # 통합 대시보드 생성
│   └── 4. team_reports.py             # 부서별 개별 리포트 생성
│
├── 데이터 폴더/
│   └── rawdata/                       # 원본 데이터 및 처리 결과
│       ├── 설문조사진행현황[VCRCRIC120S]_YYYY_N.xlsx  # 원본 설문 데이터
│       ├── 부서_부문_매핑.xlsx         # 부서-부문 매핑 테이블
│       ├── 부서명_표준화_매핑.xlsx     # 부서명 표준화 매핑
│       ├── 1. data_processor_결과_*.xlsx   # 전처리 결과
│       └── 2. text_processor_결과_*.xlsx   # AI 분석 결과
│
├── 결과물 폴더/
│   ├── generated_reports/             # 생성된 부서별 리포트
│   │   └── reports_YYYYMMDD_HHMMSS/   # 타임스탬프별 리포트 세트
│   │       ├── 간호부문/              # 부문별 폴더
│   │       ├── 관리부문/
│   │       ├── 진료부문/
│   │       └── ...
│   └── 서울아산병원 협업평가 결과.html # 통합 대시보드
│
├── 기타 스크립트/
│   ├── summarize_mutual_reviews.py    # 상호 평가 요약 (보조)
│   └── update_notion_formatted.py     # Notion 포맷 업데이트 (보조)
│
└── 설정 파일/
    ├── requirements.txt               # Python 패키지 의존성
    ├── README.md                      # 프로젝트 문서 (현재 파일)
    └── .gitignore                     # Git 제외 파일

```

## 시작하기

### 1. 사전 요구사항

- Python 3.8 이상
- Google Cloud 계정 (Vertex AI API 사용)
- 최소 8GB RAM
- 인터넷 연결 (AI API 호출)

### 2. 설치 방법

```bash
# 저장소 클론
git clone https://github.com/your-repo/team-review-project.git
cd team-review-project

# 환경 설정 (가상환경 생성 및 패키지 설치)
python 0. setup.py

# 가상환경 활성화
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate
```

### 3. Google Cloud 설정

1. Google Cloud Console에서 프로젝트 생성
2. Vertex AI API 활성화
3. 서비스 계정 생성 및 키 다운로드
4. 환경변수 설정:
```bash
export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/service-account-key.json"
```

## 사용 방법

### 전체 프로세스 실행

```bash
# 1단계: 데이터 전처리
python "1. data_processor.py"

# 2단계: AI 텍스트 분석 (선택사항)
python "2. text_processor.py"

# 3단계: 대시보드 생성
python "3. build_dashboard_html.py"

# 4단계: 부서별 리포트 생성 (선택사항)
python "4. team_reports.py"

# 또는 진료부문 버전2 실행 (방사성의약품제조소 제외)
python "4. team_reports.py" clinical_v2
```

### 각 단계별 설명

#### 1. 데이터 전처리 (data_processor.py)
- **입력**: `rawdata/설문조사진행현황[VCRCRIC120S]_*.xlsx`
- **처리**: 
  - 부서명 표준화
  - 부문 매핑
  - 점수 변환 (5점 → 100점)
  - 데이터 품질 검증
- **출력**: `rawdata/1. data_processor_결과_YYYYMMDD_HHMMSS.xlsx`

#### 2. AI 텍스트 분석 (text_processor.py)
- **입력**: data_processor 결과 파일
- **처리**:
  - 협업 후기 텍스트 분석
  - 감정 분류 (긍정/부정/중립)
  - 키워드 추출
  - 비식별화 처리
- **출력**: `rawdata/2. text_processor_결과_YYYYMMDD_HHMMSS.xlsx`
- **참고**: Google Vertex AI 비용이 발생합니다

#### 3. 통합 대시보드 생성 (build_dashboard_html.py)
- **입력**: 전처리된 데이터 (AI 분석은 선택사항)
- **처리**: 인터랙티브 차트 및 분석 생성
- **출력**: `서울아산병원 협업평가 결과.html`

#### 4. 부서별 리포트 생성 (team_reports.py)
- **입력**: 전처리된 데이터
- **처리**: 각 부서별 상세 분석
- **출력**: `generated_reports/reports_*/부문명/부서별HTML파일`
- **실행 옵션**:
  - 기본 실행: `python "4. team_reports.py"` - 전체 76개 부서 보고서 생성
  - 진료부문 v2: `python "4. team_reports.py" clinical_v2` - 진료부문 22개 부서만 (방사성의약품제조소 제외)

## 주요 기능 상세

### AI 분석 기능
- **감정 분석**: 8가지 세분화된 감정 분류
- **감정 강도**: 1-10점 척도
- **키워드 추출**: 주요 키워드 3-5개
- **의료 맥락**: 의료 서비스, 업무 효율, 존중/소통, 전문성
- **비식별화**: 부정적 피드백의 개인정보 자동 처리

### 대시보드 구성요소
1. **전체 병원 현황**: 종합 점수 및 추이
2. **부문별 분석**: 부문간 비교 차트
3. **부서별 순위**: 상위/하위 부서
4. **감정 분석**: 감정 분포 및 키워드 클라우드
5. **상세 피드백**: 필터링 가능한 피드백 테이블

## 데이터 파일 설명

### 입력 데이터
- **설문조사진행현황**: 연도별/차수별 설문 원본 데이터
- **부서_부문_매핑.xlsx**: 부서를 부문으로 분류하는 매핑 테이블
- **부서명_표준화_매핑.xlsx**: 변경된 부서명을 표준화하는 매핑

### 출력 데이터
- **전처리 결과**: 표준화되고 정제된 설문 데이터
- **AI 분석 결과**: 텍스트 분석이 추가된 데이터
- **HTML 대시보드**: 웹브라우저에서 볼 수 있는 인터랙티브 리포트

## 문제 해결

### 일반적인 오류 해결

1. **Google Cloud 인증 오류**
   ```bash
   # 인증 확인
   gcloud auth application-default login
   # 또는 서비스 계정 키 경로 확인
   echo $GOOGLE_APPLICATION_CREDENTIALS
   ```

2. **패키지 설치 오류**
   ```bash
   # pip 업그레이드
   pip install --upgrade pip
   # 패키지 재설치
   pip install -r requirements.txt --force-reinstall
   ```

3. **메모리 부족**
   - text_processor.py의 BATCH_SIZE를 줄이기 (기본값: 10)
   - 데이터를 연도별로 나누어 처리

### 로그 파일
- 오류 발생시 콘솔 출력 확인
- AI 분석 중단시 checkpoints 폴더에서 재개 가능

## 성능 및 처리 시간

- **데이터 전처리**: 약 1-2분 (38,000건 기준)
- **AI 분석**: 약 20-40분 (텍스트 수에 따라 변동)
- **대시보드 생성**: 약 1-2분
- **부서별 리포트**: 약 5-10분

## 주의사항

1. **데이터 보안**: 의료 데이터는 민감정보이므로 보안 주의
2. **API 비용**: Google Vertex AI는 사용량에 따라 과금
3. **브라우저 호환성**: Chrome, Edge, Safari 최신 버전 권장
4. **파일 크기**: 생성된 HTML 파일이 클 수 있음 (10-50MB)

## 기여 방법

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## 문의 및 지원

- **이슈 제출**: GitHub Issues 사용
- **개선 제안**: Pull Request 환영
- **최종 업데이트**: 2025년 7월

## 최근 변경사항 (2025년 7월 25일)

### 진료부문 버전2 추가
- **요청자**: 핵의학팀장님
- **변경사항**: 진료부문 보고서에서 방사성의약품제조소를 제외한 버전 추가
- **적용범위**: 
  - 진료부문 v2 실행 시 방사성의약품제조소가 섹션 4(부문별 팀 점수 순위)에서 제외됨
  - 총 23개 부서 중 22개 부서만 표시
  - 종합점수 계산에는 포함되며, 차트 표시에서만 제외
- **실행방법**: `python "4. team_reports.py" clinical_v2`
- **출력폴더**: `generated_reports/진료부문_v2_YYYYMMDD_HHMMSS/`

### Context7 MCP 연결 문제
- **증상**: Context7 API 연결 실패 (DNS 해석 불가)
- **원인**: `api.context7.ai` 도메인이 내부 DNS에서 해석되지 않음
- **해결방안**: IT팀에 DNS 허용 요청 필요

---

*서울아산병원 협업평가 시스템 - 더 나은 의료 협업 문화를 위하여*