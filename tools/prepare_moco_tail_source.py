#!/usr/bin/env python3
"""Create a connected, weighted source tail and hash-bound admission catalogs.

Run from the factory root. Existing source/catalogs are never overwritten.
This only prepares geometry; it does not approve or generate animal motion.
"""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
from eonwild_motion.glb.container import Glb
from eonwild_motion.factory.chain_subdivision import subdivide_chain


def main():
    ap=argparse.ArgumentParser()
    for name in ('motion-set','profile','output'):
        ap.add_argument('--'+name,type=Path,required=True)
    ap.add_argument('--target-links',type=int,required=True)
    ap.add_argument('--catalog-suffix',required=True)
    a=ap.parse_args()
    if not a.catalog_suffix.replace('-','').isalnum():raise ValueError('Use an alphanumeric catalog suffix')
    read=lambda p: json.loads(Path(p).read_text())
    motion=read(a.motion_set); baseline=read(motion['baseline']['path'])
    rig=read(baseline['rig']['path']); animal=read(baseline['animal']['path'])
    raw,receipt=subdivide_chain(Glb(Path(baseline['source']['path'])),rig['roles']['tail'],a.target_links)
    old_hash=baseline['source']['sha256'];new_hash=receipt['output_sha256']
    source_path=Path('assets/sha256')/(new_hash+'.glb')
    planned={source_path:raw}
    def write_variant(path,data):
        old=Path(path);new=old.with_name(old.stem+'.'+a.catalog_suffix+'.json')
        if 'id' in data:data['id']+='.'+a.catalog_suffix
        encoded=(json.dumps(data,indent=2)+'\n').encode();planned[new]=encoded
        return dict(path=str(new),sha256=hashlib.sha256(encoded).hexdigest())
    def replace_hashes(data):
        if isinstance(data,dict):return {k:replace_hashes(v) for k,v in data.items()}
        if isinstance(data,list):return [replace_hashes(v) for v in data]
        return new_hash if data==old_hash else data
    rig['roles']['tail']=receipt['chain']
    rig['provenance']=dict(parent=baseline['rig'],source_subdivision=receipt,
        classification='Engineering rig subdivision, not anatomical reconstruction')
    baseline['rig']=write_variant(baseline['rig']['path'],rig)
    animal=replace_hashes(animal)
    animal['limitations'].append('Tail source subdivided with bind shape and all existing joint positions preserved; original measurements retained.')
    baseline['animal']=write_variant(baseline['animal']['path'],animal)
    for parent,key in [(baseline,'neutral_pose_profile'),(baseline['locomotion_response_policy']['regimes']['grounded'],'neutral_support_profile')]:
        original=parent[key];data=replace_hashes(read(original['path']))
        parent[key]=write_variant(original['path'],data)
    contact=replace_hashes(read(baseline['contact_profile']['path']))
    contact['source']['path']=str(source_path)
    baseline['contact_profile']=write_variant(baseline['contact_profile']['path'],contact)
    baseline['source']=dict(path=str(source_path),sha256=new_hash)
    motion['baseline']=write_variant(motion['baseline']['path'],baseline)
    motion_lock=write_variant(a.motion_set,motion)
    profile=read(a.profile)
    profile['bindings']=[b for b in profile['bindings'] if not b['role'].startswith('tail.')]
    profile['bindings'] += [dict(role='tail.'+str(i),bone=b) for i,b in enumerate(receipt['chain'])]
    profile['authoring']['animalInstance']=animal
    profile['source']={'sourceGeometrySha256':new_hash,'status':'EXPERIMENTAL_SOURCE_ADMISSION',
        'parentProfileSha256':hashlib.sha256(a.profile.read_bytes()).hexdigest()}
    planned[a.output/'source.profile.json']=(json.dumps(profile,indent=2)+'\n').encode()
    receipt['motion_set']=motion_lock
    planned[a.output/'source-subdivision.json']=(json.dumps(receipt,indent=2)+'\n').encode()
    for p,content in planned.items():
        if p.exists() and p.read_bytes()!=content:raise FileExistsError(p)
    for p,content in planned.items():
        p.parent.mkdir(parents=True,exist_ok=True)
        if not p.exists():p.write_bytes(content)
    print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
