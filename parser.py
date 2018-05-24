from rule import Bound, Unbound, Rule, PlaceHolderRule, LiteralString, FreeVar, CapturingChoice

import re

def parse_term(text, fun_ref):
    [string, pattern, fun, freevar, nullvar] = \
            [re.fullmatch(ex, text) for ex in
            [r'"(.*)"',
             r'([a-z][a-z0-9]*)',
             r'([a-z][a-z0-9]*)\(((?:(?:[A-Z]+)|(?:\".*\")|_)' +
             r'(?:\,\s*(?:(?:[A-Z]+)|(?:\".*\")|_))*)\)',
             # Terribly sorry about the mess
             r'([A-Z]+)',
             r'(_)'
         ]]
    if string:
        return (LiteralString(string.group(1)),)
    elif freevar:
        return (FreeVar(), Unbound(freevar.group(1)[0]))
    elif nullvar:
        return (Anything(),)
    elif pattern:
        name = pattern.group(1)
        correct_pattern = next(fun for fun in fun_ref[name]
                               if fun.right_arity(0))
        return (correct_pattern,)
    elif fun:
        name = fun.group(1)
        vars = []
        for raw_var in re.split(r'\,\s', fun.group(2)):
            [bound, unbound, blank] = \
                    [re.fullmatch(ex, raw_var) for ex in
                    [r'"(.*)"',
                     r'([A-Z]+)',
                     r'(_)'
                 ]]
            if bound:
                var = Bound(bound.group(1))
            elif unbound:
                var = Unbound(unbound.group(1))
            elif blank:
                var = Blank()
            vars.append(var)
        if len(vars) == 1 and isinstance(vars[0], Unbound):
            return (fun_ref[name][0], *vars)
        else:
            correct_fun = next(fun for fun in fun_ref[name]
                               if fun.right_arity(len(vars)))
        return (correct_fun, *vars)
    else:
        raise(Exception('illegible'))

def link_rules(label, new_rule, named_rules):
    if label in named_rules:
        other_rules = [other_rule for other_rule in named_rules[label]
                       if new_rule.right_arity(other_rule.arity)]
        if other_rules:
            for other_rule in other_rules:
                other_rule.choices.append(new_rule)
                new_rule.choices.append(other_rule)
    
def parse_rule(line, rules, named_rules):
    arrow = line.index('->')
    lhs, rhs = (line[:arrow], line[arrow+1:])
    label = re.fullmatch(r'([a-z][a-z0-9]*):', lhs[0])
    if label:
        lhs = lhs[1:]
        label = label.group(1)
        if label not in named_rules:
            named_rules[label] = [PlaceHolderRule(label)]
        else:
            named_rules[label].append(PlaceHolderRule(label))
    lhs = [parse_term(term, named_rules) for term in lhs]
    rhs = [parse_term(term, named_rules) for term in rhs]
    if label:
        new_rule = Rule(lhs, rhs, label)
        link_rules(label, new_rule, named_rules)
        def subst(ls):
            new_ls = [(rule, *args) if not isinstance(rule, PlaceHolderRule)
                      else (new_rule, *args) for (rule, *args) in ls]
            assert not any(rule.arity != len(args)
                           and not (rule.arity >= 1 and len(args) == 1
                                    and isinstance(args[0], Unbound))
                           for (rule, *args) in new_ls)
            return new_ls
        new_rule.lhs = subst(new_rule.lhs)
        new_rule.rhs = subst(new_rule.rhs)
        named_rules[label].append(new_rule)
        named_rules[label] = [rule for rule in named_rules[label]
                              if not isinstance(rule, PlaceHolderRule)]
    else:
        rules.append(Rule(lhs, rhs))

def parse_capture(line, named_rules):
    label = re.sub(r'(.*):', r'\1', line[0])
    alts = [re.sub(r'"(.*)"', r'\1', literal)
            for literal in line[1:] if literal != '|']
    new_rule = CapturingChoice(label, *alts)
    link_rules(label, new_rule, named_rules)
    if label in named_rules:
        named_rules[label].append(new_rule)
    else:
        named_rules[label] = [new_rule]

def split_rule(l):
    # Ok, so this is basically a miniature RDP, derp.
    ln = (c for c in l)
    ch = next(ln)
    def adv():
        nonlocal ch
        old_ch = ch
        ch = next(ln)
        return old_ch
    def eat_space():
        while ch in ' \t':
            adv()
    def parse_string():
        adv()
        def parse_escape():
            return {'\\': '\\', '"': '"', 'a': '\a', 'b': '\b', 'f': '\f',
                    'n': '\n', 'r': '\r', 't': '\t', 'v' : '\v'}[adv()]
        res = ''
        while not ch == '"':
            if ch == '\\':
                res += parse_escape()
            else:
                res += adv()
        return f'"{res}"'
    def parse_term():
        res = ''
        while ch not in ' \t(':
            res += adv()
        if ch == '(':
            res += adv()
            while not ch == ')':
                res += adv()
            res += ch
        return res
    def parse_op():
        res = ch
        if ch == '-':
            adv()
            res += ch
        return res
    rules = []
    while True:
        try:
            eat_space()
            if ch in '-|_':
                rules.append(parse_op())
            elif ch == '"':
                rules.append(parse_string())
            else:
                rules.append(parse_term())
            adv()
        except:
            break
    return rules

def parse_rules(input, named_rules = {}):
    lines = [[*split_rule(l)] for l in input.split('\n')]
    rules = []
    for line in lines:
        if '->' in line:
            parse_rule(line, rules, named_rules)
        elif '|' in line:
            parse_capture(line, named_rules)
        elif not line or re.fullmatch('#.*', line[0]):
            continue
        else:
            raise Exception('Parser choked!')
    return (named_rules, rules)
