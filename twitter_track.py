import requests

BEARER_TOKEN = r"AAAAAAAAAAAAAAAAAAAAACKFvgEAAAAAZmNmOoEIQEvO2AJiB%2FO08HNckHI%3DfR1eBbaNMsT2RyZ77TzuBxWAbzM0lt8xeH4oqUoP88JRIa6COe"
headers = {"Authorization": f"Bearer {BEARER_TOKEN}"}
user_id = "ZZZ_EN"  # Replace with the user's ID
url = f"https://api.twitter.com/2/users/{user_id}/tweets"

response = requests.get(url, headers=headers)
tweets = response.json()

for tweet in tweets['data']:
    if "update detail" in tweet['text']:
        print(tweet['text'])
