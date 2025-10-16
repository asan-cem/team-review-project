import React, { useMemo, useState } from 'react';
import { useDashboardStore } from '../store/dashboardStore';
import { FilterSelect } from './FilterSelect';

export const Section5CollaborationReviews: React.FC = () => {
  const { filters, setFilter, getFilteredData, aggregatedData } = useDashboardStore();
  const [selectedSentiments, setSelectedSentiments] = useState<string[]>(['전체']);

  const yearOptions = ['전체', ...Object.keys(aggregatedData.hospital.yearly)];

  const reviews = useMemo(() => {
    const filteredData = getFilteredData();

    return filteredData
      .filter(item => {
        if (selectedSentiments.includes('전체')) return true;
        return selectedSentiments.includes(item.감정_분류);
      })
      .filter(item => item.정제된_텍스트 && item.정제된_텍스트 !== 'N/A')
      .map(item => ({
        year: item.기간_표시,
        review: item.정제된_텍스트,
        sentiment: item.감정_분류
      }))
      .slice(0, 1000); // 샘플이므로 최대 1000건으로 제한
  }, [getFilteredData, filters, selectedSentiments]);

  const handleSentimentChange = (sentiment: string) => {
    if (sentiment === '전체') {
      setSelectedSentiments(['전체']);
    } else {
      let newSentiments = selectedSentiments.filter(s => s !== '전체');
      if (newSentiments.includes(sentiment)) {
        newSentiments = newSentiments.filter(s => s !== sentiment);
      } else {
        newSentiments.push(sentiment);
      }
      if (newSentiments.length === 0) {
        newSentiments = ['전체'];
      }
      setSelectedSentiments(newSentiments);
    }
  };

  const getSentimentColor = (sentiment: string) => {
    switch (sentiment) {
      case '긍정': return '#28a745';
      case '부정': return '#dc3545';
      case '중립': return '#6c757d';
      default: return '#6c757d';
    }
  };

  return (
    <div className="section">
      <h2>5. 협업 후기 <span className="reviews-count">({reviews.length}건)</span></h2>

      <div className="filters">
        <FilterSelect
          label="연도 선택"
          value={filters.year}
          options={yearOptions}
          onChange={(value) => setFilter('year', value)}
        />
      </div>

      <div className="sentiment-filter">
        <label>
          <input
            type="checkbox"
            checked={selectedSentiments.includes('전체')}
            onChange={() => handleSentimentChange('전체')}
          />
          전체
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedSentiments.includes('긍정')}
            onChange={() => handleSentimentChange('긍정')}
          />
          <span style={{ color: '#28a745' }}>긍정</span>
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedSentiments.includes('중립')}
            onChange={() => handleSentimentChange('중립')}
          />
          <span style={{ color: '#6c757d' }}>중립</span>
        </label>
        <label>
          <input
            type="checkbox"
            checked={selectedSentiments.includes('부정')}
            onChange={() => handleSentimentChange('부정')}
          />
          <span style={{ color: '#dc3545' }}>부정</span>
        </label>
      </div>

      <div className="reviews-table-container">
        {reviews.length > 0 ? (
          <table>
            <thead>
              <tr>
                <th style={{ width: '120px' }}>연도</th>
                <th>후기 내용</th>
              </tr>
            </thead>
            <tbody>
              {reviews.map((review, idx) => (
                <tr key={idx}>
                  <td style={{ color: '#6c757d' }}>{review.year}</td>
                  <td>
                    {review.review}{' '}
                    <span style={{ color: getSentimentColor(review.sentiment), fontSize: '0.9em', fontWeight: 'bold' }}>
                      [{review.sentiment}]
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div style={{ padding: '40px', textAlign: 'center', color: '#6c757d' }}>
            해당 조건의 후기가 없습니다.
          </div>
        )}
      </div>
    </div>
  );
};
