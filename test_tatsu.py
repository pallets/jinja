from datetime import datetime
from tatsu.exceptions import FailedSemantics
from tatsu.util import asjson
import json
import pprint
import tatsu
import sys
from new_parser import parse_template
from jinja2.environment import Environment


with open('grammar.ebnf', 'r') as tatsu_grammar:
    with open('test_template.jinja', 'r') as test_template:
        template_string = test_template.read()

        grammar_start = datetime.now()

        grammar = tatsu.compile(tatsu_grammar.read())

        grammar_end = datetime.now()

        parse_start = datetime.now()

        ast = grammar.parse(template_string, whitespace='', parseinfo=True, semantics=JinjaSemantics())

        parse_end = datetime.now()

        with open('tatsu_jinja.json', 'w') as tatsu_ast_file:
            json.dump(asjson(ast), tatsu_ast_file, indent=2)

        new_parse_start = datetime.now()

        new_ast = parse_template(ast)

        new_parse_end = datetime.now()

        with open('tatsu_jinja.py', 'w') as new_ast_file:
            pprint.pprint(new_ast, indent=2, stream=new_ast_file)

        env = Environment(line_statement_prefix='#', line_comment_prefix='##')

        jinja_parse_start = datetime.now()

        jinja_ast = env.parse(template_string)

        jinja_parse_end = datetime.now()

        with open('parsed_jinja.py', 'w') as jinja_ast_file:
            pprint.pprint(jinja_ast, indent=2, stream=jinja_ast_file)

        print("Grammar", grammar_end - grammar_start, file=sys.stderr)
        print("Parser", parse_end - parse_start, file=sys.stderr)
        print("New Parser", new_parse_end - new_parse_start, file=sys.stderr)
        print("Jinja Parser", jinja_parse_end - jinja_parse_start, file=sys.stderr)
