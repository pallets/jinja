from datetime import datetime
import pprint
from jinja2.environment import Environment
from jinja2.parser import Parser


with open('grammar.ebnf', 'r') as tatsu_grammar:
    with open('test_template.jinja', 'r') as test_template:
        template_string = test_template.read()

        env = Environment(line_statement_prefix='#', line_comment_prefix='##')
        parser = Parser(env, template_string)

        new_parse_start = datetime.now()

        new_ast = parser.parse()

        new_parse_end = datetime.now()

        with open('tatsu_jinja.py', 'w') as new_ast_file:
            pprint.pprint(new_ast, indent=2, stream=new_ast_file)

        jinja_parse_start = datetime.now()

        jinja_ast = parser.parse_old()

        jinja_parse_end = datetime.now()

        with open('parsed_jinja.py', 'w') as jinja_ast_file:
            pprint.pprint(jinja_ast, indent=2, stream=jinja_ast_file)

        print("New Parser", new_parse_end - new_parse_start, file=sys.stderr)
        print("Jinja Parser", jinja_parse_end - jinja_parse_start, file=sys.stderr)
