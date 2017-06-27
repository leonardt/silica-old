# Syntax
Extends [mantle](https://github.com/phanrahan/mantle) syntax with
```
S ::= ...
    | if ( E ) { S* } else { S* }
    | if ( E ) { S* }
    | while ( E ) { S* }
    | for ( Id in range(Num) { S* }  # TODO: Should we support more than ranges?
    | yield
    | yield from Id
```
