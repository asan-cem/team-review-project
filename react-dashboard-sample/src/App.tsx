import './App.css';
import { Section1HospitalOverview } from './components/Section1HospitalOverview';
import { Section2DivisionScores } from './components/Section2DivisionScores';
import { Section5CollaborationReviews } from './components/Section5CollaborationReviews';

function App() {
  return (
    <div>
      <header className="header">
        <h1>서울아산병원 협업평가 결과 대시보드</h1>
        <p>2022년 ~ 2025년 협업평가 종합 분석 (React 샘플)</p>
      </header>

      <div className="container">
        <Section1HospitalOverview />

        <div className="part-divider"></div>

        <Section2DivisionScores />

        <div className="part-divider"></div>

        <div className="part-title">
          ▶ PART 2: 협업 후기 및 키워드 분석
        </div>

        <Section5CollaborationReviews />

        <div style={{ padding: '40px 0', textAlign: 'center', color: '#6c757d' }}>
          <p>© 2025 Seoul Asan Medical Center - React Dashboard Sample</p>
          <p style={{ fontSize: '0.9em', marginTop: '10px' }}>
            본 대시보드는 원본 HTML 대시보드의 React 변환 샘플입니다.
          </p>
        </div>
      </div>
    </div>
  );
}

export default App;
