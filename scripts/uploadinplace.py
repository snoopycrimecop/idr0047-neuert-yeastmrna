from hashlib import sha1
import logging
import os
from StringIO import StringIO
import omero.clients
import omero.cli

log = logging.getLogger(__file__)
# log.setLevel(logging.DEBUG)


def upload_ln_s(filepath, conn, omero_data_dir, mimetype):
    """
    Simulate an in-place ln-s upload by creating an empty file, replacing it
    with a symlink, and updating the OriginalFile metadata.

    Requires write access to the omero.data.dir Files directory

    :param filepath: Path to the file to be symlinked into OMERO
    :param conn: Connected BlitzGateway object
    :param omero_data_dir: The OMERO data directory
    :param mimetype: The mimetype to be assigned to the file in OMERO
    :return: The wrapped OriginalFile for the symlinked file
    """
    BUFSIZE = 1048576
    abspath = os.path.abspath(filepath)
    filedir = os.path.dirname(abspath)
    filename = os.path.basename(abspath)

    log.info('Creating empty OriginalFile placeholder')
    placeholder = StringIO('')
    fo = conn.createOriginalFileFromFileObj(
        placeholder, filedir, filename, 0, mimetype=mimetype)
    omero_path = os.path.join(
        omero_data_dir, 'Files', omero.util.long_to_path(fo.id))

    log.info('OriginalFile:%d Deleting %s', fo.id, omero_path)
    os.remove(omero_path)

    log.info('OriginalFile:%d Symlinking %s to %s', fo.id, abspath, omero_path)
    os.symlink(abspath, omero_path)

    log.info('OriginalFile:%d Getting size and checksum', fo.id)
    size = os.path.getsize(abspath)
    h = sha1()
    with open(abspath) as f:
        while True:
            data = f.read(BUFSIZE)
            if not data:
                break
            h.update(data)
    hash = h.hexdigest()

    log.info('OriginalFile:%d Saving size:%d and checksum:%s',
             fo.id, size, hash)
    fo.setSize(omero.rtypes.rlong(size))
    fo.setHash(omero.rtypes.rstring(hash))
    chk = omero.model.ChecksumAlgorithmI()
    chk.setValue(omero.rtypes.rstring(
        omero.model.enums.ChecksumAlgorithmSHA1160))
    fo.setHasher(chk)
    fo.save()
    return fo


# filepath = '/uod/idr/hello.txt'
# omero_data_dir = '/OMERO'
# with omero.cli.cli_login() as c:
#     conn = omero.gateway.BlitzGateway(client_obj=c.get_client())
#     upload_ln_s(filepath, conn, omero_data_dir, mimetype='mime/type')
