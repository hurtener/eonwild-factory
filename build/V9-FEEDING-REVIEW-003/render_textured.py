"""Opt-in original-base-color preview; frozen motion and clay remain untouched.

Workbench texture preview uses the asset's real embedded base color/UVs with
the same studio lighting. It does not claim full PBR normal/roughness shading.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct
import sys
import bpy

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('feeding003_clay',HERE/'render_feeding.py')
CLAY=importlib.util.module_from_spec(spec);spec.loader.exec_module(CLAY)
renderer=CLAY.OLD.base.renderer
original_import=renderer.import_character
original_camera=renderer.frame_camera
output=Path(sys.argv[sys.argv.index('--output')+1])
output.mkdir(parents=True,exist_ok=True)
bindings=[]

# Both preserved renderer layers emit this receipt. Redirect only this exact
# optional preview side effect; never rewrite the frozen clay-side receipt.
original_write=Path.write_text
def isolated_write(path,data,*args,**kwargs):
    if path.resolve()==(HERE/'prop-coupling-receipt.json').resolve():
        path=output/'prop-coupling-receipt.json'
    return original_write(path,data,*args,**kwargs)
Path.write_text=isolated_write

def original_texture_import(path,clip,frames,fps):
    root,objects,timeline=original_import(path,clip,frames,fps)
    for obj in objects:
        if obj.type!='MESH' or not any(m.type=='ARMATURE' for m in obj.modifiers):continue
        for material in obj.data.materials:
            if not material or not material.use_nodes:raise ValueError('original skinned material nodes missing')
            bsdf=next(n for n in material.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
            links=list(bsdf.inputs['Base Color'].links)
            if not links or links[0].from_node.type!='TEX_IMAGE':raise ValueError('original base color image missing')
            node=links[0].from_node
            if not node.image or not obj.data.uv_layers:raise ValueError('original image or UVs missing')
            material.node_tree.nodes.active=node
            bindings.append({'object':obj.name,'material':material.name,'original_base_color_image':node.image.name,'size':list(node.image.size),'uv_layer':obj.data.uv_layers.active.name})
    if not bindings:raise ValueError('no original textured skinned materials found')
    timeline['texturedPresentation']='original embedded base color and UVs; Workbench studio texture preview, not full PBR'
    return root,objects,timeline

def textured_camera(*args,**kwargs):
    facts=original_camera(*args,**kwargs)
    bpy.context.scene.display.shading.color_type='TEXTURE'
    return facts

renderer.import_character=original_texture_import
renderer.frame_camera=textured_camera

if __name__=='__main__':
    try:
        status=renderer.main()
        candidate=Path(sys.argv[sys.argv.index('--candidate')+1]);raw=candidate.read_bytes()
        length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);binary=raw[28+length:]
        images=[]
        for image in doc.get('images',[]):
            view=doc['bufferViews'][image['bufferView']];start=view.get('byteOffset',0);data=binary[start:start+view['byteLength']]
            images.append({'name':image.get('name'),'mimeType':image['mimeType'],'embedded_sha256':hashlib.sha256(data).hexdigest()})
        (output/'original-texture-receipt.json').write_text(json.dumps({'candidate_sha256':hashlib.sha256(raw).hexdigest(),'renderer_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'material_mode':'ORIGINAL_BASE_COLOR_WORKBENCH_TEXTURE','limitations':'Original normal and metallic/roughness textures remain intact in GLB but are not evaluated by Workbench. No invented textures. Motion/UVs/material assets unchanged.','bindings':bindings,'embedded_images':images},indent=2)+'\n')
    finally:Path.write_text=original_write
    raise SystemExit(status)
