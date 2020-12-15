# https://github.com/Yelp/bravado
from bravado.requests_client import RequestsClient
from bravado.client import SwaggerClient


admin_user_openapi_token = "4b0e734e-6404-4db1-9940-8e7937ca46bc"
integration_api_token = "b176ab24-153e-4e7d-8ea1-a77784687102"
integration_spec_url = "http://demo.local.com/api/v1/demo_api_de_v1/swagger.json?token=b176ab24-153e-4e7d-8ea1-a77784687102&db=aiat"

http_client = RequestsClient()
http_client.set_basic_auth('demo.local.com', 'aiat', admin_user_openapi_token)

odoo = SwaggerClient.from_url(
    integration_spec_url,
    http_client=http_client
)

result = odoo.res_partner.callMethodForResPartnerModel(
    method_name="search",
    body={
        'args': [[('email', '=', 'sync@it-projects.info')]]
    }
).response().incoming_response.json()

partner_id = result and result[0]

if not partner_id:
    result = odoo.res_partner.addResPartner(body={
        "name": "OpenAPI Support",
        "email": "sync@it-projects.info"
    }).response().result
    partner_id = result.id

odoo.res_partner.callMethodForResPartnerSingleRecord(
  id=partner_id,
  method_name="message_post",
  body={
    "kwargs": {
      "body": "The Openapi module works in Python! Thank you!",
      "partner_ids": [partner_id]
    }
  }
).response()

