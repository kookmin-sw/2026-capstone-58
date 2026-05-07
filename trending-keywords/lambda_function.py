import json
import os
import re
from collections import Counter
from urllib.request import urlopen, Request
from urllib.parse import urlencode

import boto3
from kiwipiepy import Kiwi

API_KEY = os.environ.get("YOUTUBE_API_KEY", "")
REGION_CODE = os.environ.get("REGION_CODE", "KR")
S3_BUCKET = os.environ.get("S3_BUCKET", "pj-kmucd1-08-s3-trending-keywords")
S3_KEY = os.environ.get("S3_KEY", "words.json")
MAX_RESULTS = 50
PAGES = 4
TOP_N = 100

NOUN_TAGS = {"NNG", "NNP", "NNB"}
MIN_KEYWORD_LEN = 2

STOPWORDS = {
    "구독", "채널", "광고", "문의", "가입", "멤버십", "후원", "댓글", "알림",
    "좋아요", "싫어요", "공유", "저장", "시청", "조회", "링크", "클릭",
    "유튜브", "브금", "아프리카", "트위치", "인스타", "인스타그램",
    "트위터", "페이스북", "네이버", "카페", "블로그", "홈페이지",
    "이메일", "메일", "업로드", "콘텐츠", "컨텐츠", "주소",
    "제공", "포함", "제작", "편집", "출처", "사용", "설정", "관련",
    "비즈니스", "공식", "문의처", "강의", "추천", "리뷰", "업데이트",
    "영상", "방송", "생방송", "방송국", "감사", "시작", "정보",
    "가능", "경우", "부분", "이상", "이하", "정도", "대상",
    "전체", "확인", "부탁", "각종", "이동", "진행", "개인",
    "오늘", "내용", "정리", "소식", "저녁", "시간", "사랑",
    "바람", "마음", "노래", "음악", "사람", "모습", "세계",
}

kiwi = Kiwi()
s3 = boto3.client("s3")


def fetch_trending_videos():
    videos = []
    page_token = None
    for _ in range(PAGES):
        params = {
            "part": "snippet,statistics",
            "chart": "mostPopular",
            "regionCode": REGION_CODE,
            "maxResults": MAX_RESULTS,
            "key": API_KEY,
        }
        if page_token:
            params["pageToken"] = page_token
        url = f"https://www.googleapis.com/youtube/v3/videos?{urlencode(params)}"
        with urlopen(Request(url)) as resp:
            data = json.loads(resp.read())
        for item in data.get("items", []):
            sn = item["snippet"]
            st = item.get("statistics", {})
            videos.append({
                "title": sn.get("title", ""),
                "description": sn.get("description", ""),
                "tags": sn.get("tags", []),
                "views": int(st.get("viewCount", 0)),
            })
        page_token = data.get("nextPageToken")
        if not page_token:
            break
    return videos


def extract_keywords_from_text(text):
    text = re.sub(r"https?://\S+", "", text)
    text = re.sub(r"[#@]", " ", text)
    keywords = set()
    for token in kiwi.tokenize(text):
        word = token.form.strip()
        if token.tag in NOUN_TAGS and len(word) >= MIN_KEYWORD_LEN and word not in STOPWORDS:
            keywords.add(word)
    return keywords


def extract_keywords(videos):
    scores = Counter()
    for v in videos:
        text = v["title"] + "\n" + v["description"] + "\n" + "\n".join(v["tags"])
        for kw in extract_keywords_from_text(text):
            scores[kw] += v["views"]
    return scores.most_common(TOP_N)


def lambda_handler(event, context):
    if not API_KEY:
        return {"statusCode": 400, "body": json.dumps({"error": "YOUTUBE_API_KEY not set"})}

    videos = fetch_trending_videos()
    keywords = extract_keywords(videos)
    words = [{"text": kw, "value": score} for kw, score in keywords]
    body = json.dumps(words, ensure_ascii=False)

    s3.put_object(Bucket=S3_BUCKET, Key=S3_KEY, Body=body, ContentType="application/json")

    return {"statusCode": 200, "body": body}
