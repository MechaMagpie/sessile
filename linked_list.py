def cons(item, tail):
    return (item, tail)

def car(list):
    try:
        head, _ = list
        return head
    except:
        raise Exception('Null list')

def cdr(list):
    try:
        _, tail = list
        return tail
    except:
        raise Exception('Null list')

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
