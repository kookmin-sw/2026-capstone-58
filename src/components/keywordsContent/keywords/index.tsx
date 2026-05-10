import { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import cloud from 'd3-cloud';
import useKeywordStore from '@/stores/useKeywordStore';

interface KeywordData {
  text: string;
  value: number;
}

// 임시 데이터 (TOP 100 키워드)
const mockKeywords: KeywordData[] = [
  { text: '게임', value: 4422776 },
  { text: '리그 오브 레전드', value: 3071670 },
  { text: '에스파', value: 1940025 },
  { text: '유튜브', value: 1823456 },
  { text: '먹방', value: 1756234 },
  { text: '브이로그', value: 1654321 },
  { text: '음악', value: 1543210 },
  { text: 'K-POP', value: 1432109 },
  { text: '여행', value: 1321098 },
  { text: '일상', value: 1210987 },
  { text: '뷰티', value: 1109876 },
  { text: '패션', value: 1008765 },
  { text: '운동', value: 987654 },
  { text: '요리', value: 876543 },
  { text: '영화', value: 765432 },
  { text: '드라마', value: 654321 },
  { text: '애니메이션', value: 543210 },
  { text: '펫', value: 532109 },
  { text: '고양이', value: 521098 },
  { text: '강아지', value: 510987 },
  { text: '축구', value: 498765 },
  { text: '야구', value: 487654 },
  { text: '농구', value: 476543 },
  { text: 'IT', value: 465432 },
  { text: '프로그래밍', value: 454321 },
  { text: '주식', value: 443210 },
  { text: '부동산', value: 432109 },
  { text: '재테크', value: 421098 },
  { text: '자기계발', value: 410987 },
  { text: '독서', value: 398765 },
  { text: '공부', value: 387654 },
  { text: '수능', value: 376543 },
  { text: '대학', value: 365432 },
  { text: '취업', value: 354321 },
  { text: '면접', value: 343210 },
  { text: '이직', value: 332109 },
  { text: '창업', value: 321098 },
  { text: '마케팅', value: 310987 },
  { text: '디자인', value: 298765 },
  { text: '사진', value: 287654 },
  { text: '카메라', value: 276543 },
  { text: 'ASMR', value: 265432 },
  { text: '힐링', value: 254321 },
  { text: '명상', value: 243210 },
  { text: '요가', value: 232109 },
  { text: '헬스', value: 221098 },
  { text: '다이어트', value: 210987 },
  { text: '레시피', value: 198765 },
  { text: '카페', value: 187654 },
  { text: '맛집', value: 176543 },
  { text: '뉴진스', value: 168432 },
  { text: '아이브', value: 159321 },
  { text: '르세라핌', value: 150210 },
  { text: '스트레이키즈', value: 141098 },
  { text: 'BTS', value: 132987 },
  { text: '블랙핑크', value: 123876 },
  { text: '트와이스', value: 114765 },
  { text: '세븐틴', value: 105654 },
  { text: 'NCT', value: 96543 },
  { text: '엔하이픈', value: 87432 },
  { text: '마인크래프트', value: 78321 },
  { text: '발로란트', value: 69210 },
  { text: '오버워치', value: 60098 },
  { text: 'FIFA', value: 51987 },
  { text: '배틀그라운드', value: 42876 },
  { text: '메이플스토리', value: 33765 },
  { text: '로스트아크', value: 24654 },
  { text: '던전앤파이터', value: 15543 },
  { text: '스타크래프트', value: 14432 },
  { text: '테트리스', value: 13321 },
  { text: '코딩', value: 12210 },
  { text: '파이썬', value: 11098 },
  { text: '자바스크립트', value: 10987 },
  { text: '리액트', value: 9876 },
  { text: 'AI', value: 8765 },
  { text: 'ChatGPT', value: 7654 },
  { text: '클라우드', value: 6543 },
  { text: '데이터', value: 5432 },
  { text: '머신러닝', value: 4321 },
  { text: '블록체인', value: 3210 },
  { text: '비트코인', value: 2109 },
  { text: '이더리움', value: 1098 },
  { text: 'NFT', value: 987 },
  { text: '메타버스', value: 876 },
  { text: 'VR', value: 765 },
  { text: 'AR', value: 654 },
  { text: '로봇', value: 543 },
  { text: '드론', value: 432 },
  { text: '전기차', value: 321 },
  { text: '테슬라', value: 210 },
  { text: '애플', value: 198 },
  { text: '삼성', value: 187 },
  { text: '아이폰', value: 176 },
  { text: '갤럭시', value: 165 },
  { text: '맥북', value: 154 },
  { text: '아이패드', value: 143 },
  { text: '에어팟', value: 132 },
  { text: '갤럭시워치', value: 121 },
  { text: '닌텐도', value: 110 },
  { text: '플레이스테이션', value: 100 },
];

interface KeywordsProps {
  isShifted?: boolean;
}

const Keywords = ({ isShifted = false }: KeywordsProps) => {
  const svgRef = useRef<SVGSVGElement>(null);
  const initializedRef = useRef(false);
  const setSelectedKeyword = useKeywordStore(s => s.setSelectedKeyword);

  useEffect(() => {
    if (!svgRef.current || initializedRef.current) return;
    initializedRef.current = true;

    const width = 800;
    const height = 600;

    d3.select(svgRef.current).selectAll('*').remove();

    const maxValue = Math.max(...mockKeywords.map(d => d.value));
    const minValue = Math.min(...mockKeywords.map(d => d.value));
    const fontScale = d3.scaleLinear().domain([minValue, maxValue]).range([10, 70]);

    const colors = [
      '#6B4EFF',
      '#8257B4',
      '#9F8CFF',
      '#634DCB',
      '#A594F9',
      '#4F378A',
      '#FF6B6B',
      '#4ECDC4',
      '#45B7D1',
      '#96CEB4',
      '#FFEAA7',
      '#DDA0DD',
      '#FF8C00',
      '#20B2AA',
      '#9370DB',
      '#3CB371',
      '#FF69B4',
      '#00CED1',
    ];

    const layout = cloud<KeywordData & cloud.Word>()
      .size([width, height])
      .words(mockKeywords.map(d => ({ ...d, size: fontScale(d.value) })))
      .padding(3)
      .rotate(() => (Math.random() > 0.7 ? 90 : 0))
      .font('Pretendard')
      .fontSize(d => d.size || 12)
      .on('end', words => {
        const svg = d3
          .select(svgRef.current)
          .attr('width', width)
          .attr('height', height)
          .append('g')
          .attr('transform', `translate(${width / 2},${height / 2})`);

        svg
          .selectAll('text')
          .data(words)
          .enter()
          .append('text')
          .style('font-size', d => `${d.size}px`)
          .style('font-family', 'Pretendard')
          .style('font-weight', '600')
          .style('fill', () => colors[Math.floor(Math.random() * colors.length)])
          .style('cursor', 'pointer')
          .style('opacity', 0)
          .attr('text-anchor', 'middle')
          .attr('transform', d => `translate(${d.x},${d.y})rotate(${d.rotate})`)
          .text(d => d.text || '')
          .transition()
          .duration(800)
          .delay((_, i) => i * 1)
          .style('opacity', 1);

        // 호버 효과 + 클릭 이벤트
        svg.selectAll('text').on('click', function () {
          const d = d3.select(this).datum() as KeywordData & cloud.Word;
          setSelectedKeyword({ text: d.text || '', value: d.value });
        });
      });

    layout.start();
  }, []);

  return (
    <div
      className={`flex items-center justify-center transition-all duration-500 ease-in-out ${isShifted ? '-translate-x-20' : 'translate-x-0'}`}
    >
      <svg ref={svgRef} />
    </div>
  );
};

export default Keywords;
