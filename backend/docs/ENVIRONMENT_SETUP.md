# 환경 변수 설정 가이드

## 개요

CRIT Server는 민감한 정보(API 키, 데이터베이스 자격증명 등)를 환경 변수로 관리합니다.
이 문서는 로컬 개발 환경과 프로덕션 환경에서 환경 변수를 설정하는 방법을 설명합니다.

---

## 로컬 개발 환경 설정

### 1단계: .env 파일 생성

`.env.example` 파일을 복사하여 `.env` 파일을 생성합니다.

```bash
cp .env.example .env
```

### 2단계: .env 파일 수정

`.env` 파일을 열고 실제 값으로 채웁니다.

```bash
# Google APIs
GEMINI_API_KEY=your_gemini_api_key_here
YOUTUBE_API_KEY=your_youtube_api_key_here
GCP_KEY_PATH=/path/to/gcp-service-account-key.json

# AWS Configuration
AWS_REGION=us-east-1
AWS_BEDROCK_MODEL_ID=anthropic.claude-3-haiku-20240307-v1:0
AWS_S3_BUCKET=your-s3-bucket-name

# Database Configuration
SPRING_DATASOURCE_URL=jdbc:mysql://your-db-host:3306/crit?useSSL=false&serverTimezone=Asia/Seoul&allowPublicKeyRetrieval=true
SPRING_DATASOURCE_USERNAME=your_db_username
SPRING_DATASOURCE_PASSWORD=your_db_password

# Application Configuration
SPRING_PROFILES_ACTIVE=dev
SERVER_PORT=8080
SPRING_JPA_HIBERNATE_DDL_AUTO=update
SPRING_JPA_SHOW_SQL=true
```

### 3단계: IDE에서 환경 변수 로드

#### IntelliJ IDEA

1. **Run → Edit Configurations**
2. **Environment variables** 필드에 다음 추가:
   ```
   GEMINI_API_KEY=your_key;YOUTUBE_API_KEY=your_key;...
   ```
   또는
3. **EnvFile 플러그인 설치** (권장)
   - Plugins → Marketplace → "EnvFile" 검색 및 설치
   - Run Configuration에서 "EnvFile" 탭 활성화
   - `.env` 파일 경로 지정

#### VS Code

1. **Extensions → "REST Client" 또는 "Thunder Client" 설치**
2. `.vscode/settings.json` 생성:
   ```json
   {
     "dotenv.enableAutocloaking": false
   }
   ```
3. **dotenv 확장 설치** (선택사항)

#### 명령줄 실행

```bash
# Linux/Mac
export $(cat .env | xargs)
./gradlew bootRun

# Windows PowerShell
Get-Content .env | ForEach-Object {
    if ($_ -match '^\s*([^=]+)=(.*)$') {
        [Environment]::SetEnvironmentVariable($matches[1], $matches[2])
    }
}
./gradlew bootRun
```

---

## 프로덕션 환경 설정

### AWS EC2 환경

#### 1. EC2 인스턴스에 환경 변수 설정

```bash
# SSH로 EC2 접속
ssh -i your-key.pem ec2-user@your-instance-ip

# 환경 변수 설정
export GEMINI_API_KEY=your_key
export YOUTUBE_API_KEY=your_key
export AWS_REGION=us-east-1
export AWS_S3_BUCKET=your-bucket
export SPRING_DATASOURCE_URL=your_db_url
export SPRING_DATASOURCE_USERNAME=your_username
export SPRING_DATASOURCE_PASSWORD=your_password
```

#### 2. systemd 서비스 파일 생성

`/etc/systemd/system/crit-server.service` 생성:

```ini
[Unit]
Description=CRIT Server
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/crit-server

# 환경 변수 파일 지정
EnvironmentFile=/home/ec2-user/crit-server/.env

ExecStart=/home/ec2-user/crit-server/gradlew bootRun
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 3. 서비스 시작

```bash
sudo systemctl daemon-reload
sudo systemctl enable crit-server
sudo systemctl start crit-server
sudo systemctl status crit-server
```

### Docker 환경

#### Dockerfile

```dockerfile
FROM openjdk:17-jdk-slim

WORKDIR /app

COPY . .

# 환경 변수는 docker run 시 -e 옵션으로 전달
ENV SPRING_PROFILES_ACTIVE=prod

RUN chmod +x gradlew

EXPOSE 8080

CMD ["./gradlew", "bootRun"]
```

#### docker-compose.yml

```yaml
version: '3.8'

services:
  crit-server:
    build: .
    ports:
      - "8080:8080"
    environment:
      GEMINI_API_KEY: ${GEMINI_API_KEY}
      YOUTUBE_API_KEY: ${YOUTUBE_API_KEY}
      AWS_REGION: ${AWS_REGION}
      AWS_S3_BUCKET: ${AWS_S3_BUCKET}
      SPRING_DATASOURCE_URL: ${SPRING_DATASOURCE_URL}
      SPRING_DATASOURCE_USERNAME: ${SPRING_DATASOURCE_USERNAME}
      SPRING_DATASOURCE_PASSWORD: ${SPRING_DATASOURCE_PASSWORD}
    depends_on:
      - mysql

  mysql:
    image: mysql:8.0
    environment:
      MYSQL_ROOT_PASSWORD: ${MYSQL_ROOT_PASSWORD}
      MYSQL_DATABASE: crit
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

