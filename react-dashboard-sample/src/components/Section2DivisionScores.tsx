import React, { useMemo } from 'react';
import Plot from 'react-plotly.js';
import { useDashboardStore } from '../store/dashboardStore';
import { FilterSelect } from './FilterSelect';

export const Section2DivisionScores: React.FC = () => {
  const { aggregatedData, filters, setFilter } = useDashboardStore();

  const yearOptions = ['전체', ...Object.keys(aggregatedData.hospital.yearly)];
  const divisionOptions = ['전체', ...Object.keys(aggregatedData.divisions)];

  const radarData = useMemo(() => {
    if (filters.division === '전체') {
      return divisionOptions
        .filter(d => d !== '전체')
        .map(division => {
          const divisionData = aggregatedData.divisions[division];
          const years = Object.keys(divisionData);
          const yearData = filters.year === '전체' || !divisionData[filters.year]
            ? divisionData[years[years.length - 1]]
            : divisionData[filters.year];

          return {
            type: 'scatterpolar',
            r: [
              yearData.존중배려,
              yearData.정보공유,
              yearData.명확처리,
              yearData.태도개선,
              yearData.전반만족
            ],
            theta: ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족'],
            fill: 'toself',
            name: division
          };
        });
    } else {
      const divisionData = aggregatedData.divisions[filters.division];
      if (!divisionData) return [];

      const years = Object.keys(divisionData);
      const yearData = filters.year === '전체' || !divisionData[filters.year]
        ? divisionData[years[years.length - 1]]
        : divisionData[filters.year];

      return [{
        type: 'scatterpolar',
        r: [
          yearData.존중배려,
          yearData.정보공유,
          yearData.명확처리,
          yearData.태도개선,
          yearData.전반만족
        ],
        theta: ['존중배려', '정보공유', '명확처리', '태도개선', '전반만족'],
        fill: 'toself',
        name: filters.division
      }];
    }
  }, [aggregatedData, filters.year, filters.division, divisionOptions]);

  const tableData = useMemo(() => {
    if (filters.division === '전체') {
      return Object.entries(aggregatedData.divisions).map(([division, years]) => {
        const yearData = filters.year === '전체' || !years[filters.year]
          ? years[Object.keys(years)[Object.keys(years).length - 1]]
          : years[filters.year];

        return {
          부문: division,
          ...yearData
        };
      });
    }

    const divisionData = aggregatedData.divisions[filters.division];
    if (!divisionData) return [];

    return Object.entries(divisionData).map(([year, data]) => ({
      부문: year,
      ...data
    }));
  }, [aggregatedData, filters.year, filters.division]);

  return (
    <div className="section">
      <h2>2. 부문별 종합 점수</h2>

      <div className="filters">
        <FilterSelect
          label="연도 선택"
          value={filters.year}
          options={yearOptions}
          onChange={(value) => setFilter('year', value)}
        />
        <FilterSelect
          label="부문 선택"
          value={filters.division}
          options={divisionOptions}
          onChange={(value) => setFilter('division', value)}
        />
      </div>

      <div className="chart-container">
        <Plot
          data={radarData as any}
          layout={{
            polar: {
              radialaxis: {
                visible: true,
                range: [0, 5]
              }
            },
            showlegend: true,
            title: { text: '부문별 5개 평가 항목 비교 (레이더 차트)' },
            autosize: true
          } as any}
          style={{ width: '100%', height: '500px' }}
          config={{ responsive: true, displayModeBar: false }}
        />
      </div>

      <div className="table-container">
        <table>
          <thead>
            <tr>
              <th>부문/연도</th>
              <th>존중배려</th>
              <th>정보공유</th>
              <th>명확처리</th>
              <th>태도개선</th>
              <th>전반만족</th>
              <th>종합점수</th>
              <th>평가건수</th>
            </tr>
          </thead>
          <tbody>
            {tableData.map((row, idx) => (
              <tr key={idx}>
                <td>{row.부문}</td>
                <td>{row.존중배려.toFixed(2)}</td>
                <td>{row.정보공유.toFixed(2)}</td>
                <td>{row.명확처리.toFixed(2)}</td>
                <td>{row.태도개선.toFixed(2)}</td>
                <td>{row.전반만족.toFixed(2)}</td>
                <td><strong>{row.종합점수.toFixed(2)}</strong></td>
                <td>{row.count.toLocaleString()}건</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};
