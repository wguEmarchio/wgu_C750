import xml.etree.cElementTree as ET
import pprint
import re

# Regex
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')

# Checks tags for different kinds of characters and formats
def key_type(element, keys):
    if element.tag == 'tag':
        if lower.search(element.attrib['k']):
            keys['lower'] += 1
        elif lower_colon.search(element.attrib['k']):
            keys['lower_colon'] += 1
        elif problemchars.search(element.attrib['k']):
            keys['problemchars'] += 1
        else:
            keys['other'] += 1
        pass
    
    return keys

# Main function - counts up number of different types of tags
def process_keys(filename):
    keys = {'lower': 0, 'lower_colon': 0, 'problemchars': 0, 'other': 0}
    for _, element in ET.iterparse(filename):
        keys = key_type(element, keys)
        
    return keys