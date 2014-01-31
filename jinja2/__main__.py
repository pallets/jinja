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


def parse_cmdline_vars(cmdline_vars, eval_values):
    args = dict(var.split('=', 1) for var in cmdline_vars)
    if eval_values:
        args = dict((key, eval(val)) for (key, val) in args.items())
    return args


def main(argv=None):
    import sys
    from argparse import ArgumentParser, FileType

    argv = argv or sys.argv

    parser = ArgumentParser(description='Expand Jinja2 template')
    parser.add_argument('template', help='template file to expand',
                        type=FileType('r'), nargs='?', default=sys.stdin)
    parser.add_argument('--var', '-v', action='append',
                        help='template variables (in X=Y format)')
    parser.add_argument('--eval', '-e', action='store_true', default=False,
                        help='eval arguments (e.g. "[1, 2]" -> [1, 2])')
    parser.add_argument('--output', '-o', help='output file',
                        type=FileType('w'), nargs='?', default=sys.stdout)

    args = parser.parse_args(argv[1:])

    tvars = parse_cmdline_vars(args.var or [], args.eval)

    # Fail on undefined
    env = Environment(undefined=StrictUndefined)
    template = env.from_string(args.template.read())

    args.output.write(template.render(tvars))


if __name__ == '__main__':
    main()
