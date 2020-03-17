import requests
import json

fb_page_id = 123
user_access_token = "aaa"

# Generate non expiring page token from user access token
# -------------------------------------------------------
response = requests.get("https://graph.facebook.com/v6.0/{}".format(fb_page_id),
                        params={"fields": "access_token",
                                "access_token": user_access_token
                                })

data_json = response.json()
print(json.dumps(data_json, indent=4, sort_keys=True))

page_access_token = data_json['access_token']
print("\npage access token:\n%s" % page_access_token)
