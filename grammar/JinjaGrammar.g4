parser grammar JinjaGrammar;

options {
    tokenVocab=JinjaLexer;
}

expression
    : block_statement
    | inline_statement
    ;

expressions     : expression*;

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

inline_statement_id
    : STATEMENT_ID_IMPORT
    | STATEMENT_ID_INCLUDE
    | STATEMENT_ID_SET
    ;

inline_statement            : STATEMENT_OPEN inline_statement_id STATEMENT_CLOSE;

block_statement_start       : STATEMENT_OPEN block_statement_id STATEMENT_CLOSE;
block_statement_end         : STATEMENT_OPEN END_STATEMENT_ID_PREFIX block_statement_id STATEMENT_CLOSE;

block_statement             : block_statement_start expressions block_statement_end;