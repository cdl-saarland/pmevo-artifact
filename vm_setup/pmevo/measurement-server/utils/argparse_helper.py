# vim: et:ts=4:sw=4:fenc=utf-8


def add_server_args(ap):
    ap.add_argument('--port', metavar='PORT', type=int, default="42424",
                    help='the port to listen for requests')
    ap.add_argument('--sslpath', metavar='PATH', default="./ssl",
                    help='the path to a folder containing an SSL key, certificate and ca file')


def add_bool_arg(parser, name, helpText, default=False):
        group = parser.add_mutually_exclusive_group(required=False)
        group.add_argument('--' + name, dest=name, action='store_true', help=helpText)
        group.add_argument('--no-' + name, dest=name, action='store_false',
                           help='the negation of ' + name)
        parser.set_defaults(**{name: default})
