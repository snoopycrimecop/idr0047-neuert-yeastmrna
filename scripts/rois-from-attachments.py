#!/usr/bin/env python
# coding: utf-8

# In[1]:


from os import (
    SEEK_CUR,
    SEEK_END,
    SEEK_SET,
)

class OriginalFileLike(object):
    """
    Based on
    https://github.com/openmicroscopy/openmicroscopy/blob/v5.4.7/components/tools/OmeroPy/src/omero/gateway/__init__.py#L5232
    https://docs.python.org/2/library/stdtypes.html#file-objects
    """
    def __init__(self, originalfile, bufsize=2621440):
        self.originalfile = originalfile
        self.bufsize = bufsize
        self.rfs = self.originalfile._conn.createRawFileStore()
        self.rfs.setFileId(self.originalfile.id)
        self.pos = 0

    def __iter__(self):
        return self.originalfile.getFileInChunks(self.bufsize)

    def seek(self, n, mode=0):
        if mode == SEEK_SET:
            self.pos = n
        elif mode == SEEK_CUR:
            self.pos += n
        elif mode == SEEK_END:
            self.pos = self.rfs.size() + n
        else:
            raise ValueError('Invalid mode: %s' % mode)

    def tell(self):
        return self.pos

    def read(self, n=-1):
        buf = ''
        if n < 0:
            endpos = self.rfs.size()
        else:
            endpos = min(self.pos + n, self.rfs.size())
        while self.pos < endpos:
            nread = min(self.bufsize, endpos - self.pos)
            buf += self.rfs.read(self.pos, nread)
            self.pos += nread
        return buf

    def close(self):
        self.rfs.close()

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.close()


# In[2]:


import omero.clients
from omero.gateway import BlitzGateway
from omero.rtypes import rdouble, rint
from getpass import getpass
from scipy.io import loadmat
#import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import re

pd.set_option('max_rows', 5)


# In[3]:


username = raw_input('username: ')
password = getpass()


def connect(username, password):
    conn = BlitzGateway(
        username,
        password,
        host='localhost',
        port=4064,
        secure=True)
    connected = conn.connect()
    assert connected
    conn.c.enableKeepAlive(60)
    return conn


# In[4]:


def get_label_image(im):
    filename = ''
    for ann in im.listAnnotations():
        try:
            filename = ann.getFile().name
            if re.match('M_Lab_.+\\.mat', filename):
                print 'Found: %s' % filename
                break
        except AttributeError:
            continue
    if not filename:
        raise Exception('Failed to get label image for %s' % im.name)
    with OriginalFileLike(ann.getFile()) as f:
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
    #print (x0, y0, w, h)

    mask = omero.model.MaskI()
    # BUG in older versions of Numpy:
    # https://github.com/numpy/numpy/issues/5377
    # Need to convert to an int array
    #mask.setBytes(np.packbits(submask))
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
    for index in xrange(1, int(labels.max()) + 1):
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


# In[5]:


conn = connect(username, password)
print('Connected')
project = conn.getObject('Project', attributes={'name': 'idr0047-neuert-yeastmRNA'})
#images = [conn.getObject('Image', 4010034)]
missing = []
for dataset in project.listChildren():
    if dataset.name == 'processed':
        continue
    images = list(dataset.listChildren())
    print(len(images))
    for im in images:
        if im.name.startswith('M_') or im.name.startswith('SD_') or '.companion.ome' in im.name:
            continue
        try:
            rois = create_rois(im)
            save_rois(conn, im, rois)
        except Exception as e:
            print e
            missing.append((im.id, im.name))
            # raise

if missing:
    print 'No segmentations found for:\n%s' % '\n'.join(m[1] for m in missing)


# In[ ]:

conn.close()
