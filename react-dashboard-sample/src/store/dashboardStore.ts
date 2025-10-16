import { create } from 'zustand';
import type { DashboardFilters, EvaluationRecord } from '../types/dashboard';
import { sampleRawData, sampleAggregatedData } from '../data/sampleData';

interface DashboardState {
  rawData: EvaluationRecord[];
  aggregatedData: typeof sampleAggregatedData;
  filters: DashboardFilters;
  setFilter: (key: keyof DashboardFilters, value: string | string[]) => void;
  resetFilters: () => void;
  getFilteredData: () => EvaluationRecord[];
}

const initialFilters: DashboardFilters = {
  year: '전체',
  division: '전체',
  department: '전체',
  unit: '전체',
  sentiment: ['전체'],
  scoreType: '종합점수'
};

export const useDashboardStore = create<DashboardState>((set, get) => ({
  rawData: sampleRawData,
  aggregatedData: sampleAggregatedData,
  filters: initialFilters,

  setFilter: (key, value) => {
    set((state) => ({
      filters: { ...state.filters, [key]: value }
    }));
  },

  resetFilters: () => {
    set({ filters: initialFilters });
  },

  getFilteredData: () => {
    const { rawData, filters } = get();

    return rawData.filter((item) => {
      if (filters.year !== '전체' && item.기간_표시 !== filters.year) return false;
      if (filters.division !== '전체' && item.피평가부문 !== filters.division) return false;
      if (filters.department !== '전체' && item.피평가부서 !== filters.department) return false;
      if (filters.unit !== '전체' && item.피평가Unit !== filters.unit) return false;
      if (!filters.sentiment.includes('전체') && !filters.sentiment.includes(item.감정_분류)) return false;
      return true;
    });
  }
}));
