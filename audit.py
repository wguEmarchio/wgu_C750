import xml.etree.cElementTree as ET
from collections import defaultdict
import re
import pprint

OSMFILE = 'map_slc'
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)

# Expected values for street types
expected = ['Street', 'Avenue', 'Boulevard', 'Drive', 'Court', 'Place', 'Square', 'Lane', 'Road', 'Trail', 'Parkway', 'Commons',
           'Circle', 'Cove', 'East', 'West', 'North', 'South','Terrace', 'Village', 'Way']

# Check if street type and if in Expected list
def audit_street_type(street_types, street_name):
    m = street_type_re.search(street_name)
    if m:
        street_type = m.group()
        if street_type not in expected:
            street_types[street_type].add(street_name)

# Check if street type           
def is_street_name(elem):
    return (elem.attrib['k'] == 'addr:street')

# Audits file to list all street types found
def audit(osmfile):
    osm_file = open(osmfile, 'r')
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=('start',)):
        
        if elem.tag == 'node' or elem.tag == 'way':
            for tag in elem.iter('tag'):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
    osm_file.close()
    print(street_types)
    return street_types

# Run audit
audit('map_slc')