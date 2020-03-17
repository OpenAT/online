import requests
import json

fb_page_id = 123
page_access_token = "abc"

# Get form data
# -------------
forms_url = "https://graph.facebook.com/v6.0/{}/leadgen_forms?access_token={}".format(fb_page_id, page_access_token)
response = requests.get(forms_url)

data_json = response.json()
print("Form Data:\n\n")
print(json.dumps(data_json, indent=4, sort_keys=True))
