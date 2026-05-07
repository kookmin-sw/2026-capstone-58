export const getScoreColors = (score: number) => {
  if (score <= 30) return { fill: '#FF0000', track: '#FFEFEF' };
  if (score <= 70) return { fill: '#FF9D00', track: '#FFFCEF' };
  return { fill: '#5AC467', track: '#5AC46733' };
};
