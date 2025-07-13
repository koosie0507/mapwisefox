expr ::= output_spec_expr
       | compound_expr ;

output_spec_expr ::= "[" output_spec compound_expr "]" ;
output_spec ::= "->" ("query" | "filter" | "both") ":" ;

compound_expr ::= group_expr
                | binary_expr
                | unary_expr
                | atomic_expr ;

group_expr ::= "(" expr ")" ;
binary_expr ::= expr boolean_op expr ;
unary_expr  ::= "!" expr
              | match_expr ;
match_expr ::= match_op "(" compound_expr ")" ;
match_op ::= "approx"
           | "nearest (" number ")"
           | "match (" match_type ")" ;

atomic_expr ::= value_expr attr_clause? ;
value_expr ::= STRING_LITERAL ;
attr_clause ::= "in" field_list ;
field_list ::= field_name ("," field_name)* ;
boolean_op ::= "&" | "|" ;
field_name ::= IDENTIFIER ;
match_type ::= "strict" | "loose" | "regex" ;

number ::= DIGIT+ ;
STRING_LITERAL ::= '"' { any character except '"' }* '"' ;
IDENTIFIER ::= LETTER (LETTER | DIGIT | "_")* ;
