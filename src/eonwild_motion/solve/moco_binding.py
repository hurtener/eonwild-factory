"""Validate physical axial links against the actual admitted skin topology."""


def validate_axial_bindings(metadata, roles, parents):
    bindings = metadata['axial_bindings']
    bodies = [b['body'] for b in bindings]
    nodes = [roles[b['role']] for b in bindings]
    if len(set(bodies)) != len(bodies) or len(set(nodes)) != len(nodes):
        raise ValueError('Each physical axial body requires a unique skin bone')
    chain = metadata.get('tail_chain', [])
    if not chain:
        return  # Older coarse axial models retain their existing adapter.
    tail_roles = sorted((r for r in roles if r.startswith('tail.')),
                        key=lambda r: int(r.split('.')[-1]))
    if len(chain) != len(tail_roles)-1:
        raise ValueError('Physical tail link count differs from admitted skin chain')
    by_body = {b['body']: b['role'] for b in bindings}
    for part, start, end in zip(chain, tail_roles, tail_roles[1:]):
        if (part['role'], part['end_role']) != (start, end):
            raise ValueError('Physical tail is not in semantic chain order')
        if by_body.get(part['body']) != start or parents[roles[end]] != roles[start]:
            raise ValueError('Physical tail binding differs from connected skin topology')
