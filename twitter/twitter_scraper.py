import requests
from datetime import datetime, timedelta, timezone
from config import BEARER_TOKEN
from config import GOOGLE_AI_API_KEY
from prompts import twitter_prompt


USERNAME = "Jaemyung_Lee"
USER_ID = "106379129"


def get_recent_tweets():
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=5) # 추출 시간

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

def main():
    tweets = get_recent_tweets()

    for t in tweets:
        if "note_tweet" in t and "text" in t["note_tweet"]:
            full_text = t["note_tweet"]["text"]
        else:
            full_text = t["text"]

        if not is_related_to_sk_gas(full_text):
            continue

        print("=" * 50)
        print("날짜:", t["created_at"])
        print("내용:", full_text)
        print("URL:", f"https://x.com/{USERNAME}/status/{t['id']}")


if __name__ == "__main__":
    main()