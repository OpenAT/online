# Authentication Example
Example for authentication and requests with an odoo web_controller of type json

### Authentication request
```
POST: http://localhost:8069/web/session/authenticate

# Headers
{'Content-type': 'application/json'}

# Payload
{
  'jsonrpc': '2.0',
    'params': {
      'db': db,
      'login': user,
      'password': password,
    },
}


# Returns the session_id in the answer if login was successfull
session_id = result['result']['session_id']
```

### Subsequent requests
```
http://localhost:8069/your/controller/route

# Headers
{
    'X-Openerp-Session-Id': session_id,
    'Content-type': 'application/json',
}

# Payload
{
  'jsonrpc': '2.0',
    'params': {
        ...
    },
}
```

### Full Example in Python
``` python
import json
import urllib2

db = 'odoo9'
user = 'admin'
password = 'admin'

request = urllib2.Request(
  'http://localhost:8069/web/session/authenticate',
    json.dumps({
      'jsonrpc': '2.0',
        'params': {
          'db': db,
          'login': user,
          'password': password,
        },
    }),
    {'Content-type': 'application/json'})
    result = urllib2.urlopen(request).read()
    result = json.loads(result)
    session_id = result['result']['session_id']
    request = urllib2.Request(
      'http://localhost:8069/web/dataset/call_kw',
      json.dumps({
        'jsonrpc': '2.0',
        'params': {
          'model': 'ir.module.module',
          'method': 'search_read',
          'args': [
            [('state', '=', 'installed')],
            ['name'],
          ],
          'kwargs': {'context': {'lang': 'fr_FR'}},
        },
    }),
    {
        'X-Openerp-Session-Id': session_id,
        'Content-type': 'application/json',
  })
  result = urllib2.urlopen(request).read()
  result = json.loads(result)
  for module in result['result']:
    print module['name']
```
