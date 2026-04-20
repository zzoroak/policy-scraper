import os
from datetime import datetime, timedelta, timezone

import requests

BEARER_TOKEN = os.getenv("BEARER_TOKEN")
GOOGLE_AI_API_KEY = os.getenv("GOOGLE_AI_API_KEY")
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

from prompts import twitter_prompt

USERNAME = "Jaemyung_Lee"
USER_ID = "106379129"


def get_recent_tweets():
    now = datetime.now(timezone.utc)
    since = now - timedelta(minutes=30)

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
    tweets = get_recent_tweets()

    for t in tweets:
        print("=" * 50)
        print(f"[트윗] {t['created_at']} / {t['id']}")

        if "note_tweet" in t and "text" in t["note_tweet"]:
            full_text = t["note_tweet"]["text"]
        else:
            full_text = t["text"]

        print(f"[내용]\n{full_text[:100]}...")

        try:
            related = is_related_to_sk_gas(full_text)
            print(f"[필터 결과] {'관련 있음' if related else '관련 없음'}")

            if not related:
                print("[스킵]")
                continue

        except Exception as e:
            print("[필터 에러 → 그냥 전송]", e)
            related = True

        message = f"""이재명 대통령 트위터

{full_text}

https://x.com/{USERNAME}/status/{t['id']}
"""

        if len(message) > 4000:
            message = message[:4000]

        send_telegram(message)


if __name__ == "__main__":
    if __name__ == "__main__":
        print("실행:", datetime.now())
        main()
