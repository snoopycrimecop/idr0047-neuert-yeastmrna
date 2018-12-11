#!/usr/bin/env python
# Generate companion files

from datetime import date
import glob
import os
import os.path
import uuid
import xml.etree.ElementTree as ET


BASE_DIRECTORY = os.environ.get(
    "BASE_DIRECTORY", "/uod/idr/filesets/idr0047-neuert-yeastmRNA")
FTP_FOLDER = "20181016-ftp"
RAW_IMAGES_DIR = "#1_Raw_Images"
ANALYZED_IMAGES_DIR = "#2_Analyzed_images"

# Based on Table 2: Experimental data sets and conditions
EXPERIMENTS = {
    'Exp1_rep1': [0, 1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
    'Exp1_rep2': [0, 1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
    'Exp2_rep1': [0, 1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
    'Exp2_rep2': [0, 1, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55],
    'Exp2_rep3': [0, 2, 4, 6, 8, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55]
    }
POSITIONS = ['im1', 'im2', 'im3', 'im4']

# Missing raw images as confirmed by the submitters
MISSING_IMAGES = set([
    'Exp1_rep1_50min_im4.tif',
    'Exp1_rep2_50min_im4.tif',
    'Exp2_rep3_40min_im3.tif'])

# Review raw images
raw_images_list = map(
    os.path.basename,
    glob.glob("%s/%s/*/%s/*" % (BASE_DIRECTORY, FTP_FOLDER, RAW_IMAGES_DIR)))
expected_images_list = [
    '%s_%gmin_%s.tif' % (x, y, z) for x in EXPERIMENTS for
    y in EXPERIMENTS[x] for z in POSITIONS]
missing_raw_images = set(expected_images_list) - set(raw_images_list)
assert missing_raw_images == MISSING_IMAGES, missing_raw_images
# TODO: check all extra images end with im5.tif to im8.tif
extra_raw_images = set(raw_images_list) - set(expected_images_list)

sd_mRNA_mat_list = map(
    os.path.basename,
    glob.glob("%s/%s/*/%s/SD_mRNA*.mat" % (
        BASE_DIRECTORY, FTP_FOLDER, ANALYZED_IMAGES_DIR)))
expected_mat_list = ['SD_mRNA_%s.mat' % x[:-4] for x in raw_images_list]
assert not sorted(set(expected_mat_list) - set(sd_mRNA_mat_list))
assert not sorted(set(sd_mRNA_mat_list) - set(expected_mat_list))


# Create secondary folder for analyzed files with companions
COMPANION_DIRECTORY = os.path.join(
    BASE_DIRECTORY, "%s-companions" % date.today().strftime("%Y%m%d"))

for e in EXPERIMENTS:
    experiment_source_directory = os.path.join(BASE_DIRECTORY, FTP_FOLDER, e)
    experiment_target_directory = os.path.join(COMPANION_DIRECTORY, e)
    if not os.path.exists(experiment_target_directory):
        os.makedirs(experiment_target_directory)
        os.symlink(
            os.path.join(experiment_source_directory, ANALYZED_IMAGES_DIR),
            os.path.join(experiment_target_directory, ANALYZED_IMAGES_DIR))

# Generate companion OME-XML
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
            ANALYZED_IMAGES_DIR + '/M_nuclei_%s_nuclei3D.tiff',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_CY53Dfilter.tiff',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_CY53D3immax.tiff',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_TMR3Dfilter.tiff',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_TMR3D3immax.tiff'
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
            ANALYZED_IMAGES_DIR + '/M_Lab_%s_Cells.tif',
            ANALYZED_IMAGES_DIR + '/M_Lab_%s_trans_plane.tif',
            ANALYZED_IMAGES_DIR + '/M_nuclei_%s_nuclei.tif',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_CY5max.tif',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_CY5maxF.tif',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_TMRmax.tif',
            ANALYZED_IMAGES_DIR + '/SD_mRNA_%s_TMRmaxF.tif',
        ],
    }
]


def create_companion(experiment, timepoint, position):
    """Create a companion OME-XML for a given experiment"""
    root = ET.Element("OME", attrib=OME_ATTRIBUTES)
    name = "%s_%gmin_%s" % (experiment, timepoint, position)
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
                "FileName": tiffs[t] % (name)
                }).text = str(uuid.uuid4())

    tree = ET.ElementTree(root)
    tree.write("%s/%s/%s.companion.ome" % (
        COMPANION_DIRECTORY, experiment, name),
        encoding='utf-8', xml_declaration=True)


for experiment in EXPERIMENTS:
    for timepoint in EXPERIMENTS[experiment]:
        for position in POSITIONS:
            if ('%s_%gmin_%s.tif' % (experiment, timepoint, position) in
                    MISSING_IMAGES):
                continue
            create_companion(experiment, timepoint, position)
