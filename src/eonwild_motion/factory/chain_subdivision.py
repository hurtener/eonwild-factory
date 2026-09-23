"""Subdivide a semantic skin chain without moving its existing bind geometry.

This is an engineering rig edit, not anatomical reconstruction. New joints split
the longest links; skin influence is interpolated along the admitted centreline.
The result needs its own source hash, semantic map and admission.
"""
from copy import deepcopy
import hashlib
import struct

import numpy as np
from scipy.spatial.transform import Rotation, Slerp

from ..errors import ContractError
from ..glb.container import Glb
from ..layers.leg_contact_resolve_v3 import _world_matrices
from ..solve.whole_body_gait_transition import _append_accessor, _encode
from .source import _decompose_bind_local, _skin_reconstruction_error


def subdivide_chain(source, names, target_links):
    if source.document.get('animations'):
        raise ContractError('Chain subdivision requires animation-free source geometry')
    if type(target_links) is not int or not len(names)-1 < target_links <= 64:
        raise ContractError('Target links must exceed the source chain, at most 64')
    if len(set(names)) != len(names) or len(names) < 3:
        raise ContractError('Chain needs at least three unique nodes')
    chain = [source.name_to_node[name] for name in names]
    if any(source.parents[b] != a for a, b in zip(chain, chain[1:])):
        raise ContractError('Semantic chain must be directly parented in order')
    if len(source.document['skins']) != 1:
        raise ContractError('Subdivision currently supports one skin')
    original_world = np.asarray(_world_matrices(source, source.rest_translation,
                                                source.rest_rotation, source.rest_scale))
    world = list(original_world.copy())
    doc, binary = deepcopy(source.document), bytearray(source.binary)
    skin = doc['skins'][0]
    original_slots = {skin['joints'].index(n) for n in chain}
    mesh_nodes = [i for i, n in enumerate(source.nodes) if n.get('skin') == 0]
    if len(mesh_nodes) != 1:
        raise ContractError('Subdivision requires a single skinned mesh node')
    mesh_node = mesh_nodes[0]
    before_error, _ = _skin_reconstruction_error(source, skin_index=0, mesh_node=mesh_node)
    if before_error > 3e-6:
        raise ContractError('Source must have canonical bind skin')
    inserted = []
    while len(chain)-1 < target_links:
        lengths = [np.linalg.norm(world[b][:3, 3]-world[a][:3, 3])
                   for a, b in zip(chain, chain[1:])]
        j = int(np.argmax(lengths)); a, b = chain[j:j+2]
        mid = np.eye(4)
        mid[:3, 3] = (world[a][:3, 3]+world[b][:3, 3])/2
        mid[:3, :3] = Slerp([0, 1], Rotation.from_matrix(
            np.array([world[a][:3, :3], world[b][:3, :3]])))(.5).as_matrix()
        name = names[0]+'_subdivision_'+str(len(inserted))
        if name in source.name_to_node:
            raise ContractError('Subdivision joint name already exists')
        new = len(doc['nodes'])
        doc['nodes'].append({'name': name, 'children': [b]})
        doc['nodes'][a]['children'] = [new if n == b else n for n in doc['nodes'][a]['children']]
        world.append(mid)
        for n, parent in ((new, a), (b, new)):
            t, r, s, _ = _decompose_bind_local(np.linalg.solve(world[parent], world[n]), label=name)
            doc['nodes'][n].update(translation=t, rotation=r, scale=s)
            doc['nodes'][n].pop('matrix', None)
        skin['joints'].append(new); chain.insert(j+1, new); inserted.append(name)
    points = np.array([world[n][:3, 3] for n in chain])
    segments = np.diff(points, axis=0)
    lengths = np.linalg.norm(segments, axis=1)
    if np.any(lengths < 1e-5):
        raise ContractError('Degenerate subdivided chain')
    edges = np.r_[0, np.cumsum(lengths)]
    slots = np.array([skin['joints'].index(n) for n in chain])
    processed = set(); changed = 0; influence = np.zeros(len(chain))
    mesh_world = original_world[mesh_node]
    for primitive in doc['meshes'][doc['nodes'][mesh_node]['mesh']]['primitives']:
        attrs = primitive['attributes']
        suffixes = sorted(k[7:] for k in attrs if k.startswith('JOINTS_'))
        key = tuple(attrs['JOINTS_'+s] for s in suffixes)
        if key in processed:
            continue
        processed.add(key)
        js = np.concatenate([np.array(source.accessor_values(attrs['JOINTS_'+s]), dtype=int) for s in suffixes], axis=1)
        ws = np.concatenate([np.array(source.accessor_values(attrs['WEIGHTS_'+s])) for s in suffixes], axis=1)
        vertices = np.array(source.accessor_values(attrs['POSITION']))
        vertices = (mesh_world @ np.c_[vertices, np.ones(len(vertices))].T).T[:, :3]
        for row in np.flatnonzero(np.sum(np.where(np.isin(js, list(original_slots)), ws, 0), axis=1) > 1e-10):
            t = np.clip(np.sum((vertices[row]-points[:-1])*segments, axis=1)/lengths**2, 0, 1)
            distances = np.sum((vertices[row]-points[:-1]-t[:, None]*segments)**2, axis=1)
            j = int(np.argmin(distances)); fraction = float(t[j])
            tail = np.isin(js[row], list(original_slots))
            total = float(ws[row, tail].sum())
            kept = [(int(k), float(w)) for k, w, selected in zip(js[row], ws[row], tail) if not selected and w > 0]
            added = [(int(slots[j]), total*(1-fraction)), (int(slots[j+1]), total*fraction)]
            available = js.shape[1]-len(kept)
            if available < 2:
                raise ContractError('Insufficient influence slots for continuous subdivision')
            pairs = kept+[(k, w) for k, w in added if w > 0]
            js[row] = 0; ws[row] = 0
            for col, (k, w) in enumerate(pairs):
                js[row, col] = k; ws[row, col] = w
            influence[j] += added[0][1]; influence[j+1] += added[1][1]; changed += 1
        for i, s in enumerate(suffixes):
            for kind, data in (('JOINTS_', js[:, i*4:(i+1)*4]), ('WEIGHTS_', ws[:, i*4:(i+1)*4])):
                accessor = attrs[kind+s]
                item, _, width, _, code = source.accessor_layout(accessor)
                if item.get('normalized', False):
                    raise ContractError('Normalized skin accessors are unsupported')
                offset, count, stride = source.accessor_region(accessor)
                for row in range(count):
                    struct.pack_into('<'+code*width, binary, offset+row*stride, *data[row])
    if np.any(influence <= 0):
        raise ContractError('Every subdivided chain joint must influence skin')
    # Keep original bind matrices byte-equivalent; recomputing unrelated joints
    # introduces rounding changes in tightly calibrated jaw/contact witnesses.
    matrices = list(source.accessor_values(source.document['skins'][0]['inverseBindMatrices']))
    matrices.extend(np.linalg.solve(world[n], mesh_world).T.reshape(-1)
                    for n in skin['joints'][len(matrices):])
    matrices = np.asarray(matrices)
    skin['inverseBindMatrices'] = _append_accessor(doc, binary, matrices, 'MAT4')
    doc['buffers'][0]['byteLength'] = len(binary)
    raw = _encode(doc, binary)
    reopened = Glb.from_bytes(raw)
    after_error, vertices = _skin_reconstruction_error(reopened, skin_index=0, mesh_node=mesh_node)
    check_world = np.asarray(_world_matrices(reopened, reopened.rest_translation, reopened.rest_rotation, reopened.rest_scale))
    world_error = float(np.max(np.abs(check_world[:len(source.nodes)]-original_world)))
    if max(after_error, world_error) > 3e-6:
        raise ContractError('Subdivision changed bind skin or existing joint positions')
    return raw, {'schema': 'eonwild.motion.chain-subdivision.v1',
        'source_sha256': hashlib.sha256(source.raw).hexdigest(),
        'output_sha256': hashlib.sha256(raw).hexdigest(),
        'chain': [doc['nodes'][n]['name'] for n in chain], 'inserted': inserted,
        'links': len(chain)-1, 'nodes': len(chain), 'length_m': float(edges[-1]),
        'skin_vertices': vertices, 'reweighted_vertices': changed,
        'joint_weight_totals': influence.tolist(), 'bind_skin_error_m': after_error,
        'existing_joint_world_error': world_error,
        'classification': 'Engineering subdivision and interpolated skin weights; no anatomical claim'}
