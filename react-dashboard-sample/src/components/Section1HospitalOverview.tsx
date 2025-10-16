import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useDashboardStore } from '../store/dashboardStore';
import { FilterSelect } from './FilterSelect';

export const Section1HospitalOverview: React.FC = () => {
  const { aggregatedData, filters, setFilter } = useDashboardStore();

  const yearOptions = ['전체', ...Object.keys(aggregatedData.hospital.yearly)];

  const metrics = useMemo(() => {
    if (filters.year === '전체') {
      const allYears = Object.values(aggregatedData.hospital.yearly);
      const totalCount = allYears.reduce((sum, year) => sum + year.count, 0);
      const avgScores = {
        존중배려: allYears.reduce((sum, y) => sum + y.존중배려 * y.count, 0) / totalCount,
        정보공유: allYears.reduce((sum, y) => sum + y.정보공유 * y.count, 0) / totalCount,
        명확처리: allYears.reduce((sum, y) => sum + y.명확처리 * y.count, 0) / totalCount,
        태도개선: allYears.reduce((sum, y) => sum + y.태도개선 * y.count, 0) / totalCount,
        전반만족: allYears.reduce((sum, y) => sum + y.전반만족 * y.count, 0) / totalCount,
        종합점수: allYears.reduce((sum, y) => sum + y.종합점수 * y.count, 0) / totalCount
      };
      return { ...avgScores, count: totalCount };
    }
    return aggregatedData.hospital.yearly[filters.year] || {
      존중배려: 0, 정보공유: 0, 명확처리: 0, 태도개선: 0, 전반만족: 0, 종합점수: 0, count: 0
    };
  }, [aggregatedData, filters.year]);

  const chartData = useMemo(() => {
    const years = Object.keys(aggregatedData.hospital.yearly);
    const scoreTypes = ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족', '종합점수'] as const;

    return scoreTypes.map(scoreType => ({
      x: years,
      y: years.map(year => aggregatedData.hospital.yearly[year][scoreType]),
      name: scoreType,
      type: 'scatter',
      mode: 'lines+markers',
      line: { width: 2 },
      marker: { size: 8 }
    }));
  }, [aggregatedData]);

  return (
    <div className="section">
      <h2>1. 병원 전체 협업평가 결과</h2>

      <div className="filters">
        <FilterSelect
          label="연도 선택"
          value={filters.year}
          options={yearOptions}
          onChange={(value) => setFilter('year', value)}
        />
      </div>

      <div className="metrics-container">
        <div className="metric-card">
          <h3>존중배려</h3>
          <div className="value">{metrics.존중배려.toFixed(2)}</div>
          <div className="count">{metrics.count.toLocaleString()}건</div>
        </div>
        <div className="metric-card">
          <h3>정보공유</h3>
          <div className="value">{metrics.정보공유.toFixed(2)}</div>
          <div className="count">{metrics.count.toLocaleString()}건</div>
        </div>
        <div className="metric-card">
          <h3>명확처리</h3>
          <div className="value">{metrics.명확처리.toFixed(2)}</div>
          <div className="count">{metrics.count.toLocaleString()}건</div>
        </div>
        <div className="metric-card">
          <h3>태도개선</h3>
          <div className="value">{metrics.태도개선.toFixed(2)}</div>
          <div className="count">{metrics.count.toLocaleString()}건</div>
        </div>
        <div className="metric-card">
          <h3>전반만족</h3>
          <div className="value">{metrics.전반만족.toFixed(2)}</div>
          <div className="count">{metrics.count.toLocaleString()}건</div>
        </div>
        <div className="metric-card">
          <h3>종합점수</h3>
          <div className="value">{metrics.종합점수.toFixed(2)}</div>
          <div className="count">{metrics.count.toLocaleString()}건</div>
        </div>
      </div>

      <div className="chart-container">
        <Plot
          data={chartData as any}
          layout={{
            title: { text: '연도별 협업 점수 추이' },
            xaxis: { title: { text: '기간' } },
            yaxis: { title: { text: '점수' }, range: [0, 5] },
            hovermode: 'closest',
            showlegend: true,
            legend: { orientation: 'h', y: -0.2 },
            autosize: true
          } as any}
          style={{ width: '100%', height: '500px' }}
          config={{ responsive: true, displayModeBar: false }}
        />
      </div>
    </div>
  );
};
