# vim: et:ts=4:sw=4:fenc=utf-8

import os

def add_client_args(ap):
    ap.add_argument('--host', metavar='ADDR', default="localhost",
                      help='a remote host to connect with')
    ap.add_argument('--port', metavar='PORT', default="42424",
                      help='a port of the remote host to connect with')
    ap.add_argument('--sslpath', metavar='PATH', default=os.path.expandvars("${PMEVO_BASE}/ssl/"),
                      help='path to a folder containing an ssl key and certificate')


