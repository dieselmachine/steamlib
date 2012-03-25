from cStringIO import StringIO

def get_next(s):
    c = None
    while c not in ['"','{','}']:
        c = s.read(1)
    if c == '"':
        " string "
        data = ''
        while True:
            c = s.read(1)
            if c == '"':
                break
            data += c
    elif c == '{':
        " dict "
        data = {}
        while True:
            key = get_next(s)
            if key:
                value = get_next(s)
                data[key] = value
            else:
                return data
            next = s.read(1)
            if next == '}':
                break
            s.seek(-1,1)
    elif c == '}':
        return None
    return data
    
def parse_vdf(data):
    data = StringIO('{%s}' % data)
    return get_next(data)
