import os
import xml.dom.minidom
import xml.etree.ElementTree as ET

import parseXML

def encode(raw_xml):
    parsed_xml, hierarchy_xml = parse(raw_xml)
    tree = ET.fromstring(parsed_xml)

    # remove bounds attribute, which is unnecessary for gpt.
    for element in tree.iter():
        if 'bounds' in element.attrib:
            del element.attrib['bounds']
        if 'important' in element.attrib:
            del element.attrib['important']
        if 'class' in element.attrib:
            del element.attrib['class']

    encoded_xml = ET.tostring(tree, encoding='unicode')
    pretty_xml = xml.dom.minidom.parseString(encoded_xml).toprettyxml()

    return parsed_xml, hierarchy_xml, encoded_xml, pretty_xml


def parse(raw_xml):
    parsed_xml = parseXML.parse(raw_xml)
    hierarchy_xml = parseXML.hierarchy_parse(parsed_xml)
    return parsed_xml, hierarchy_xml


# appname = "com.google.android.apps.youtube.music"
# task = "playSong"
# index = 1
# save_dir = f"layouts/{appname}/{task}/"
# raw_xml_path = save_dir + f"{str(index)}.xml"

# parsed_xml_path = save_dir + f"{str(index)}_parsed.xml"
# hierarchy_parsed_xml_path = save_dir + f"{str(index)}_hierarchy_parsed.xml"
# encoded_xml_path = save_dir + f"{str(index)}_encoded.xml"
# pretty_xml_path = save_dir + f"{str(index)}_pretty.xml"

save_dir = f"../layout/"
raw_xml_path = save_dir + f"layout.xml"
parsed_xml_path = save_dir + f"layout_parsed.xml"
hierarchy_parsed_xml_path = save_dir + f"layout_hierarchy_parsed.xml"
encoded_xml_path = save_dir + f"layout_encoded.xml"
pretty_xml_path = save_dir + f"layout_pretty.xml"

with open(raw_xml_path, "r") as f:
    raw_xml = f.read()

# parsed_xml = parseXML.parse(raw_xml)
# hierarchy_xml = parseXML.hierarchy_parse(parsed_xml)

parsed_xml, hierarchy_xml, encoded_xml, pretty_xml = encode(raw_xml)

with open(parsed_xml_path, 'w', encoding='utf-8') as f:
    f.write(parsed_xml)
with open(hierarchy_parsed_xml_path, 'w', encoding='utf-8') as f:
    f.write(hierarchy_xml)
with open(encoded_xml_path, 'w', encoding='utf-8') as f:
    f.write(encoded_xml)
with open(pretty_xml_path, 'w', encoding='utf-8') as f:
    f.write(pretty_xml)
    