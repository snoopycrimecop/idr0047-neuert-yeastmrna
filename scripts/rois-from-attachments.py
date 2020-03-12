#!/usr/bin/env python
# coding: utf-8

import omero.clients
import omero.cli
from omero.rtypes import rdouble, rint
from scipy.io import loadmat
import numpy as np
import re


def get_label_image(im):
    filename = ''
    for ann in im.listAnnotations():
        try:
            filename = ann.getFile().name
            if re.match('M_Lab_.+\\.mat', filename):
                print('Found: %s' % filename)
                break
        except AttributeError:
            continue
    if not filename:
        raise Exception('Failed to get label image for %s' % im.name)
    with ann.getFile().asFileObj() as f:
        mat = loadmat(f)
        return mat['cells']


def roi_from_binary_image(binim, rgba):
    # Find bounding box to minimise size of mask
    xmask = binim.sum(0).nonzero()[0]
    ymask = binim.sum(1).nonzero()[0]
    x0 = min(xmask)
    w = max(xmask) - x0 + 1
    y0 = min(ymask)
    h = max(ymask) - y0 + 1
    submask = binim[y0:(y0 + h), x0:(x0 + w)]
    # print (x0, y0, w, h)

    mask = omero.model.MaskI()
    # BUG in older versions of Numpy:
    # https://github.com/numpy/numpy/issues/5377
    # Need to convert to an int array
    # mask.setBytes(np.packbits(submask))
    mask.setBytes(np.packbits(np.asarray(submask, dtype=int)))
    mask.setWidth(rdouble(w))
    mask.setHeight(rdouble(h))
    mask.setX(rdouble(x0))
    mask.setY(rdouble(y0))

    ch = omero.gateway.ColorHolder.fromRGBA(*rgba)
    mask.setFillColor(rint(ch.getInt()))

    roi = omero.model.RoiI()
    roi.addShape(mask)
    return roi


def create_rois(im):
    labels = get_label_image(im)
    print(im.name, labels.shape, labels.min(), labels.max())
    rois = []
    for index in range(1, int(labels.max()) + 1):
        rgba = (128, 128, 128, 128)
        roi = roi_from_binary_image(labels == index, rgba)
        rois.append(roi)
    return rois


def save_rois(conn, im, rois):
    print('Saving %d ROIs for image %d:%s' % (len(rois), im.id, im.name))
    us = conn.getUpdateService()
    for roi in rois:
        # Due to a bug need to reload the image for each ROI
        im = conn.getObject('Image', im.id)
        roi.setImage(im._obj)
        roi1 = us.saveAndReturnObject(roi)
        assert roi1


def main(conn):
    project = conn.getObject(
        'Project', attributes={'name': 'idr0047-neuert-yeastmrna/experimentA'})
    missing = []
    for dataset in project.listChildren():
        if dataset.name == 'processed':
            continue
        images = list(dataset.listChildren())
        print(len(images))
    # For testing with two images:
    # `omero delete Image/Roi:4010034,4010056 --report`
    # images = conn.getObjects('Image', [4010034, 4010056])
        for im in images:
            if (im.name.startswith('M_') or im.name.startswith('SD_') or
                    '.companion.ome' in im.name):
                continue
            try:
                rois = create_rois(im)
                save_rois(conn, im, rois)
            except Exception as e:
                print(e)
                missing.append((im.id, im.name))
                # raise

    if missing:
        print('No segmentations found for:\n%s' %
              '\n'.join(m[1] for m in missing))


if __name__ == '__main__':
    with omero.cli.cli_login() as c:
        conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
        main(conn)
