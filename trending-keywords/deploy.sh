#!/bin/bash
# YouTube Trending Keywords Lambda 배포 스크립트
# Docker + AWS CLI가 있는 환경에서 실행하세요.

REGION="ap-northeast-2"
ACCOUNT_ID="730335373015"
ECR_REPO="youtube-trending-keywords"
LAMBDA_NAME="youtube-trending-keywords"
S3_BUCKET="pj-kmucd1-08-s3-trending-keywords"
ROLE_NAME="SafeRole-pj-kmucd1-08"
IMAGE_URI="${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com/${ECR_REPO}:latest"

echo "=== 1. S3 버킷 생성 ==="
aws s3api create-bucket \
  --bucket $S3_BUCKET \
  --region $REGION \
  --create-bucket-configuration LocationConstraint=$REGION

echo "=== 2. ECR 리포지토리 생성 ==="
aws ecr create-repository \
  --repository-name $ECR_REPO \
  --region $REGION

echo "=== 3. Docker 이미지 빌드 & 푸시 ==="
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin ${ACCOUNT_ID}.dkr.ecr.${REGION}.amazonaws.com
docker build --platform linux/amd64 -t $ECR_REPO .
docker tag $ECR_REPO:latest $IMAGE_URI
docker push $IMAGE_URI

echo "=== 4. Lambda 함수 생성 (기존 역할 사용) ==="
aws lambda create-function \
  --function-name $LAMBDA_NAME \
  --package-type Image \
  --code ImageUri=$IMAGE_URI \
  --role arn:aws:iam::${ACCOUNT_ID}:role/${ROLE_NAME} \
  --timeout 60 \
  --memory-size 512 \
  --environment "Variables={YOUTUBE_API_KEY=${YOUTUBE_API_KEY},S3_BUCKET=${S3_BUCKET}}" \
  --region $REGION

echo "=== 5. EventBridge 스케줄 (1시간 간격) ==="
aws events put-rule \
  --name ${LAMBDA_NAME}-hourly \
  --schedule-expression "rate(1 hour)" \
  --region $REGION

aws lambda add-permission \
  --function-name $LAMBDA_NAME \
  --statement-id eventbridge-hourly \
  --action lambda:InvokeFunction \
  --principal events.amazonaws.com \
  --source-arn arn:aws:events:${REGION}:${ACCOUNT_ID}:rule/${LAMBDA_NAME}-hourly \
  --region $REGION

aws events put-targets \
  --rule ${LAMBDA_NAME}-hourly \
  --targets "Id=1,Arn=arn:aws:lambda:${REGION}:${ACCOUNT_ID}:function:${LAMBDA_NAME}" \
  --region $REGION

echo "=== 배포 완료! ==="
echo "S3: s3://${S3_BUCKET}/words.json"
echo "Lambda: ${LAMBDA_NAME} (1시간마다 자동 실행)"
