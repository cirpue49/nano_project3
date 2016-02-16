import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

#keys represent abbreviated streets' name and values represent expected name 
#By using this dictionary, I updated all abbreviated streets' name into expected names.
mapping = { "St": "Street",
            "St.": "Street",
            "Ave":"Avenue",
            "Rd.":"Road",
            "Rd":"Road",
            "broadway":"Broadway",
            "square":"Square",
            "Cres":"Crescent",
            "street":"Street",
            "Dr.":"Drive",
            "avenue":"Avenue",
            "Ave.":"Avenue",
            "Blvd,":"Boulevard",
            "St":"Street",
            "Ave":"Avenue",
            "parkway":"Parkway",
            "blvd":"Boulevard",
            "Avenie":"Avenue",
            "Hwy":"Highway",
            "Dr":"Drive",
            "Rd.":"Road",
            "st":"Street",
            "Blvd":"Boulevard",
            }

#update old name to expected name 
def update_name(name, mapping):
    old_name=street_type_re.search(name).group()
    return name.replace(old_name,mapping[old_name])   


def shape_element(element):
    node = {}
    
    if element.tag == "node" or element.tag == "way":
        node['id']=element.attrib['id']
        node['type']=element.tag
        node['created']={ 
        "changeset":element.attrib["changeset"], 
        "version":element.attrib["version"],
        "timestamp":element.attrib["timestamp"]}
        #'user', 'uid', 'visible', 'lat', and 'lon' are sometimes missing their values.
        #So only when there is a value, it creates a key for dictionary
        if 'user' in element.attrib.keys():
            node['created']["user"]=element.attrib["user"]
        if 'uid' in element.attrib.keys():
            node['created']["uid"]=element.attrib["uid"]
        if 'visible' in element.attrib.keys():
            node['visible']=element.attrib['visible']
        if 'lat' in element.attrib.keys():
            node['pos']=[float(element.attrib['lat']),float(element.attrib['lon'])]

        #create a address dictionary for all 'tag'  
        address={}
        for tag in element.iter("tag"):
            if problemchars.match(tag.attrib['k']):
                continue
            elif "addr:" in tag.attrib['k'] and ":" not in tag.attrib['k'][5:]:
                #Cleaning a street's name
                if tag.attrib['k']=="addr:street":
                    res = street_type_re.search(tag.attrib['v'])
                    #AttributeError: 'NoneType' object has no attribute 'group'
                    if res:
                        if street_type_re.search(tag.attrib['v']).group() in mapping.keys():
                            address[tag.attrib['k'][5:]]=update_name(tag.attrib['v'] , mapping)
                        else:
                            address[tag.attrib['k'][5:]]=tag.attrib['v'] 
                    else:
                        continue
                    
                elif tag.attrib['k']=="addr:postcode":
                    if len(tag.attrib['v'])>4:
                        p=tag.attrib['v'].find('9')
                        address[tag.attrib['k'][5:]]=tag.attrib['v'][p:p+5]

                else:
                    address[tag.attrib['k'][5:]]=tag.attrib['v']
                
                
            elif tag.attrib['k'][:4]=="addr:" and ":" in tag.attrib['k'][5:]:
                continue

            #create many keys for additional analysis
            elif tag.attrib['k']=="amenity":
                node['amenity']=tag.attrib['v']
            elif tag.attrib['k']=="service":
                node['service']=tag.attrib['v']
            elif tag.attrib['k']=="leisure":
                node['leisure']=tag.attrib['v']
            elif tag.attrib['k']=="cuisine":
                node['cuisine']=tag.attrib['v']

            else:
                continue
        
            node['address']=address
        
    return node

#process osm file into json file 
def process_map(file_in):
    file_out = "{0}.json".format(file_in)
    data = []
    count=0
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            el = shape_element(element)
            if el:
                data.append(el)
                fo.write(json.dumps(el) + "\n")
    return data

#insert json file to mongo 
def insert_data(infile, db):
    data = process_map(infile, pretty = False)
    for i in data:
        db.map.insert_one(i)

from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client.test

insert_data('san_francisco_california.osm', db)
print "success!"



