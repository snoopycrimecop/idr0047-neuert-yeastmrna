#!/usr/bin/env python

# WARNING: This script will use your current OMERO login session if one
# exists. If you want to use a different login ensure you logout first.

import csv
import os
import omero.clients
import omero.cli


def list_files(rootdir):
    with open('idr0047-neuert-20180911-ftp.txt') as f:
        files = [line.strip() for line in f.readlines()]
        return files
    # TODO: Run this for real on the actual filesystem instead of using
    # a pre-generated list
    files = [os.path.join(fileparts[0], filename)
             for fileparts in os.walk(rootdir)
             for filename in fileparts[2]
             if fileparts[2]]

    uploads = [fn for fn in files
               if os.path.splitext(fn) not in ('.tif', '.tiff')]
    assert set(os.path.splitext(fn) for fn in uploads) == set(
        ['.csv', '.mat'])
    return uploads


def upload_and_attach(conn, uploads):
    datasets = {}
    for exp in uploads:
        ds = list(conn.getObjects('Dataset', attributes={'name': exp}))
        assert len(ds) == 1
        datasets[exp] = ds

    for (exp, filenames) in uploads.items():
        for filename in filenames:
            if filename.endswith('csv'):
                # https://tools.ietf.org/html/rfc7111
                mimetype = 'text/csv'
            else:
                # http://justsolve.archiveteam.org/wiki/MAT
                mimetype = 'application/x-matlab-data'

            fa = conn.createFileAnnfromLocalFile(
                filename,
                ns='idr.openmicroscopy.org/unstable/analysis/original',
                mimetype=mimetype,
            )
            datasets[exp].linkAnnotation(fa)


def parse_processed_file(filename, rootdir):
    """
    Create a mapping of processesd-file-path: dataset-or-image-name
    """
    attachmap = {}
    with open(filename) as f:
        for line in csv.reader(f, delimiter='\t', quotechar="'"):
            parent, windowspath, description = line
            if parent.startswith('#') or parent in ('Experiment', ''):
                continue
            filepath = os.path.join(rootdir, *windowspath.split('\\'))
            attachmap[filepath] = parent
    return attachmap


def get_omero_targets(conn, projectname):
    """
    Get all OMERO datasets and images in this project
    """
    project = conn.getObject('Project', attributes={'name': projectname})
    assert project
    datasets = {}
    images = {}
    for d in project.listChildren():
        datasets[d.name] = d
        for i in d.listChildren():
            images[i.name] = i
    return datasets, images


def main(conn):
    rootdir = '/uod/idr/filesets/idr0047-neuert/20180911-ftp'
    uploads = list_files(rootdir)
    attachmap = parse_processed_file(
        'idr0000-experimentB-processed.txt', rootdir)
    datasets, images = get_omero_targets(conn, 'idr0047-neuert')
    # Cross-check
    datasetsimages = set(datasets.keys()).union(images.keys())
    attach_without_target = set(attachmap.values()).difference(
        datasetsimages)
    assert attach_without_target == set(), sorted(attach_without_target)
    uploads_without_attach = set(uploads).difference(attachmap.keys())
    assert uploads_without_attach == set(), sorted(uploads_without_attach)


if __name__ == '__main__':
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
