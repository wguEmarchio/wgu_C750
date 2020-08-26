import csv
import codecs
import pprint
import re
import xml.etree.cElementTree as ET

import cerberus
import schema

OSM_PATH = 'map_slc'

NODES_PATH = "nodes.csv"
NODE_TAGS_PATH = "nodes_tags.csv"
WAYS_PATH = "ways.csv"
WAY_NODES_PATH = "ways_nodes.csv"
WAY_TAGS_PATH = "ways_tags.csv"

# Regex searches
LOWER_COLON = re.compile(r'^([a-z]|_)+:([a-z]|_)+')
PROBLEMCHARS = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

SCHEMA = schema.schema

# Used for column headings in output .csv files
NODE_FIELDS = ['id', 'lat', 'lon', 'user', 'uid', 'version', 'changeset', 'timestamp']
NODE_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_FIELDS = ['id', 'user', 'uid', 'version', 'changeset', 'timestamp']
WAY_TAGS_FIELDS = ['id', 'key', 'value', 'type']
WAY_NODES_FIELDS = ['id', 'node_id', 'position']

# Mapping values for updating street information
mapping = {
    'St' : 'Street',
    'St.': 'Street',
    'Ste.': 'Suite',
    'Ave': 'Avenue',
    'Ave.':'Avenue',
    'ave': 'Avenue',
    'Rd' : 'Road',
    'Rd.': 'Road',
    'Ln' : 'Lane',
    'S,' : 'South',
    'S'  : 'South',
    'S.' : 'South',
    'N'  : 'North',
    'E'  : 'East',
    'W'  : 'West',
    'W.' : 'West',
    'Ct' : 'Court',
    'Dr' : 'Drive',
    'Cir': 'Circle',
    'Blvd': 'Boulevard',
    'Pkwy': 'Parkway',
    'Pl'  : 'Place'
        }

# Updates abbreviated values to full name in mapping dictionary
def update_all(name, mapping):
    name_list = name.split()
      
    for n in range(len(name_list)):
        for k,v in mapping.items():
            if name_list[n] == k:
                name_list[n] = name_list[n].replace(k,v)
    name = ' '.join(name_list)
    return name

# Capitalizes all first letters of words in name
def cap_all(name):
    name_list = name.split()

    for names in name_list:
        names.capitalize()

    name = ' '.join(name_list)
    return name

# Creates dictionaries that will be used to insert into .csv files
def shape_element(element, node_attr_fields=NODE_FIELDS, way_attr_fields=WAY_FIELDS,
                  problem_chars=PROBLEMCHARS, default_tag_type='regular'):

    node_attribs = {}
    way_attribs = {}
    way_nodes = []
    tags = []  # Handle secondary tags the same way for both node and way elements
    node_dict = {}
    way_dict = {}

    if element.tag == 'node':
        node_attribs['id'] = element.attrib.get('id')
        node_attribs['user'] = element.attrib.get('user')
        node_attribs['uid'] = element.attrib.get('uid')
        node_attribs['version'] = element.attrib.get('version')
        node_attribs['lat'] = element.attrib.get('lat')
        node_attribs['lon'] = element.attrib.get('lon')
        node_attribs['timestamp'] = element.attrib.get('timestamp')
        node_attribs['changeset'] = element.attrib.get('changeset')
        for tag in element.iter('tag'):
            if not PROBLEMCHARS.search(tag.attrib['k']):
                key_attrib = tag.attrib['k']
                type_attrib = 'regular'
                value_attrib = tag.attrib['v']
                if LOWER_COLON.search(tag.attrib['k']):
                    type_attrib = (tag.attrib['k'].split(':'))[0]
                    key_attrib = ':'.join(tag.attrib['k'].split(':')[1:])
                tags.append({'id':element.attrib.get('id'), 'key':key_attrib, 'value': value_attrib, 'type': type_attrib})          
        node_dict = {'node': node_attribs, 'node_tags': tags}
        return node_dict
    elif element.tag == 'way':
        way_attribs['id'] = element.attrib.get('id')
        way_attribs['user'] = element.attrib.get('user')
        way_attribs['uid'] = element.attrib.get('uid')
        way_attribs['version'] = element.attrib.get('version')
        way_attribs['timestamp'] = element.attrib.get('timestamp')
        way_attribs['changeset'] = element.attrib.get('changeset')
        for tag in element.iter('tag'):
            if not PROBLEMCHARS.search(tag.attrib['k']):
                key_attrib = tag.attrib['k']
                type_attrib = 'regular'
                value_attrib = update_all(tag.attrib['v'], mapping)
                if tag.attrib['v'] == 'name':
                    value_attrib = cap_all(value_attrib)
                if LOWER_COLON.search(tag.attrib['k']):
                    type_attrib = (tag.attrib['k'].split(':'))[0]
                    key_attrib = ':'.join(tag.attrib['k'].split(':')[1:])
                tags.append({'id':element.attrib.get('id'), 'key':key_attrib, 'value': value_attrib, 'type': type_attrib})
        position = 0
        for nodes in element.iter('nd'):
            way_nodes.append({'id': element.attrib.get('id'), 'node_id':nodes.attrib.get('ref'), 'position': position})
            position += 1
        way_dict = {'way': way_attribs, 'way_nodes': way_nodes, 'way_tags': tags}
        return way_dict

