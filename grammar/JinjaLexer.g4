lexer grammar JinjaLexer;

TRUE_LOWER      : 'true';
TRUE_PY         : 'True';
TRUE
    : TRUE_LOWER
    | TRUE_PY
    ;

FALSE_LOWER     : 'false';
FALSE_PY        : 'False';
FALSE
    : FALSE_LOWER
    | FALSE_PY
    ;

BOOLEAN
    : TRUE
    | FALSE
    ;

NONE_LOWER      : 'none';
NONE_PY         : 'None';
NONE
    : NONE_LOWER
    | NONE_PY
    ;

LPAR            : '(';
LSQB            : '[';
LBRACE          : '{';
RPAR            : ')';
RSQB            : ']';
RBRACE          : '}';
DOT             : '.';
COLON           : ':';
COMMA           : ',';
SEMI            : ';';
PLUS            : '+';
MINUS           : '-';
STAR            : '*';
SLASH           : '/';
VBAR            : '|';
AMPER           : '&';
LESS            : '<';
GREATER         : '>';
EQUAL           : '=';
PERCENT         : '%';
EQEQUAL         : '==';
NOTEQUAL        : '!=';
LESSEQUAL       : '<=';
GREATEREQUAL    : '>=';
TILDE           : '~';
CIRCUMFLEX      : '^';
LEFTSHIFT       : '<<';
RIGHTSHIFT      : '>>';
DOUBLESTAR      : '**';
DOUBLESLASH     : '//';
AT              : '@';
RARROW          : '->';
ELLIPSIS        : '...';
EXCLAMATION     : '!';

STATEMENT_OPEN      : '{%' SP?;
STATEMENT_CLOSE     : SP? '%}';

EXPRESSION_OPEN     : '{{';
EXPRESSION_CLOSE    : '}}';

COMMENT_OPEN        : '{#';
COMMENT_CLOSE       : '#}';

STRING_LITERAL                           : STRING_LITERAL_SINGLE_QUOTE | STRING_LITERAL_DOUBLE_QUOTE;
fragment STRING_LITERAL_SINGLE_QUOTE     : '\'' (~[\\\r\n'])* '\'';
fragment STRING_LITERAL_DOUBLE_QUOTE     : '"' (~[\\\r\n"])* '"';

SP              : [ \t\f]+;

// Statement identifiers for built-in statements

STATEMENT_ID_BLOCK      : 'block';
STATEMENT_END_ID_BLOCK  : 'endblock';
STATEMENT_ID_FROM       : 'from';
STATEMENT_ID_IMPORT     : 'import';
STATEMENT_ID_INCLUDE    : 'include';
STATEMENT_ID_RAW        : 'raw';
STATEMENT_ID_SET        : 'set';
STATEMENT_END_ID_SET    : 'endset';

STATEMENT_ID_IMPORT_AS  : 'as';

STATEMENT_INCLUDE_IGNORE_MISSING    : 'ignore missing';
STATEMENT_INCLUDE_WITH_CONTEXT      : 'with context';
STATEMENT_INCLUDE_WITHOUT_CONTEXT   : 'without context';

END_STATEMENT_ID_PREFIX    : 'end';

IDENTIFIER                       : IDENTIFIER_START IDENTIFIER_CONTINUE*;
fragment IDENTIFIER_START        : [a-zA-Z_];
fragment IDENTIFIER_CONTINUE     : [a-zA-Z0-0_];
