빠른 분석
/sc:analyze src/ --focus quality          # Quick quality check
/sc:analyze --uc --focus security         # Fast security scan


심층 조사
/sc:troubleshoot "bug" --think --seq      # Systematic debugging
/sc:analyze --think-hard --focus architecture  # Architectural analysis

학습 및 문서화
/sc:explain React hooks --c7 --verbose    # Detailed explanation with docs
/sc:document api/ --persona-scribe        # Professional documentation

기능 개발 
/sc:design new-feature --persona-architect --c7
/sc:build --magic --persona-frontend --validate
/sc:test --play --coverage
/sc:document --persona-scribe --c7

잘 작동하는 플래그 조합

#Safe improvement
--safe-mode --validate --preview

#Deep analysis  
--think --seq --c7

#Large project
--delegate auto --uc --focus

#Learning
--verbose --c7 --persona-mentor

#Security work
--persona-security --focus security --validate

#Performance work
--persona-performance --focus performance --play


## 📋 Plan.md - # 7. Deployment Preparation

### # 1. Project Planning
```bash
/sc:design --api --ddd --plan --persona-architect
```

### # 2. Frontend Development
```bash
/sc:build --react --magic --tdd --persona-frontend
```

### # 3. Backend Development
```bash
/sc:build --api --tdd --coverage --persona-backend
```

### # 4. Quality Check
```bash
/sc:review --quality --evidence --persona-qa
```

### # 5. Security Scan
```bash
/sc:scan --security --owasp --persona-security
```

### # 6. Performance Optimization
```bash
/sc:improve --performance --iterate --persona-performance
```

---

## 🔍 Troubleshoot.md - # 1. Problem Analysis

### # 1. Problem Analysis
💡
```bash
/sc:troubleshoot --investigate --prod --persona-analyzer
```

### # 2. Root Cause Analysis
```bash
/sc:troubleshoot --prod --five-whys --seq --persona-analyzer
```

### # 3. Performance Analysis
```bash
/sc:analyze --profile --perf --seq --persona-performance
```

### # 4. Fix Implementation
```bash
/sc:improve --quality --threshold 95% --persona-refactorer
```

---

## 📌 Summary

이 문서는 두 가지 주요 워크플로우를 다룹니다:

1. **Deployment Preparation (배포 준비)**
   - 프로젝트 계획부터 성능 최적화까지의 전체 개발 라이프사이클
   - 각 단계별 전문 페르소나 활용

2. **Problem Analysis (문제 분석)**
   - 프로덕션 환경의 문제 조사 및 해결
   - 체계적인 원인 분석과 개선 구현

각 명령어는 특정 페르소나와 함께 사용되어 해당 도메인의 전문성을 활용합니다.