# Helper Functions

# Gets element information from file
def get_element(osm_file, tags=('node', 'way', 'relation')):

    context = ET.iterparse(osm_file, events=('start', 'end'))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

# Validation to make sure matches schema
def validate_element(element, validator, schema=SCHEMA):

    if validator.validate(element, schema) is not True:
        field, errors = next(validator.errors.items())
        message_string = "\nElement of type '{0}' has the following errors:\n{1}"
        error_string = pprint.pformat(errors)
        
        raise Exception(message_string.format(field, error_string))

class UnicodeDictWriter(csv.DictWriter, object):

    def writerow(self, row):
        super(UnicodeDictWriter, self).writerow({
            k: v for k, v in row.items()  
        })

    def writerows(self, rows):
        for row in rows:
            self.writerow(row)

# Main Function to process file
def process_map(file_in, validate):

    with codecs.open(NODES_PATH, 'w') as nodes_file, \
         codecs.open(NODE_TAGS_PATH, 'w') as nodes_tags_file, \
         codecs.open(WAYS_PATH, 'w') as ways_file, \
         codecs.open(WAY_NODES_PATH, 'w') as way_nodes_file, \
         codecs.open(WAY_TAGS_PATH, 'w') as way_tags_file:

        nodes_writer = UnicodeDictWriter(nodes_file, NODE_FIELDS)
        node_tags_writer = UnicodeDictWriter(nodes_tags_file, NODE_TAGS_FIELDS)
        ways_writer = UnicodeDictWriter(ways_file, WAY_FIELDS)
        way_nodes_writer = UnicodeDictWriter(way_nodes_file, WAY_NODES_FIELDS)
        way_tags_writer = UnicodeDictWriter(way_tags_file, WAY_TAGS_FIELDS)

        nodes_writer.writeheader()
        node_tags_writer.writeheader()
        ways_writer.writeheader()
        way_nodes_writer.writeheader()
        way_tags_writer.writeheader()

        validator = cerberus.Validator()

        for element in get_element(file_in, tags=('node', 'way')):
            el = shape_element(element)
            if el:
                if validate is True:
                    validate_element(el, validator)

                if element.tag == 'node':
                    nodes_writer.writerow(el['node'])
                    node_tags_writer.writerows(el['node_tags'])
                elif element.tag == 'way':
                    ways_writer.writerow(el['way'])
                    way_nodes_writer.writerows(el['way_nodes'])
                    way_tags_writer.writerows(el['way_tags'])

if __name__ == '__main__':
    process_map(OSM_PATH, validate=True)