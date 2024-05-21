parser grammar JinjaGrammar;

options {
    tokenVocab=JinjaLexer;
}

start : expressions;

expression
    : inline_statement
    ;

expressions     : expression*;

list_literal            : LSQB SP? list_literal_values? SP? RSQB;
list_literal_values
    :
    (list_literal_value SP? COMMA SP?)*
    list_literal_value
    ;
list_literal_value
    : STRING_LITERAL
    | variable_name
    ;

variable_name : IDENTIFIER;

statement_include_template
    : STRING_LITERAL
    | list_literal
    | variable_name
    ;

statement_include_context
    : STATEMENT_INCLUDE_WITH_CONTEXT
    | STATEMENT_INCLUDE_WITHOUT_CONTEXT
    ;

statement_include
    : STATEMENT_ID_INCLUDE
        (SP statement_include_template)
        (SP STATEMENT_INCLUDE_IGNORE_MISSING)?
        (SP statement_include_context)?
    ;

statement_import_file
    : STRING_LITERAL
    | variable_name
    ;

statement_import
    : STATEMENT_ID_IMPORT SP statement_import_file SP STATEMENT_ID_IMPORT_AS SP variable_name
    ;

block_statement_id
    : STATEMENT_ID_BLOCK
    | STATEMENT_ID_SET
    ;

block_statement_with_parameters
    : block_statement_id
    | block_statement_id
    ;

block_statement_without_parameters
    : block_statement_id
    ;

block_statement_start_content
    : block_statement_without_parameters
    | block_statement_with_parameters
    ;

inline_statement_content
    : statement_include
    | statement_import
    ;

inline_statement            : STATEMENT_OPEN inline_statement_content STATEMENT_CLOSE;

block_statement_start       : STATEMENT_OPEN block_statement_start_content STATEMENT_CLOSE;
block_statement_end         : STATEMENT_OPEN END_STATEMENT_ID_PREFIX block_statement_id STATEMENT_CLOSE;

block_statement             : block_statement_start expressions block_statement_end;