import json
from django.template import Template, Context
from django.conf import settings
from collections import namedtuple


#Credentials = namedtuple("Credentials", "congregation username password")

#def read_credentials as Credentials:
#    with open('credentials.json') as json_file:  
#    data = json.load(json_file)
#    for p in data['credentials']:
#        c = Credentials(p['congregation'], p['username'], p['password'])
#    return c

f = open("login.xml", "r")
template = f.read()

t = Template(template)
c = Context({"congregation": "a",
             "username": "b",
             "password":"c"})
print t.render(c)
