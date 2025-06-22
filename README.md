# 리뷰 분석 시스템

직원 만족도 및 협업 피드백을 분석하는 AI 기반 시스템입니다.

## 기능

- **텍스트 정제**: 오타 및 문법 교정
- **감정 분석**: 긍정/부정/중립 분류
- **익명화 처리**: 부정적 피드백의 개인정보 보호
- **카테고리 분류**: 5가지 협업 이슈 카테고리 자동 태깅
- **CSV 일괄 처리**: 대용량 리뷰 데이터 처리

## 지원 모델

1. **Google Vertex AI** (main.py)
   - Gemini 2.0 Flash
   - 프로젝트 ID: mindmap-462708
   - 리전: us-central1

2. **Claude API** (process_with_claude.py)
   - Claude 3.5 Sonnet
   - API 키 기반 접근

## 설치

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. Google Cloud 설정 (Vertex AI 사용 시)

```bash
# Google Cloud SDK 설치
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# 인증 설정
gcloud auth application-default login

# 프로젝트 설정
gcloud config set project mindmap-462708

# Vertex AI API 활성화
gcloud services enable aiplatform.googleapis.com
```

### 3. Claude API 설정 (Claude 사용 시)

```bash
export ANTHROPIC_API_KEY='your-api-key-here'
```

## 사용법

### Vertex AI로 처리

```bash
python main.py
```

### Claude API로 처리

```bash
python process_with_claude.py
```

## 입력 형식

CSV 파일 (`reviews_original.csv`)에 다음 열이 필요합니다:
- `original_review`: 원본 리뷰 텍스트

## 출력 형식

처리된 결과는 다음 열을 포함합니다:
- `original_text`: 원본 텍스트
- `refined_text`: 정제된 텍스트
- `is_anonymized`: 익명화 여부 (true/false)
- `sentiment`: 감정 (긍정/부정/중립)
- `labels`: 카테고리 라벨 배열

## 카테고리

1. **부서간 협업**: 서로 다른 부서/팀 간의 업무 연계와 협력 문제
2. **직원간 소통**: 같은 부서/팀 내 동료 간의 소통 및 관계 문제
3. **전문성 부족**: 개인의 업무 지식, 기술, 경험 부족 문제
4. **업무 태도**: 책임감, 적극성 등 업무를 대하는 자세 문제
5. **상호 존중**: 인격적 대우, 배려 등 관계에서의 예의 문제

## 익명화 규칙

**비식별 처리 조건**:
- 부정적 피드백이면서
- 실명 명시 (예: "김민희 직원") 또는
- 특정 직책 (예: "팀장", "과장", "대리") 또는
- 소수 식별 가능 호칭 (예: "여자 직원", "유엠")

**비식별 처리 제외**:
- 긍정적/중립적 피드백
- 일반적 호칭 ("선생님", "직원분", "담당자")

## 파일 구조

```
python-project/
├── main.py                     # Vertex AI 기반 처리
├── process_with_claude.py      # Claude API 기반 처리
├── requirements.txt            # Python 의존성
├── reviews_original.csv        # 입력 데이터
├── intro_gemini_2_0_flash.ipynb # Gemini 2.0 참조 문서
└── README.md                   # 프로젝트 설명
```

## 예시

### 입력
```
original_review
"김철수 팀장이 불친절해서 기분이 나빴습니다"
"선생님들이 항상 도움을 많이 주셔서 감사합니다"
```

### 출력
```csv
original_text,refined_text,is_anonymized,sentiment,labels
"김철수 팀장이 불친절해서 기분이 나빴습니다","담당자의 태도가 다소 불친절하여 불편함을 느꼈습니다",true,부정,"['상호 존중']"
"선생님들이 항상 도움을 많이 주셔서 감사합니다","선생님들이 항상 도움을 많이 주셔서 감사합니다",false,긍정,"['업무 태도']"
```

## 라이선스

MIT License