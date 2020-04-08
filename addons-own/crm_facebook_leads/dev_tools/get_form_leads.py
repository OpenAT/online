import requests
import json

fb_form_id = 123
page_access_token = "abc"

# Get form leads
# --------------
leads_url = "https://graph.facebook.com/v6.0/{}/leads?access_token={}".format(
    fb_form_id,
    page_access_token)
response = requests.get(leads_url)

data_json = response.json()
print("Form Leads:\n\n")
print(json.dumps(data_json, indent=4, sort_keys=True))