#### 실행

```bash
# .env 파일에서 환경 변수 로드
docker-compose up -d
```

### AWS Elastic Beanstalk 환경

#### .ebextensions/env.config

```yaml
option_settings:
  aws:elasticbeanstalk:application:environment:
    GEMINI_API_KEY: your_gemini_key
    YOUTUBE_API_KEY: your_youtube_key
    AWS_REGION: us-east-1
    AWS_S3_BUCKET: your-bucket
    SPRING_DATASOURCE_URL: your_db_url
    SPRING_DATASOURCE_USERNAME: your_username
    SPRING_DATASOURCE_PASSWORD: your_password
    SPRING_PROFILES_ACTIVE: prod
```

#### 배포

```bash
eb deploy
```

---

## 환경 변수 설명

### Google APIs

| 변수 | 설명 | 예시 |
|------|------|------|
| `GEMINI_API_KEY` | Google Gemini API 키 | `AIzaSy...` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 키 | `AIzaSy...` |
| `GCP_KEY_PATH` | GCP 서비스 계정 키 파일 경로 | `/path/to/key.json` |

### AWS Configuration

| 변수 | 설명 | 예시 |
|------|------|------|
| `AWS_REGION` | AWS 리전 | `us-east-1` |
| `AWS_BEDROCK_MODEL_ID` | Bedrock 모델 ID | `anthropic.claude-3-haiku-20240307-v1:0` |
| `AWS_S3_BUCKET` | S3 버킷명 | `my-bucket-name` |

### Database Configuration

| 변수 | 설명 | 예시 |
|------|------|------|
| `SPRING_DATASOURCE_URL` | MySQL 연결 URL | `jdbc:mysql://host:3306/crit` |
| `SPRING_DATASOURCE_USERNAME` | DB 사용자명 | `admin` |
| `SPRING_DATASOURCE_PASSWORD` | DB 비밀번호 | `password123` |

### Application Configuration

| 변수 | 설명 | 예시 |
|------|------|------|
| `SPRING_PROFILES_ACTIVE` | Spring 프로필 | `dev`, `prod` |
| `SERVER_PORT` | 서버 포트 | `8080` |
| `SPRING_JPA_HIBERNATE_DDL_AUTO` | JPA DDL 자동 생성 | `update`, `create`, `validate` |
| `SPRING_JPA_SHOW_SQL` | SQL 로깅 | `true`, `false` |

---

## 보안 모범 사례

### 1. .env 파일 보호

```bash
# .env 파일 권한 설정 (소유자만 읽기 가능)
chmod 600 .env
```

### 2. 환경 변수 검증

```bash
# 필수 환경 변수 확인
required_vars=("GEMINI_API_KEY" "YOUTUBE_API_KEY" "SPRING_DATASOURCE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "Error: $var is not set"
        exit 1
    fi
done
```

### 3. 민감한 정보 로깅 방지

```java
// application.properties
logging.level.org.springframework.web=INFO
logging.level.org.hibernate.SQL=DEBUG
# 비밀번호는 로깅하지 않음
```

### 4. 정기적인 키 로테이션

- API 키는 정기적으로 변경
- 데이터베이스 비밀번호는 90일마다 변경
- 변경 후 모든 환경에서 업데이트

---

## 문제 해결

### 환경 변수가 로드되지 않음

```bash
# 1. 환경 변수 확인
echo $GEMINI_API_KEY

# 2. .env 파일 형식 확인 (BOM 없음, LF 줄바꿈)
file .env

# 3. 애플리케이션 로그 확인
tail -f server.log | grep -i "environment\|property"
```

### 데이터베이스 연결 실패

```bash
# 1. 연결 문자열 확인
echo $SPRING_DATASOURCE_URL

# 2. 데이터베이스 접근성 확인
mysql -h your-host -u your-user -p

# 3. 보안 그룹 확인 (AWS)
# 3306 포트가 열려있는지 확인
```

### API 키 오류

```bash
# 1. API 키 유효성 확인
curl -X GET "https://www.googleapis.com/youtube/v3/channels?part=id&forHandle=codingapple&key=$YOUTUBE_API_KEY"

# 2. API 할당량 확인
# Google Cloud Console → API & Services → Quotas
```

---

## 참고 자료

- [Spring Boot Externalized Configuration](https://spring.io/projects/spring-boot)
- [Google Cloud API Keys](https://cloud.google.com/docs/authentication/api-keys)
- [AWS Credentials](https://docs.aws.amazon.com/general/latest/gr/aws-sec-cred-types.html)
- [12 Factor App - Config](https://12factor.net/config)
