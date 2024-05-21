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

STATEMENT_OPEN      : '{%';
STATEMENT_CLOSE     : '%}';

EXPRESSION_OPEN     : '{{';
EXPRESSION_CLOSE    : '}}';

COMMENT_OPEN        : '{#';
COMMENT_CLOSE       : '#}';

SP              : [ \t\f]+;

IDENTIFIER      : [a-zA-Z_][a-zA-Z0-9_]*;

// Statement identifiers for built-in statements

STATEMENT_ID_BLOCK      : 'block';
STATEMENT_ID_IMPORT     : 'import';
STATEMENT_ID_INCLUDE    : 'include';
STATEMENT_ID_RAW        : 'raw';
STATEMENT_ID_SET        : 'set';

END_STATEMENT_ID_PREFIX    : 'end';