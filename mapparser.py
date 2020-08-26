import xml.etree.cElementTree as ET
import pprint

# Counts number of first-level tags in file
def count_tags(filename):
    tag_dict = {}
    for event, elem in ET.iterparse(filename):
        if not elem.tag in tag_dict:
            tag_dict[elem.tag] = 1
        else:
            tag_dict[elem.tag] += 1
    print(tag_dict)
    return tag_dict

count_tags('map_slc')