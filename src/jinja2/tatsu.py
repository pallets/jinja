from tatsu import parse
import pprint

from .lexer import Lexer
from .utils import LRUCache

# cache for the lexers. Exists in order to be able to have multiple
# environments with the same lexer
_tatsu_lexer_cache = LRUCache(50)


def get_tatsu_lexer(environment):
    """Return a tatsu lexer which is probably cached."""
    key = (
        environment.block_start_string,
        environment.block_end_string,
        environment.variable_start_string,
        environment.variable_end_string,
        environment.comment_start_string,
        environment.comment_end_string,
        environment.line_statement_prefix,
        environment.line_comment_prefix,
        environment.trim_blocks,
        environment.lstrip_blocks,
        environment.newline_sequence,
        environment.keep_trailing_newline,
    )
    tatsu_lexer = _tatsu_lexer_cache.get(key)
    if tatsu_lexer is None:
        tatsu_lexer = TatsuLexer(environment)
        _tatsu_lexer_cache[key] = tatsu_lexer
    return tatsu_lexer


GRAMMAR = r'''
    @@grammar::CALC

    @@whitespace:://


    start = {expression}+ ;


    expression
        =
        | code
        | variable
        | comment
        | data:/(.|\n)/
        ;

    code
        = block_begin:'{%' {code_content:code_content}+ block_end:'%}' ;

    code_content
        = 
        | whitespace:/[\ \n]+/
        | name:/\w+/
        | operator:operator
        ;

    operator
        =
        | '+' | '-' | '/' | '//' | '*' | '**' | '~'
        | '[' | ']' | '(' | ')' | '{' | '}'
        | '==' | '!=' | '>' | '>=' | '<' | '<=' | '='
        | '.' | ':' | '|' | ',' | ';'
        ; 

    variable = variable_begin:'{{' {variable_content:variable_content}+ variable_end:'}}' ;

    variable_content
        = 
        | whitespace:/[\ \n]+/
        | name:/\w+/
        ;

    comment = comment_begin:'<!--' ~ {comment_data:comment_content}+ comment_end:'-->' ;

    comment_content = /([^-]|-(?!->)|\\n)/ ;
'''

def tatsu_tokenize(source):
        # use print for debug
        pprint.pprint(parse(GRAMMAR, source), indent=2, width=20)
        return parse(GRAMMAR, source)

def get_ast_tokens(lineno, ast):
    for item in ast.items():
        if isinstance(item[1], list):
            for item_ast in item[1]:
                for result in get_ast_tokens(lineno, item_ast):
                    yield result
        else:
            yield lineno.get(), item[0], item[1]
            lineno.add(item[1].count("\n"))

class Lineno():
    def __init__(self, value = 1):
        self.value = value

    def get(self):
        return self.value

    def add(self, number):
        self.value += number

class TatsuLexer(Lexer):
    def tokeniter(self, source, name, filename=None, state=None):
        tatsu_tokens = tatsu_tokenize(source)
        data = None
        lineno = Lineno()

        for token in tatsu_tokens:
            if token['data']:
                data = (data or "") + token['data']
            else:   # ast
                if data:
                    yield lineno.get(), 'data', data
                    lineno.add(data.count("\n"))
                    data = None
                for result in get_ast_tokens(lineno, token):
                    yield result
        
        if data:
            yield lineno.get(), 'data', data