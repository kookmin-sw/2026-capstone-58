#!/bin/bash
# crit-server 시작 스크립트
# 현재 EC2 IP를 감지하여 설정 파일 업데이트 후 서버 실행

IP=$(curl -s http://169.254.169.254/latest/meta-data/public-ipv4)
echo "현재 EC2 IP: $IP"

# application.properties 업데이트
PROPS="src/main/resources/application.properties"
sed -i "s|http://[0-9.]*\.nip\.io:8080/login/oauth2/code/google|http://${IP}.nip.io:8080/login/oauth2/code/google|" "$PROPS"
sed -i "s|http://[0-9.]*:5173/oauth-callback|http://${IP}:5173/oauth-callback|" "$PROPS"

# SecurityConfig.java CORS 업데이트
SEC="src/main/java/com/capstone/crit/security/SecurityConfig.java"
sed -i "s|http://[0-9.]*:5173|http://${IP}:5173|g" "$SEC"
sed -i "s|http://[0-9.]*:3000|http://${IP}:3000|g" "$SEC"

echo "설정 업데이트 완료"
echo "서버 시작..."
./gradlew bootRun
