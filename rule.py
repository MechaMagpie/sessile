import re
from overrides import overrides

def cons(item, tail):
    return (item, tail)

def car(list):
    try:
        head, _ = list
        return head
    except:
        raise Exception('Null list')

def cdr(list):
    _, tail = list
    return tail

def flatten(list):
    def linked_generator(list):
        while list:
            head, list = list
            yield head
    return tuple(linked_generator(list))

def unflatten(flat_list):
    def inner_unflatten(gen):
        try:
            elem = next(gen)
            return (elem, inner_unflatten(gen))
        except StopIteration:
            return None
    return inner_unflatten(elem for elem in flat_list)

def take(n, list):
    try:
        head = []
        for _ in range(n, 0, -1):
            (elem, list) = list
            head.append(elem)
        return (tuple(reversed(head)), list)
    except:
        raise Exception('List too short')

class Var(object):
    hash_prefix = ''
    
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value

    def __repr__(self):
        return f"{type(self).__name__}({self.value})"

    def __eq__(self, other):
        return type(self) == type(other) and self.value == other.value

    def __hash__(self):
        hash(type(self).hash_prefix + self.value)

class Unbound(Var):
    hash_prefix = '_'

class Bound(Var):
    hash_prefix = '#'
    
class Rule(object):
    @staticmethod
    def _unbound(ls):
        return [name for name in ls if isinstance(name, Unbound)]
    @staticmethod
    def _bound(ls):
        return [name for name in ls if isinstance(name, Bound)]
    
    def __init__(self, lhs, rhs, label = None):
        self.label = label
        self.lhs = lhs
        self.rhs = rhs
        def var_names(ls):
            from collections import OrderedDict
            return OrderedDict.fromkeys([name for _, *names in ls
                                         for name in names]).keys()
        self.lhs_names = var_names(lhs)
        self.rhs_names = [name for name in var_names(rhs)
                          if name in self.lhs_names]
        self.lhs_param = _unbound(self.lhs_names)
        self.rhs_param = _unbound(self.rhs_names)
        assert(set(self.lhs_param) >= set(self.rhs_param))
        self.arity = len(self.rhs_param)
        self.choices = [self]
        
    def __str__(self):
        def sidestr(side):
            return ' '.join([t._str(args) for t, *args in side])
        rule = sidestr(self.lhs) + ' -> ' + sidestr(self.rhs)
        if self.label:
            return self.label + ': ' + rule
        else:
            return rule

    def _str(self, args):
        if self.arity:
            return f"{self.label}({', '.join([str(arg) for arg in args])})"
        else:
            return self.label

    def right_arity(self, num_args):
        return num_args == self.arity
        
    def match(self, stack):
        '''
        If matched, returns tuple of result and remaining stack
        If not matched, returns None
        '''
        def inner_match(lhs, stack, bindings):
            pattern, *vars = lhs[-1]
            for choice in pattern.choices:
                match = choice.match(stack)
                if not match:
                    continue
                result, new_stack = match
                if len(vars) > 1:
                    res_bindings = dict(zip(vars, result))
                elif len(vars) == 1:
                    res_bindings = {vars[0]: result[0]}
                else:
                    res_bindings = {}
                if not all(bindings[n] == res_bindings[n]
                           for n in res_bindings if n in bindings):
                    continue
                if len(lhs[:-1]):
                    next = inner_match(lhs[:-1], new_stack,
                                       {**bindings, **res_bindings})
                    if next:
                        return next
                else:
                    return ({**bindings, **res_bindings}, new_stack)
            return None
        init_bindings = {name: name.value for name in _bound(self.rhs_names)}
        mat = inner_match(self.lhs, stack, init_bindings)
        if mat:
            binding, new_stack = mat
            return [binding[name] for name in self.rhs_param]
        else:
            return None

    def apply(self, values, stack):
        '''
        Given variable bindings, returns stack after unpacking RHS
        '''
        binding = dict((*zip(self.rhs_param, values),
                        *((x, x.value) for x in _bound(self.rhs_names))))
        for rule, *names in self.rhs:
            def arglist(item):
                return isinstance(item, (tuple, list))
            if len(names) == 1 and arglist(binding[names[0]]):
                stack = rule.apply(binding[names[0]], stack)
            else:
                vars = [binding[name] for name in names]
                stack = rule.apply(vars, stack)
        return stack

class PlaceHolderRule(Rule):
    def __init__(self, label):
        self.name = label
        self.arity = -1
        self.choices = []

    @overrides
    def right_arity(self, num_args):
        return True

class LiteralString(Rule):
    def __init__(self, text):
        self.text = text
        self.choices = [self]
        self.arity = 0

    def __str__(self):
        return '"' + self.text + '"'

    @overrides
    def _str(self, args):
        return str(self)

    @overrides
    def match(self, stack):
        if stack and car(stack) == self.text:
            return ([], cdr(stack))
        else:
            return None

    @overrides
    def apply(self, _, stack):
        return cons(self.text, stack)

class FreeVar(Rule):
    def __init__(self):
        self.arity = 1
        self.choices = [self]

    @overrides
    def match(self, stack):
        if stack:
            return ([car(stack)], cdr(stack))
        else:
            return None
        
    @overrides
    def apply(self, values, stack):
        try:
            [value] = values
            return cons(value, stack)
        except:
            for value in values:
                stack = cons(value, stack)
            return stack

    @overrides
    def _str(self, vars):
        return vars[0]
