#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import codecs
import json

street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]


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


def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)


def is_street_name(elem):
    return (elem.attrib['k'] == "addr:street")


def audit():
    osm_file = open('san_francisco_california,.osm', "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    return dict(street_types)

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
        if 'user' in element.attrib.keys():
            node['created']["user"]=element.attrib["user"]
        if 'uid' in element.attrib.keys():
            node['created']["uid"]=element.attrib["uid"]
        if 'visible' in element.attrib.keys():
            node['visible']=element.attrib['visible']
        if 'lat' in element.attrib.keys():
            node['pos']=[float(element.attrib['lat']),float(element.attrib['lon'])]


        address={}
        for tag in element.iter("tag"):
            if problemchars.match(tag.attrib['k']):
                continue
            elif "addr:" in tag.attrib['k'] and ":" not in tag.attrib['k'][5:]:
                if tag.attrib['k']=="addr:street":
                    # for i in mapping:
                    res = street_type_re.search(tag.attrib['v'])
                    #AttributeError: 'NoneType' object has no attribute 'group'
                    if res:
                        if street_type_re.search(tag.attrib['v']).group() in mapping.keys():
                            
                            address[tag.attrib['k'][5:]]=update_name(tag.attrib['v'] , mapping)
                            # print tag.attrib['k'][5:]
                            # print update_name(tag.attrib['v'] , mapping)
                        else:
                            address[tag.attrib['k'][5:]]=tag.attrib['v'] 
                    else:
                        continue
                    
                    # print address[tag.attrib['k'][5:]]  
                elif tag.attrib['k']=="addr:postcode":
                    if len(tag.attrib['v'])>4:
                        p=tag.attrib['v'].find('9')
                        address[tag.attrib['k'][5:]]=tag.attrib['v'][p:p+5]

                else:
                    address[tag.attrib['k'][5:]]=tag.attrib['v']
                
                
            elif tag.attrib['k'][:4]=="addr:" and ":" in tag.attrib['k'][5:]:
                continue
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
            # print node['address']

        node['node_refs']=[]
        for nd in element.iter("nd"):
            node['node_refs'].append(nd.attrib['ref'])
        if node['node_refs']==[]:
            del node['node_refs']

        
    return node


def process_map(file_in, pretty = False):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    count=0
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            # count+=1
            # if count==100000:
            #     return data
            el = shape_element(element)
            if el:
                data.append(el)
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    # print data
    return data

# def test():
#     # NOTE: if you are running this code on your computer, with a larger dataset, 
#     # call the process_map procedure with pretty=False. The pretty=True option adds 
#     # additional spaces to the output, making it significantly larger.
#     data = process_map('san_francisco_california.osm', True)
#     #pprint.pprint(data)
    
#     correct_first_elem = {
#         "id": "261114295", 
#         "visible": "true", 
#         "type": "node", 
#         "pos": [41.9730791, -87.6866303], 
#         "created": {
#             "changeset": "11129782", 
#             "user": "bbmiller", 
#             "version": "7", 
#             "uid": "451048", 
#             "timestamp": "2012-03-28T18:31:23Z"
#         }
#     }
#     assert data[0] == correct_first_elem
#     assert data[-1]["address"] == {
#                                     "street": "West Lexington Street", 
#                                     "housenumber": "1412"
#                                       }
#     assert data[-1]["node_refs"] == [ "2199822281", "2199822390",  "2199822392", "2199822369", 
#                                     "2199822370", "2199822284", "2199822281"]
#     print "Success!"

# if __name__ == "__main__":
#     test()
def insert_data(infile, db):
    data = process_map(infile, pretty = False)
    for i in data:
        db.map.insert_one(i)
#collection:map original giant data
#map_1 change post
#map_2 add if function

from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27017")
db = client.test

insert_data('san_francisco_california.osm', db)
print "success!"



