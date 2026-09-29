#!/usr/bin/env python3
"""How alive is a clip? Per semantic body part, the peak-to-peak motion over a time window,
measured in the body's own heading frame (so travel and turning don't count):

  pitch / yaw / roll ranges of each segment's world orientation (degrees),
  vertical bob of pelvis, chest and head (cm), lateral sway of the tail tip (cm).

usage: measure_liveliness.py <clip.glb> <profile.json> [--window START END] [--label NAME] ...
Several clip/profile pairs can be given as clip.glb:profile.json; a table compares them.
"""
import argparse, json, struct
from pathlib import Path
import numpy as np

COMPONENTS = {5126: (np.float32, 4)}
WIDTH = {'SCALAR': 1, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def load_glb(path):
    raw = Path(path).read_bytes()
    n = struct.unpack('<I', raw[12:16])[0]
    doc = json.loads(raw[20:20 + n])
    rest = raw[20 + n:]
    blob = rest[8:8 + struct.unpack('<I', rest[:4])[0]] if rest else b''
    return doc, blob


def accessor(doc, blob, i):
    a = doc['accessors'][i]; v = doc['bufferViews'][a['bufferView']]
    w = WIDTH[a['type']]; start = v.get('byteOffset', 0) + a.get('byteOffset', 0)
    stride = v.get('byteStride', 4 * w)
    out = np.empty((a['count'], w), np.float64)
    for k in range(a['count']):
        out[k] = np.frombuffer(blob, np.float32, w, start + k * stride)
    return out


def qmat(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def sample(times, values, interp, t, rotation):
    if interp == 'CUBICSPLINE':
        values = values.reshape(len(times), 3, -1)[:, 1]
    if t <= times[0]: return values[0]
    if t >= times[-1]: return values[-1]
    j = np.searchsorted(times, t) - 1; u = (t - times[j]) / (times[j + 1] - times[j])
    a, b = values[j], values[j + 1]
    if rotation:
        if a @ b < 0: b = -b
        q = (1 - u) * a + u * b; return q / np.linalg.norm(q)
    return (1 - u) * a + u * b


class Clip:
    def __init__(self, path):
        self.doc, blob = load_glb(path); nodes = self.doc['nodes']
        self.names = [n.get('name', str(i)) for i, n in enumerate(nodes)]
        self.parent = {c: i for i, n in enumerate(nodes) for c in n.get('children', [])}
        self.rest = [(np.array(n.get('translation', [0, 0, 0]), float), np.array(n.get('rotation', [0, 0, 0, 1]), float),
                      np.array(n.get('scale', [1, 1, 1]), float)) for n in nodes]
        anim = self.doc['animations'][0]; self.channels = {}
        for ch in anim['channels']:
            s = anim['samplers'][ch['sampler']]
            self.channels[(ch['target']['node'], ch['target']['path'])] = (
                accessor(self.doc, blob, s['input'])[:, 0], accessor(self.doc, blob, s['output']), s.get('interpolation', 'LINEAR'))
        self.duration = max(v[0][-1] for v in self.channels.values())

    def world(self, t):
        local = []
        for i, (tr, rot, sc) in enumerate(self.rest):
            if (i, 'translation') in self.channels: tr = sample(*self.channels[(i, 'translation')], t, False)
            if (i, 'rotation') in self.channels: rot = sample(*self.channels[(i, 'rotation')], t, True)
            if (i, 'scale') in self.channels: sc = sample(*self.channels[(i, 'scale')], t, False)
            m = np.eye(4); m[:3, :3] = qmat(rot) * sc; m[:3, 3] = tr; local.append(m)
        out = [None] * len(local)
        def get(i):
            if out[i] is None: out[i] = local[i] if i not in self.parent else get(self.parent[i]) @ local[i]
            return out[i]
        return [get(i) for i in range(len(local))]


def heading_frame(pelvis, head):
    f = head - pelvis; f[1] = 0; f /= np.linalg.norm(f); up = np.array([0, 1., 0])
    return np.stack([np.cross(up, f), up, f])  # rows: right, up, forward


def angles(direction, frame):
    """Pitch (up positive) and yaw (right positive) of a segment direction in the heading frame."""
    d = frame @ direction; d /= np.linalg.norm(d)
    return np.degrees(np.arcsin(np.clip(d[1], -1, 1))), np.degrees(np.arctan2(d[0], d[2]))


def measure(glb, profile, window=None, hz=30):
    clip = Clip(glb); prof = json.loads(Path(profile).read_text())
    idx = {b['role']: clip.names.index(b['bone']) for b in prof['bindings'] if b['bone'] in clip.names}
    t0, t1 = window or (0, clip.duration)
    rows = []
    for t in np.arange(t0, t1, 1 / hz):
        W = clip.world(t); P = lambda r: W[idx[r]][:3, 3]
        frame = heading_frame(P('pelvis'), P('head'))
        seg = lambda a, b: P(b) - P(a)
        tails = sorted(r for r in idx if r.startswith('tail.'))
        necks = sorted(r for r in idx if r.startswith('neck.'))
        row = {}
        row['pelvis→chest'] = angles(seg('pelvis', 'chest'), frame)
        row['neck'] = angles(seg(necks[0], necks[-1]), frame)
        row['head'] = angles(seg(necks[-1], 'head'), frame)
        row['tail base'] = angles(seg('pelvis', tails[2]), frame)
        row['tail mid'] = angles(seg(tails[2], tails[5]), frame)
        row['tail tip'] = angles(seg(tails[5], tails[-1]), frame)
        up = lambda r: P(r)[1]
        tip_side = (frame @ (P(tails[-1]) - P('pelvis')))[0]
        head_side = (frame @ (P('head') - P('pelvis')))[0]
        row['_heights'] = (up('pelvis'), up('chest'), up('head'), tip_side, head_side)
        def knee(side):
            h, k, a = P(side + 'Leg.0'), P(side + 'Leg.1'), P(side + 'Leg.2')
            u, v = h - k, a - k; return np.degrees(np.arccos(np.clip(u @ v / np.linalg.norm(u) / np.linalg.norm(v), -1, 1)))
        row['_legs'] = (knee('left'), up('leftLeg.3'), (frame @ (P('leftLeg.3') - P('pelvis')))[2])
        if 'jaw_lower' in idx:
            j = W[idx['jaw_lower']][:3, :3]; h = W[idx['head']][:3, :3]
            rel = h.T @ j; row['_jaw'] = np.degrees(np.arccos(np.clip((np.trace(rel) - 1) / 2, -1, 1)))
        rows.append(row)
    result = {}
    for key in rows[0]:
        if key.startswith('_'): continue
        a = np.array([r[key] for r in rows])
        result[key] = dict(pitch=float(np.ptp(a[:, 0])), yaw=float(np.ptp(np.unwrap(np.radians(a[:, 1])) * 180 / np.pi)))
    h = np.array([r['_heights'] for r in rows])
    result['bob_cm'] = dict(pelvis=float(np.ptp(h[:, 0]) * 100), chest=float(np.ptp(h[:, 1]) * 100), head=float(np.ptp(h[:, 2]) * 100))
    result['sway_cm'] = dict(tail_tip=float(np.ptp(h[:, 3]) * 100), head=float(np.ptp(h[:, 4]) * 100))
    L = np.array([r['_legs'] for r in rows])
    result['left leg'] = dict(knee_range_deg=float(np.ptp(L[:, 0])), knee_min_deg=float(L[:, 0].min()),
                              foot_lift_cm=float(np.ptp(L[:, 1]) * 100), foot_reach_cm=float(np.ptp(L[:, 2]) * 100))
    if '_jaw' in rows[0]: result['jaw_deg'] = float(np.ptp([r['_jaw'] for r in rows]))
    return result


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('clips', nargs='+', help='clip.glb:profile.json[@start-end]')
    a = ap.parse_args(); results = {}
    for spec in a.clips:
        body, _, win = spec.partition('@'); glb, profile = body.split(':')
        window = tuple(float(x) for x in win.split('-')) if win else None
        results[Path(glb).parent.name + '/' + Path(glb).stem + (f'@{win}' if win else '')] = measure(glb, profile, window)
    names = list(results)
    print(f"{'':22s}" + ''.join(f'{n[-26:]:>28s}' for n in names))
    for key in results[names[0]]:
        vals = results[names[0]][key]
        if isinstance(vals, dict):
            for sub in vals:
                print(f'{key + " " + sub:22s}' + ''.join(f'{results[n][key][sub]:28.1f}' for n in names))
        else:
            print(f'{key:22s}' + ''.join(f'{results[n].get(key, float("nan")):28.1f}' for n in names))


if __name__ == '__main__':
    main()
