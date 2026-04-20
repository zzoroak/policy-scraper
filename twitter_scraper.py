import os
from datetime import datetime, timedelta, timezone

import requests

LAST_ID_FILE = "last_tweet_id.txt"

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

from prompts import twitter_prompt

USERNAME = "Jaemyung_Lee"
USER_ID = "106379129"


def get_recent_tweets():
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=90)

    print(f"[트윗 조회] since: {since.isoformat()}")

    start_time = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"https://api.x.com/2/users/{USER_ID}/tweets"

    params = {
        "start_time": start_time,
        "tweet.fields": "created_at,text,note_tweet"
    }

    headers = {
        "Authorization": f"Bearer {BEARER_TOKEN}"
    }

    res = requests.get(url, headers=headers, params=params)

    if res.status_code != 200:
        print("[트윗 조회 실패]", res.status_code, res.text)
        return []

    data = res.json().get("data", [])
    print(f"[트윗 조회 성공] 개수: {len(data)}")

    return data


def is_related_to_sk_gas(text):
    print("[Gemini 요청] 시작")

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-lite:generateContent?key={GOOGLE_AI_API_KEY}"

    payload = {
        "contents": [
            {
                "parts": [{"text": twitter_prompt(text)}]
            }
        ]
    }

    headers = {
        "Content-Type": "application/json"
    }

    res = requests.post(url, headers=headers, json=payload)

    if res.status_code != 200:
        print("[Gemini 실패]", res.text)
        return False

    result = res.json()
    answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    print(f"[Gemini 결과] {answer}")

    return answer.upper().startswith("YES")


def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    res = requests.post(url, json=payload)

    if res.status_code != 200:
        print("[텔레그램 실패]", res.text)
    else:
        print("[텔레그램 성공]")


def main():
    last_processed_id = 0
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, "r") as f:
            content = f.read().strip()
            if content.isdigit():
                last_processed_id = int(content)

    print(f"[체크] 이전에 처리한 마지막 ID: {last_processed_id}")

    tweets = get_recent_tweets()
    if not tweets:
        print("새로운 트윗이 없습니다.")
        return

    tweets.sort(key=lambda x: int(x['id']))

    new_last_id = last_processed_id

    for t in tweets:
        current_id = int(t['id'])

        if current_id <= last_processed_id:
            continue

        print("=" * 50)
        print(f"[신규 트윗 발견] {t['created_at']} / {current_id}")

        full_text = t.get("note_tweet", {}).get("text", t["text"])

        try:
            related = is_related_to_sk_gas(full_text)
            if not related:
                print("[스킵] 관련 없는 내용")
                new_last_id = current_id
                continue

        except Exception as e:
            print("[필터 에러 → 그냥 전송]", e)
            related = True

        message = f"이재명 대통령 트위터\n\n{full_text}\n\nhttps://x.com/{USERNAME}/status/{t['id']}"
        if len(message) > 4000: message = message[:4000]

        send_telegram(message)

        new_last_id = current_id

    if new_last_id > last_processed_id:
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(new_last_id))
        print(f"[저장] 최신 ID 업데이트: {new_last_id}")


if __name__ == "__main__":
    if __name__ == "__main__":
        print("실행:", datetime.now())
        main()
