import requests
import json

# fb_page_id = 123
# system_user_token = "asd"


fb_form_id = 345
page_access_token = "345"

# Get form questions/fields
# -------------------------
# HINT: To get a list of all available fields of an endpoint use ?metadata=1
#       e.g. "https://graph.facebook.com/v12.0/<form_id>?metadata=1

questions_url = "https://graph.facebook.com/v12.0/{}?fields=questions&access_token={}".format(
    fb_form_id,
    page_access_token)

response = requests.get(questions_url)

data_json = response.json()
print("Form Questions (Fields):\n\n")
print(json.dumps(data_json, indent=4, sort_keys=True))
