import requests
from datetime import datetime, timedelta, timezone
from config import BEARER_TOKEN
from config import GOOGLE_AI_API_KEY
from config import TELEGRAM_TOKEN
from config import CHAT_ID
from prompts import twitter_prompt


USERNAME = "Jaemyung_Lee"
USER_ID = "106379129"


def get_recent_tweets():
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=1) # 추출 시간

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
        print(res.status_code, res.text)
        return []

    return res.json().get("data", [])

def is_related_to_sk_gas(text):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GOOGLE_AI_API_KEY}"

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
        print("Gemini error:", res.text)
        return False

    result = res.json()
    answer = result["candidates"][0]["content"]["parts"][0]["text"].strip()

    return answer.upper().startswith("YES")

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    payload = {
        "chat_id": CHAT_ID,
        "text": message
    }

    res = requests.post(url, json=payload)

    if res.status_code != 200:
        print("텔레그램 전송 실패:", res.text)

def main():
    tweets = get_recent_tweets()

    for t in tweets:
        if "note_tweet" in t and "text" in t["note_tweet"]:
            full_text = t["note_tweet"]["text"]
        else:
            full_text = t["text"]

        #if not is_related_to_sk_gas(full_text):
        #    continue

        message = f"""
이재명 대통령 트위터

{full_text}

https://x.com/{USERNAME}/status/{t['id']}
"""

        # 길이 제한 대비
        if len(message) > 4000:
            message = message[:4000]

        send_telegram(message)


if __name__ == "__main__":
    main()