#!/usr/bin/env python
# Generate companion files


import os
import uuid
import xml.etree.ElementTree as ET

BASE_DIRECTORY = os.environ.get(
    "BASE_DIRECTORY", "/uod/idr/filesets/idr0047-neuert/")

EXPERIMENTS = ['Exp1_rep1', 'Exp1_rep2', 'Exp2_rep1', 'Exp2_rep2', 'Exp2_rep3']
TIMEPOINTS = [0, 1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 50, 55]

OME_ATTRIBUTES = {
    'xmlns': 'http://www.openmicroscopy.org/Schemas/OME/2016-06',
    'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
    'xmlns:OME': 'http://www.openmicroscopy.org/Schemas/OME/2016-06',
    'xsi:schemaLocation': 'http://www.openmicroscopy.org/Schemas/OME/2016-06 \
http://www.openmicroscopy.org/Schemas/OME/2016-06/ome.xsd',
}

IMAGES = [
    {
        'Image': {'ID': 'Image:0', 'Name': '3D images'},
        'Pixels': {
            'ID': 'Pixels:0:0',
            'DimensionOrder': 'XYZTC',
            'Type': 'uint16',
            'SizeX': '2048',
            'SizeY': '2048',
            'SizeZ': '25',
            'SizeC': '5',
            'SizeT': '1',
        },
        'Channels': [
            {'Color': '65535', 'ID': 'Channel:0:0',
             'Name': 'Nuclei', 'SamplesPerPixel': '1'},
            {'Color': '-16776961', 'ID': 'Channel:0:1',
             'Name': 'CTT1 filter', 'SamplesPerPixel': '1'},
            {'Color': '-16776961', 'ID': 'Channel:0:2',
             'Name': 'CTT1 immax', 'SamplesPerPixel': '1'},
            {'Color': '16711935', 'ID': 'Channel:0:3',
             'Name': 'STL1 filter', 'SamplesPerPixel': '1'},
            {'Color': '16711935', 'ID': 'Channel:0:4',
             'Name': 'STL1 immax', 'SamplesPerPixel': '1'},
        ],
        'TIFFData': [
            'M_nuclei_%s_nuclei3D.tiff',
            'SD_mRNA_%s_CY53Dfilter.tiff',
            'SD_mRNA_%s_CY53D3immax.tiff',
            'SD_mRNA_%s_TMR3Dfilter.tiff',
            'SD_mRNA_%s_TMR3D3immax.tiff'
        ]
    },
    {
        'Image': {'ID': 'Image:1', 'Name': 'Projections images'},
        'Pixels': {
            'ID': 'Pixels:1:0',
            'DimensionOrder': 'XYZTC',
            'Type': 'uint16',
            'SizeX': '2048',
            'SizeY': '2048',
            'SizeZ': '1',
            'SizeC': '7',
            'SizeT': '1',
        },
        'Channels': [
            {'Color': '-1', 'ID': 'Channel:1:0',
             'Name': 'Cells', 'SamplesPerPixel': '1'},
            {'Color': '-1', 'ID': 'Channel:1:1',
             'Name': 'Brightfield processed', 'SamplesPerPixel': '1'},
            {'Color': '65535', 'ID': 'Channel:1:2',
             'Name': 'Nuclei', 'SamplesPerPixel': '1'},
            {'Color': '-16776961', 'ID': 'Channel:1:3',
             'Name': 'CTT1 immax', 'SamplesPerPixel': '1'},
            {'Color': '-16776961', 'ID': 'Channel:1:4',
             'Name': 'CTT1 filt', 'SamplesPerPixel': '1'},
            {'Color': '16711935', 'ID': 'Channel:1:5',
             'Name': 'STL1 immax', 'SamplesPerPixel': '1'},
            {'Color': '16711935', 'ID': 'Channel:1:6',
             'Name': 'STL1 filt', 'SamplesPerPixel': '1'},
        ],
        'TIFFData': [
            'M_Lab_%s_Cells.tif',
            'M_Lab_%s_trans_plane.tif',
            'M_nuclei_%s_nuclei.tif',
            'SD_mRNA_%s_CY5max.tif',
            'SD_mRNA_%s_CY5maxF.tif',
            'SD_mRNA_%s_TMRmax.tif',
            'SD_mRNA_%s_TMRmaxF.tif',
        ],
    }
]


def create_companion(name):
    """Create a companion OME-XML for a given experiment"""
    root = ET.Element("OME", attrib=OME_ATTRIBUTES)
    for i in IMAGES:
        image = ET.SubElement(root, "Image", attrib=i["Image"])
        pixels = ET.SubElement(image, "Pixels", attrib=i["Pixels"])
        for channel in i["Channels"]:
            ET.SubElement(pixels, "Channel", attrib=channel)

        tiffs = i["TIFFData"]
        for t in range(len(tiffs)):
            tiffdata = ET.SubElement(pixels, "TiffData", attrib={
                "FirstC": str(t), "IFD": '0'})
            ET.SubElement(tiffdata, "UUID", attrib={
                "FileName": tiffs[t] % name}).text = str(uuid.uuid4())

    tree = ET.ElementTree(root)
    tree.write("%s.companion.ome" % name, encoding='utf-8',
               xml_declaration=True)


for experiment in EXPERIMENTS:
    for timepoint in TIMEPOINTS:
        create_companion("%s_%g" % (experiment, timepoint))
