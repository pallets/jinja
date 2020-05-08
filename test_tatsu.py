from tatsu.util import asjson
import json
import tatsu


with open('tatsu_grammar.txt', 'r') as tatsu_grammar:
    with open('test_template.jinja', 'r') as test_template:
        ast = tatsu.parse(tatsu_grammar.read(), test_template.read(), whitespace='')

        print(json.dumps(asjson(ast), indent=4))