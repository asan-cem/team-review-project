// 대시보드 데이터 타입 정의

export interface EvaluationRecord {
  response_id: string;
  설문시행연도: string;
  기간_표시: string;
  평가부서: string;
  평가부문: string;
  피평가부서: string;
  피평가부문: string;
  피평가Unit: string;
  존중배려: number;
  정보공유: number;
  명확처리: number;
  태도개선: number;
  전반만족: number;
  종합점수: number;
  정제된_텍스트: string;
  감정_분류: '긍정' | '부정' | '중립';
  핵심_키워드: string[];
}

export interface AggregatedData {
  hospital: {
    yearly: {
      [year: string]: {
        존중배려: number;
        정보공유: number;
        명확처리: number;
        태도개선: number;
        전반만족: number;
        종합점수: number;
        count: number;
      };
    };
  };
  divisions: {
    [division: string]: {
      [year: string]: {
        존중배려: number;
        정보공유: number;
        명확처리: number;
        태도개선: number;
        전반만족: number;
        종합점수: number;
        count: number;
      };
    };
  };
}

export interface DashboardFilters {
  year: string;
  division: string;
  department: string;
  unit: string;
  sentiment: string[];
  scoreType: string;
}
