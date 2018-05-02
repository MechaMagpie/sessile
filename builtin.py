'''
Built in functions:
int: LHS X matches if X is integer
float: LHS X matches if X is float
in: LHS X Y matches if X in Y
cat: RHS X Y concatenates X Y
arith: LHS X matches if X is space-seperated RPN arithemetic expression, RHS X evaluates expression
arithf: same as above but floating point math
print: RHS X prints X to output
clist: LHS A matches C-seperated list and string C as list with C appended, RHS A pushes concatenation of all but last element seperated with last element of A
nlist: LHS A matches W terms as A and a tag of form '[W' where W is an integer, RHS A pushes every A and '[W' where W is the length of A
cfnlst: LHS A matches W terms, a tag '[W' and a char C, A being all terms plus C
re: LHS A matches a string and a regex that describes it, with all groups as A
stop: RHS terminates the program
prepend: RHS A prepends A to current input
get: LHS A matches term W and if W is a key, returns value A
set: RHS K V sets V at key K
del: RHS K removes value at K
'''
from rule import Rule, cons, car, cdr
from overrides import overrides
import types, re

class BuiltInRule(Rule):    
    def __init__(self, name, arity = 0, match = None, apply = None):
        self.name = name
        if callable(arity):
            self.right_arity = types.MethodType(arity, self)
            self.arity = -1
        else:
            self.arity = arity
        if match:
            self.match = types.MethodType(match, self)
        if apply:
            self.apply = types.MethodType(apply, self)
        
    def _str(self, args):
        if self.arity:
            return f"{self.name}({', '.join(args)})"
        else:
            return self.name

    def match(self, stack):
        raise(Exception(f"no LHS supplied for {self.name}!"))

    def apply(self, values, stack):
        raise(Exception(f"no RHS supplied for {self.name}!"))

class UserInterrupt(Exception):
    pass
    
class PrependCondition(Exception):
    def __init__(self, stack, prepend):
        self.stack = stack
        self.prepend = prepend
    
def is_int(val):
    try:
        int(val)
        return True
    except:
        return False

def is_float(val):
    try:
        float(val)
        return True
    except:
        return False

def any_arity(self, _):
    return True
    
def is_int_match(self, stack):
    if is_int(car(stack)):
        return ([car(stack)], cdr(stack))
    else:
        return None
is_int = BuiltInRule(name = 'int', arity = 1, match = is_int_match)

def is_float_match(self, stack):
    if is_float(car(stack)):
        return ([car(stack)], cdr(stack))
    else:
        return None
is_float = BuiltInRule(name = 'float', arity = 1, match = is_float_match)

def in_test_match(self, stack):
    try:
        ((second, first), rem) = take(2, stack)
        assert(first in second)
        return ([first, second], rem)
    except:
        return None
in_test = BuiltInRule(name = 'in', arity = 2, match = in_test_match)

def concatenate(self, values, stack):
    return cons(''.join(values), stack)
cat = BuiltInRule(name = 'cat', arity = any_arity, apply = concatenate)

def arith_processor(f = False):
    import operator
    def eval_arith(self, values, stack):
        try:
            [expr] = values
            ops = expr.split(' ')
        except:
            ops = values
        temp_stack = []
        for op in ops:
            try:
                if f:
                    temp_stack.append(float(op))
                else:
                    temp_stack.append(int(op))
            except:
                b, a = (int(temp_stack.pop()), int(temp_stack.pop()))
                fun = {'+': operator.add, '-': operator.sub, '*': operator.mul,
                       '/': operator.div, '%': operator.mod, '^': operator.pow}
                temp_stack.append(fun[op](a, b))
        return str(temp_stack.pop())

def arith_tester(f = False):
    def test_arith(self, stack):
        try:
            expr = car(stack)
            elems = expr.split(' ')
            count = 0
            for elem in elems:
                if f and is_float(elem) or is_int(elem):
                    count += 1
                elif elem in ['+', '-', '*', '/', '%' '^']:
                    count -= 1
                else:
                    raise Exception('wut')
                assert(count >= 1)
            assert(count == 1)
            return ([expr], cdr(stack))
        except:
            return None
arithmetic = BuiltInRule(name = 'arith', arity = 1, match = arith_tester(),
                         apply = arith_processor())
float_arithmetic = BuiltInRule(name = 'arithf', arity = 1,
                               match = arith_tester(f = True),
                               apply = arith_processor(f = True))

def output_top(self, values, stack):
    print(', '.join(values))
    return stack
output = BuiltInRule(name = 'print', arity = 1, apply = output_top)

def csv_split(self, stack):
    try:
        char = car(stack)
        vals = car(cdr(stack)).split(char)
        assert(len(vals) > 1)
        return ([*vals, char], cdr(stack))
    except:
        return None
def csv_join(self, values, stack):
    (*vals, char) = values
    return cons(char.join(vals), stack)
csv_list = BuiltInRule(name = 'clist', arity = 2,
                       match = csv_split, apply = csv_join)

def decode_tag(tag):
    return int(re.fullmatch(r'\[([0-9]+)', tag).group(0))
def cfl_join(self, stack):
    try:
        ((char, tag), rest_stack) = take(2, stack)
        n = decode_tag(tag)
        (vals, rest_stack) = take(n, rest_stack)
        return ((*vals, char), rest_stack)
    except:
        return None
csv_from_nlist = BuiltInRule(name = 'cfnlst', arity = any_arity,
                             match = cfl_join)
def nls_join(self, stack):
    try:
        tag = car(stack)
        n = decode_tag(tag)
        (vals, rest_stack) = take(n, cdr(stack))
        return (vals, rest_stack)
    except:
        return None
def nls_dump(self, values, stack):
    tag = '[' + str(len(values))
    for val in values:
        stack = cons(val, stack)
    stack = cons(tag, stack)
    return stack
num_list = BuiltInRule('nlist', arity = 2,
                       match = nls_join, apply = nls_dump)

def regex_group(self, stack):
        try:
            ((regex, target), rest) = take(2, stack)
            match = re.fullmatch(regex, target)
            assert(match)
            return (match.groups, rest)
        except:
            return None
regex_bypass = BuiltInRule(name = 're', arity = any_arity, match = regex_group)

def stop_and_print(self, _, stack):
    raise UserInterrupt(*reveresed(flatten(stack)))
user_stop = BuiltInRule(name = 'stop', apply = stop_and_print)

def prepend_ls(self, list, stack):
    raise PrependCondition(stack, list)
prepend = BuiltInRule(name = 'prepend', arity = any_arity, apply = prepend_ls)

global_state = {}
def reset_state():
    global_state = {}
def global_lookup(self, stack):
    try:
        return ([global_state[car(stack)]], cdr(stack))
    except:
        return None
global_get = BuiltInRule(name = 'get', arity = 1, match = global_lookup)
def global_assign(self, pair, stack):
    key, value = pair
    global_state[key] = value
global_set = BuiltInRule(name = 'set', arity = 2, apply = global_assign)
def global_retract(self, key, stack):
    [key] = key
    del global_state[key]
global_del = BuiltInRule(name = 'del', arity = 1, apply = global_retract)
funs = [is_int, is_float, in_test, cat, arithmetic, float_arithmetic, output,
        csv_list, csv_from_nlist, num_list, regex_bypass, user_stop, prepend,
        global_get, global_set, global_del]
default_named = dict((fun.name, [fun]) for fun in funs)
