from datetime import datetime
from tatsu.util import asjson
import json
import tatsu
import sys


with open('grammar.ebnf', 'r') as tatsu_grammar:
    with open('test_template.jinja', 'r') as test_template:
        grammar_start = datetime.now()

        grammar = tatsu.compile(tatsu_grammar.read())

        grammar_end = datetime.now()

        parse_start = datetime.now()

        ast = grammar.parse(test_template.read(), whitespace='')

        parse_end = datetime.now()

        print(json.dumps(asjson(ast), indent=2))

        print("Grammar", grammar_end - grammar_start, file=sys.stderr)
        print("Parser", parse_end - parse_start, file=sys.stderr)