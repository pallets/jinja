#!/usr/bin/env python
'''Command line for expanding Jinja2 templates.

Template variables can are passed via the command line (using -vX=Y)

Example:

    $ echo 'Hello {{name}}' > template.txt
    $ jj2.py -v name=Bugs template.txt
    Hello Bugs
    $
'''


from . import Environment, StrictUndefined


def parse_value(value):
    prefix = 'py:'
    if value[:3] != prefix:
        return value

    return eval(value[len(prefix):])


def parse_cmdline_vars(cmdline_vars):
    kvs = (var.split('=', 1) for var in cmdline_vars)
    return dict((var, parse_value(val)) for var, val in kvs)


def main(argv=None):
    import sys
    from argparse import ArgumentParser, FileType

    argv = argv or sys.argv

    parser = ArgumentParser(description='Expand Jinja2 template')
    parser.add_argument('template', help='template file to expand',
                        type=FileType('r'), nargs='?', default=sys.stdin)
    parser.add_argument(
        '--var', '-v', action='append',
        help='template variables (in X=Y format, prefix with py: to eval)')
    parser.add_argument('--output', '-o', help='output file',
                        type=FileType('w'), nargs='?', default=sys.stdout)

    args = parser.parse_args(argv[1:])

    tvars = parse_cmdline_vars(args.var or [])

    # Fail on undefined
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(args.template.read())

    args.output.write(template.render(tvars))


if __name__ == '__main__':
    main()
