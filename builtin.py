'''
Built in functions:
int
float
cat
succ 
pred
arith
arithf
print
clist
nlist

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

def concatenate(self, values, stack):
    return cons(''.join(values), stack)
cat = BuiltInRule(name = 'cat', arity = any_arity, apply = concatenate)

def increment_int(by):
    def increment_inner(self, values, stack):
        newval = str(int(car(stack)) + by)
        return cons(newval, cdr(stack))
increment = BuiltInRule(name = 'succ', arity = 1, apply = increment_int(1))
decrement = BuiltInRule(name = 'pred', arity = 1, apply = increment_int(-1))

def arith_processor(f = False):
    import operator
    def eval_arith(self, values, stack):
        [expr] = values
        ops = expr.split(' ')
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
csv_list = BuiltInRule('clist', arity = any_arity,
                       match = csv_split, apply = csv_join)

def nls_join(self, stack):
    try:
        tag = car(stack)
        n = int(re.fullmatch(r'\[([0-9]+)', tag).group(0))
        (vals, rest_stack) = take(n, cdr(stack))
        return ([*vals, tag], rest_stack)
    except:
        return None
def nls_dump(self, values, stack):
    (*vals, tag) = values
    for val in vals:
        stack = cons(val, stack)
    stack = cons(tag, stack)
    return stack
num_list = BuiltInRule('nlist', arity = any_arity,
                       match = nls_join, apply = nls_dump)

funs = [is_int, is_float, cat, increment, decrement, arithmetic, float_arithmetic,
        output, csv_list, num_list]
default_named = dict((fun.name, [fun]) for fun in funs)
