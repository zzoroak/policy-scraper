import requests
from datetime import datetime, timedelta, timezone
from config import BEARER_TOKEN

USERNAME = "Jaemyung_Lee"
USER_ID = "106379129"


def get_recent_tweets():
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=1)

    start_time = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    url = f"https://api.x.com/2/users/{USER_ID}/tweets"

    params = {
        "max_results": 10, # 과금 제한
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


def main():
    tweets = get_recent_tweets()

    for t in tweets:
        print("=" * 50)
        print("날짜:", t["created_at"])

        if "note_tweet" in t and "text" in t["note_tweet"]:
            full_text = t["note_tweet"]["text"]
        else:
            full_text = t["text"]

        print("내용:", full_text)
        print("URL:", f"https://x.com/{USERNAME}/status/{t['id']}")


if __name__ == "__main__":
    main()