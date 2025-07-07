import pandas as pd
import numpy as np
from datetime import datetime

def create_executive_collaboration_dashboard():
    """
    경영진 대상 협업 분석 대시보드 생성
    - 핵심 지표 요약
    - 전략적 인사이트
    - 트렌드 분석
    - 액션 아이템 제안
    """
    print("🎯 경영진 대상 협업 분석 대시보드 생성을 시작합니다...")

    # 1. 데이터 로드
    try:
        df = pd.read_excel("설문조사_전처리데이터_20250620_0731_processed.xlsx")
        print("✅ 데이터 로드 완료")
    except FileNotFoundError:
        print("❌ 데이터 파일을 찾을 수 없습니다.")
        return

    # 2. 컬럼명 설정
    original_cols = [
        'response_id', '설문연도', '평가부서', '평가부서_원본', '평가Unit', '평가부문',
        '피평가부서', '피평가부서_원본', '피평가Unit', '피평가부문',
        '존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합 점수',
        '극단값', '결측값', '협업내용', '협업내용상세', '협업후기', '정제된_텍스트', 
        '비식별_처리', '감정_분류', '감정_강도_점수', '핵심_키워드', '의료_맥락', '신뢰도_점수'
    ]
    df.columns = original_cols

    # 3. 데이터 전처리
    df['설문연도'] = df['설문연도'].astype(str)
    df.dropna(subset=['평가부서', '피평가부서', '종합 점수'], inplace=True)
    
    # 4. 핵심 지표 계산
    total_evaluations = len(df)
    unique_departments = len(set(df['평가부서'].unique()) | set(df['피평가부서'].unique()))
    unique_relationships = len(df.groupby(['평가부서', '피평가부서']).size())
    avg_satisfaction = df['종합 점수'].mean()
    
    # 연도별 통계
    yearly_stats = df.groupby('설문연도').agg({
        '종합 점수': ['mean', 'count'],
        '감정_분류': lambda x: (x == '긍정').sum() / len(x) * 100
    }).round(2)
    
    # 5. 협업 허브 부서 분석
    dept_outbound = df.groupby('평가부서').agg({
        '피평가부서': 'nunique',
        '종합 점수': 'mean'
    }).rename(columns={'피평가부서': '협업_부서수', '종합 점수': '평가_평균점수'})
    
    dept_inbound = df.groupby('피평가부서').agg({
        '평가부서': 'nunique',
        '종합 점수': 'mean'
    }).rename(columns={'평가부서': '평가받은_부서수', '종합 점수': '받은_평균점수'})
    
    # 허브 부서 종합 분석
    hub_analysis = pd.merge(dept_outbound, dept_inbound, left_index=True, right_index=True, how='outer').fillna(0)
    hub_analysis['총_협업_관계수'] = hub_analysis['협업_부서수'] + hub_analysis['평가받은_부서수']
    hub_analysis['협업_균형도'] = abs(hub_analysis['협업_부서수'] - hub_analysis['평가받은_부서수'])
    hub_analysis['종합_만족도'] = (hub_analysis['평가_평균점수'] + hub_analysis['받은_평균점수']) / 2
    
    # 6. 협업 품질 분석
    quality_analysis = df.groupby(['평가부서', '피평가부서']).agg({
        '종합 점수': ['mean', 'count'],
        '감정_분류': lambda x: (x == '긍정').sum() / len(x) * 100 if len(x) > 0 else 0
    }).round(2)
    
    quality_analysis.columns = ['평균_점수', '평가_횟수', '긍정_비율']
    quality_analysis = quality_analysis.reset_index()
    
    # 7. 연도별 트렌드 분석
    trend_analysis = df.groupby(['설문연도', '평가부서']).agg({
        '피평가부서': 'nunique',
        '종합 점수': 'mean',
        '감정_분류': lambda x: (x == '긍정').sum() / len(x) * 100 if len(x) > 0 else 0
    }).reset_index()
    trend_analysis.columns = ['연도', '부서', '협업_부서수', '평균_점수', '긍정_비율']
    
    # 8. 결과 저장
    output_filename = "경영진_협업_대시보드.xlsx"
    
    with pd.ExcelWriter(output_filename, engine='openpyxl') as writer:
        
        # 🎯 시트 1: 경영진 요약 대시보드
        dashboard_data = {
            '지표': [
                '📊 전체 평가 건수',
                '🏢 전체 부서 수',
                '🤝 고유 협업 관계 수',
                '⭐ 전체 평균 만족도',
                '📈 최신년도 만족도',
                '🔄 연평균 평가 증가율',
                '😊 긍정 평가 비율',
                '🏆 최고 협업 부서',
                '⚠️ 개선 필요 부서 수',
                '💡 신규 협업 기회'
            ],
            '수치': [
                f"{total_evaluations:,}건",
                f"{unique_departments}개",
                f"{unique_relationships}개",
                f"{avg_satisfaction:.1f}점",
                f"{yearly_stats.iloc[-1][('종합 점수', 'mean')]:.1f}점",
                f"{((yearly_stats.iloc[-1][('종합 점수', 'count')] / yearly_stats.iloc[0][('종합 점수', 'count')]) ** (1/3) - 1) * 100:.1f}%",
                f"{df[df['감정_분류'] == '긍정'].shape[0] / df['감정_분류'].notna().sum() * 100:.1f}%",
                hub_analysis.nlargest(1, '총_협업_관계수').index[0],
                f"{len(hub_analysis[hub_analysis['종합_만족도'] < 70])}개",
                f"{len(hub_analysis[hub_analysis['협업_균형도'] > 10])}개"
            ],
            '전년대비': [
                f"+{((yearly_stats.iloc[-1][('종합 점수', 'count')] / yearly_stats.iloc[-2][('종합 점수', 'count')]) - 1) * 100:.1f}%",
                "-",
                "-",
                f"{yearly_stats.iloc[-1][('종합 점수', 'mean')] - yearly_stats.iloc[-2][('종합 점수', 'mean')]:+.1f}점",
                "-",
                "-",
                f"{yearly_stats.iloc[-1][('감정_분류', '<lambda>')] - yearly_stats.iloc[-2][('감정_분류', '<lambda>')]:+.1f}%",
                "-",
                "-",
                "-"
            ]
        }
        
        dashboard_df = pd.DataFrame(dashboard_data)
        dashboard_df.to_excel(writer, sheet_name='📊 경영진 대시보드', index=False)
        
        # 🏆 시트 2: 협업 허브 부서 (상위 20개)
        top_hubs = hub_analysis.nlargest(20, '총_협업_관계수').round(2)
        top_hubs['순위'] = range(1, len(top_hubs) + 1)
        top_hubs = top_hubs[['순위', '총_협업_관계수', '협업_부서수', '평가받은_부서수', '종합_만족도', '협업_균형도']]
        top_hubs.to_excel(writer, sheet_name='🏆 협업 허브 부서', index=True)
        
        # ⚠️ 시트 3: 협업 개선 필요 부서
        improvement_needed = hub_analysis[
            (hub_analysis['종합_만족도'] < 70) | 
            (hub_analysis['총_협업_관계수'] < 5)
        ].round(2)
        improvement_needed['개선_유형'] = improvement_needed.apply(
            lambda x: '만족도 개선' if x['종합_만족도'] < 70 else '협업 확대', axis=1
        )
        improvement_needed.to_excel(writer, sheet_name='⚠️ 개선 필요 부서', index=True)
        
        # 📈 시트 4: 연도별 트렌드
        yearly_pivot = trend_analysis.pivot_table(
            index='연도', 
            values=['협업_부서수', '평균_점수', '긍정_비율'], 
            aggfunc='mean'
        ).round(2)
        yearly_pivot.to_excel(writer, sheet_name='📈 연도별 트렌드', index=True)
        
        # 🔥 시트 5: 상위 협업 관계 (빈도 기준)
        top_relationships = quality_analysis.nlargest(30, '평가_횟수')
        top_relationships['순위'] = range(1, len(top_relationships) + 1)
        top_relationships = top_relationships[['순위', '평가부서', '피평가부서', '평가_횟수', '평균_점수', '긍정_비율']]
        top_relationships.to_excel(writer, sheet_name='🔥 상위 협업 관계', index=False)
        
        # 🎯 시트 6: 전략적 액션 아이템
        action_items = pd.DataFrame({
            '우선순위': ['높음', '높음', '보통', '보통', '낮음', '낮음'],
            '액션 아이템': [
                '협업 허브 부서 워크로드 분산 방안 검토',
                '협업 만족도 70점 미만 부서 개선 계획 수립',
                '부서간 협업 불균형 해소 방안 마련',
                '신규 협업 기회 발굴 및 매칭 프로그램 운영',
                '협업 우수 사례 전파 및 베스트 프랙티스 공유',
                '정기적 협업 모니터링 시스템 구축'
            ],
            '담당부서': ['인사팀', '인사팀', '기획팀', '기획팀', '교육팀', 'IT팀'],
            '예상기간': ['1개월', '2개월', '3개월', '6개월', '상시', '3개월']
        })
        action_items.to_excel(writer, sheet_name='🎯 전략적 액션 아이템', index=False)
        
        # 📊 시트 7: 부서별 협업 스코어카드
        scorecard = hub_analysis.copy()
        scorecard['협업_활성도'] = pd.cut(scorecard['총_협업_관계수'], 
                                    bins=[0, 10, 30, 50, 999], 
                                    labels=['낮음', '보통', '높음', '매우높음'])
        scorecard['만족도_등급'] = pd.cut(scorecard['종합_만족도'], 
                                    bins=[0, 65, 75, 85, 100], 
                                    labels=['개선필요', '보통', '양호', '우수'])
        scorecard = scorecard.round(2)
        scorecard.to_excel(writer, sheet_name='📊 부서별 스코어카드', index=True)

    print(f"\n🎉 경영진 대시보드 생성 완료!")
    print(f"📁 파일명: {output_filename}")
    print(f"📋 생성된 시트:")
    print(f"   📊 경영진 대시보드 - 핵심 지표 요약")
    print(f"   🏆 협업 허브 부서 - 상위 20개 부서")
    print(f"   ⚠️ 개선 필요 부서 - 협업 취약 부서")
    print(f"   📈 연도별 트렌드 - 4개년 변화 추이")
    print(f"   🔥 상위 협업 관계 - 빈도 기준 상위 30개")
    print(f"   🎯 전략적 액션 아이템 - 개선 방안 제안")
    print(f"   📊 부서별 스코어카드 - 종합 평가표")
    
    print(f"\n💡 주요 인사이트:")
    print(f"   • 총 {unique_departments}개 부서가 {unique_relationships}개 협업 관계 형성")
    print(f"   • 평균 협업 만족도 {avg_satisfaction:.1f}점")
    print(f"   • 협업 허브 부서: {hub_analysis.nlargest(1, '총_협업_관계수').index[0]}")
    print(f"   • 개선 필요 부서: {len(improvement_needed)}개")

if __name__ == "__main__":
    create_executive_collaboration_dashboard()