from rule import Bound, Unbound, Rule, PlaceHolderRule, LiteralString, FreeVar

import re

def parse_term(text, fun_ref):
    [string, pattern, fun, freevar] = \
            [re.fullmatch(ex, text) for ex in
            [r'"(.*)"',
             r'([a-z][a-z0-9]*)',
             r'([a-z][a-z0-9]*)\(((?:(?:[A-Z]+)|(?:\".*\"))' +
             r'(?:\,\s+(?:(?:[A-Z]+)|(?:\".*\")))*)\)',
             # Terribly sorry about the mess
             r'([A-Z]+)'
         ]]
    if string:
        return (LiteralString(string.group(1)),)
    elif freevar:
        return (FreeVar(), *freevar.group(1))
    elif pattern:
        name = pattern.group(1)
        correct_pattern = next(fun for fun in fun_ref[name]
                               if fun.right_arity(0))
        return (correct_pattern,)
    elif fun:
        name = fun.group(1)
        vars = []
        for raw_var in re.split(r'\,\s', fun.group(2)):
            try:
                var = Bound(re.fullmatch(r'\"(.*)\"', raw_var).group(1))
            except:
                var = Unbound(raw_var)
            vars.append(var)
        if len(vars and isinstance(vars[0], Unbound)) == 1:
            return (fun_ref[name][0], *vars)
        else:
            correct_fun = next(fun for fun in fun_ref[name]
                               if fun.right_arity(len(vars)))
        return (correct_fun, *vars)
    else:
        raise(Exception('illegible'))

def parse_rules(input, named_rules = {}):
    lines = [re.split(r'(?<!\,)\s+', l) for l in input.split('\n')]
    rules = []
    for line in lines:
        try:
            arrow = line.index('->')
        except:
            break
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
            other_rules = [other_rule for other_rule in named_rules[label]
                           if new_rule.right_arity(other_rule.arity)]
            if other_rules:
                for other_rule in other_rules:
                    other_rule.choices.append(new_rule)
                    new_rule.choices.append(other_rule)
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
    return (named_rules, rules)
