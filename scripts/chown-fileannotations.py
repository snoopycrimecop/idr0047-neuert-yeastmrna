#!/usr/bin/env python

# WARNING: This script will use your current OMERO login session if one
# exists. If you want to use a different login ensure you logout first.

import sys
import omero.clients
import omero.cli

DRYRUN = False


def command_and_wait(client, cmd, cmdargs, wait):
    """
    :cmd: Command from `omero.cmd`, e.g. `omero.cmd.FindChildren`
    :cmdargs: Dictionary of argumemnts for `cmd`
    :wait: Maximum wait in seconds for command to complete
    :return: Command response
    """
    req = cmd(**cmdargs)
    handle = client.sf.submit(req)
    cb = omero.callbacks.CmdCallbackI(client, handle)
    cb.loop(wait * 2, 500)
    rsp = cb.getResponse()
    return rsp


def getFileAnnotations(client, targetType, targetId, wait):
    rsp = command_and_wait(client, omero.cmd.FindChildren, {
        'targetObjects': {targetType: [targetId]},
        'typesOfChildren': ['FileAnnotation']},
        wait)
    return rsp.children['ome.model.annotations.FileAnnotation']


def chown(client, userid, fileannids, wait):
    rsp = command_and_wait(
        client, omero.cmd.Chown2,
        {
            'targetObjects': {'FileAnnotation': fileannids},
            'userId': userid,
            'dryRun': DRYRUN,
        },
        wait)
    return rsp


def main(client, userid, datasetids):
    for d in datasetids:
        print('Dataset:%d' % d)
        fas = getFileAnnotations(client, 'Dataset', d, 60)
        print('  Chowning %d FileAnnotations to user %d' % (len(fas), userid))
        rsp = chown(client, userid, fas, 300)
        for (key, value) in rsp.includedObjects.items():
            print('  %s: %d objects' % (key, len(value)))


if __name__ == '__main__':
    userid = int(sys.argv[1])
    datasetids = [int(arg) for arg in sys.argv[2:]]
    with omero.cli.cli_login() as c:
        main(c.get_client(), userid, datasetids)
