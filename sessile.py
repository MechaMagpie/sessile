'''
Language spec:
transform rule = [label, ":"] patterns "->" patterns;
patterns       = pattern, {" ", pattern};
pattern        = string | matcher | var
string         = """, char, {char}, """;
matcher        = label, "(", vars, ")";
label          = letter, {letter | number};
vars           = var, {", " var};
var            = upper_letter, {upper_letter};

For simplicity in the initial implementation, patterns must be seperated by whitespace.

Pattern match rule:
  Pattern matches item(s) if:
    1) pattern is a string, item is same as pattern
    2) pattern is a labelled matcher, item(s) match LHS of pattern

Transform apply rule:
  Recursively apply each pattern by replacing the items that matched the LHS with the corresponding RHS, with the same variable bindings.

Matcher variable bindings:
  On the match step, variables are bound to the raw strings matching the variables in the subpattern's LHS, in the order introduced on the LHS.
  On the apply step, variable bindings are used to compute the resulting RHS, in the order introduced on the LHS.
  All variables used on the RHS must be introduced on the LHS, but not all variables need to be used.
  Special case:
    For rules with (unambiguous) arity > 1 a single argument will be interpreted as a list of arguments.

Program flow:
  System loads one or more rule files, then a number of text files. For each text file, system repeatedly reads a single token (dependent on the current read mode) and then attempts to apply every rule in the order introduced, restarting after each successful application. When the entire file is read and no more rules apply, system prints the entire stack to an output file.

Rule files:
  Rule files contain newline seperated optionally labelled rules. Labelled rules can be used as matchers in other rules, but will not be applied directly. Multiple rules can be introduced with one label, the system will try each correct arity variation when matching. RHS used in apply step is always first introduced correct arity version.

Built-in functions:
'''

from parser import parse_term, parse_rules
from rule import cons, flatten
from builtin import default_named as start_table, UserInterrupt, PrependCondition
import argparse

def run(named_rules, rules, stack, input):
    try:
        while True:
            try:
                rule, args, res_stack = next((rule, *match) for rule, match in
                                             ((rule, rule.match(stack))
                                              for rule in rules) if match)
                try:
                    stack = rule.apply(args, res_stack)
                except PrependCondition as prep:
                    stack = prep.stack
                    input.prepend(prep.prepend)
            except StopIteration:
                try:
                    stack = cons(next(input), stack)
                except KeyboardInterrupt:
                    raise UserInterrupt(*reversed(flatten(stack)))
    except StopIteration:
        return stack

def run_batch(named_rules, rules, stack, input):
    stack = run(named_rules, rules, stack, input)
    return stack

def run_interactive(named_rules, rules, seperator):
    stack = None
    input = PrependableGenerator(input_generator(seperator))
    try:
        run(named_rules, rules, stack, input)
    except UserInterrupt as err:
        print('[' + ', '.join(err.args) + ']')

class PrependableGenerator():
    def __init__(self, base_gen):
        self.base_gen = base_gen
        self.but_first = []

    def prepend(self, seq):
        self.but_first += reversed(seq)

    def __next__(self):
        if self.but_first:
            return self.but_first.pop()
        else:
            return next(base_gen)

    def __iter__(self):
        return self

def input_generator(seperator):
    while True:
        line = input()
        for token in line.split(seperator):
            yield token
        
def token_generator(file, sep):
    if sep:
        for line in file:
            for token in line.split(sep):
                yield token
    else:
        for line in file:
            for char in line:
                yield char
    
parser = argparse.ArgumentParser(description='Run the sessile stream processor')
parser.add_argument('-i', '--interactive', action = 'store_true')
parser.add_argument('source', type = argparse.FileType('r'), nargs = '*')
parser.add_argument('-c', '--seperator', type = str, nargs = 1, default = '')
parser.add_argument('-f', '--infiles', type = argparse.FileType('r'),
                    nargs = '*')
parser.add_argument('-o', '--outfile', type = argparse.FileType('w'),
                    nargs = 1)
args = parser.parse_args()
patterns, rules = start_table, []
for sourcefile in args.source:
    new_patterns, new_rules = parse_rules(sourcefile.read(), patterns)
    patterns.update(new_patterns)
    rules += new_rules
if args.interactive:
    seperator = args.seperator if args.seperator else ' '
    run_interactive(patterns, rules, seperator)
else:
    stack = None
    seperator = args.seperator[0]
    for infile in args.infiles:
        stack = run_batch(patterns, rules, stack,
                          token_generator(infile, seperator))
        infile.close()
    tokens = (token for token in
              reversed(flatten(stack)))
    outfile = args.outfile[0]
    outfile.write(next(tokens))
    for token in tokens:
        outfile.write(seperator)
        outfile.write(token)
    outfile.flush()
    outfile.close()
