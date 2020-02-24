# -*- coding: utf-8 -*-
from lxml import etree
import io


# https://emredjan.github.io/blog/2017/04/08/validating-xml/

# Validate xml
filename_xml = '/Users/mkarrer/Entwicklung/github/online/gl2k/submission_content_inner_small.xml'
filename_xsd = '/Users/mkarrer/Entwicklung/github/online/online_o8/addons-own/fso_con_zmr/doc/Spendenmeldung/Sonderausgaben/2018-25-01/UebermittlungSonderausgaben_2.xsd'


# OPEN AND PARSE SCHEMA FILE
# --------------------------
with io.open(filename_xsd, 'r', encoding="utf-8") as schema_file:
    schema_to_check = schema_file.read()

# Parse the XSD File as etree XMLSchema
xmlschema_doc = etree.fromstring(schema_to_check.encode('utf-8'))
xmlschema = etree.XMLSchema(xmlschema_doc)


# OPEN AND PARSE XML DATA-FILE
# ----------------------------
with io.open(filename_xml, 'r', encoding="utf-8") as xml_file:
    xml_to_check = xml_file.read()

# parse the xml file
try:
    doc = etree.fromstring(xml_to_check.encode('utf-8'))
    print('XML well formed, syntax ok.')
# check for file IO error
except IOError:
    print('Invalid File')
# check for XML syntax errors
except etree.XMLSyntaxError as err:
    print('XML Syntax Error, see error_syntax.log')
    with open('error_syntax.log', 'w') as error_log_file:
        error_log_file.write(str(err.error_log))
    quit()
except:
    print('Unknown error, exiting.')
    quit()


# VALIDATE XML DATA-FILE AGAINST SCHEMA
# -------------------------------------
try:
    xmlschema.assertValid(doc)
    print('XML valid, schema validation ok.')

except etree.DocumentInvalid as err:

    print str(err.error_log)

    #print('Schema validation error, see error_schema.log')
    #with open('error_schema.log', 'w') as error_log_file:
    #    error_log_file.write(str(err.error_log))
    #quit()

except:
    print('Unknown error, exiting.')
    quit()
