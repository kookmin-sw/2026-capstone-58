# Crit Frontend

React + TypeScript + Vite 기반 프론트엔드 프로젝트입니다.

## 기술 스택

- React 19
- TypeScript 5.9
- Vite 8
- Tailwind CSS 4
- React Router 7
- ESLint + Prettier

## 시작하기

```bash
# 패키지 설치
pnpm install

# 개발 서버 실행
pnpm dev

# 빌드
pnpm build

# 프리뷰
pnpm preview
```

## 스크립트

| 명령어              | 설명               |
| ------------------- | ------------------ |
| `pnpm dev`          | 개발 서버 실행     |
| `pnpm build`        | 프로덕션 빌드      |
| `pnpm preview`      | 빌드 결과 미리보기 |
| `pnpm lint`         | ESLint 검사        |
| `pnpm lint:fix`     | ESLint 자동 수정   |
| `pnpm format`       | Prettier 포맷팅    |
| `pnpm format:check` | Prettier 포맷 검사 |

## 프로젝트 구조

```
src/
├── assets/          # 정적 리소스
├── pages/           # 페이지 컴포넌트
│   └── main/
├── routes/          # 라우팅 설정
│   └── routes.tsx
├── index.css        # 글로벌 스타일
└── index.tsx        # 엔트리 포인트
```

## 경로 별칭

`@/*` → `src/*` 경로 별칭이 설정되어 있습니다.

```tsx
import MainPage from '@/pages/main';
```
