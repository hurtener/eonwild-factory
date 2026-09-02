"""Fixed full-body review views; prop is an authored approximation only."""
import importlib.util
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
spec=importlib.util.spec_from_file_location('bite_fixed_views',ROOT/'build/V9-GROUNDED-COMMITTED-BITE-001/render_fixed_views.py')
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
original=base.renderer.import_character


def import_with_prop(path,clip_name,frame_count,fps):
    root,objects,timeline=original(path,clip_name,frame_count,fps)
    bpy.context.scene.render.threads_mode='FIXED'
    bpy.context.scene.render.threads=4
    prop=next(obj for obj in objects if obj.name.startswith('v9-bite-preview-target'))
    prop.name='feeding-soft-prop-AUTHORED-not-physics'
    prop.data.materials[0].diffuse_color=(0.50,0.13,0.06,1.)
    receipt=json.loads(path.with_name('receipt.json').read_text())
    center=prop.location.copy()
    radius=receipt['target']['preview_prop_radius_m']
    tissue=bpy.data.curves.new('feeding-tissue-connector-AUTHORED','CURVE')
    tissue.dimensions='3D'
    tissue.resolution_u=2
    tissue.bevel_resolution=2
    tissue.bevel_depth=.025
    spline=tissue.splines.new('POLY')
    spline.points.add(2)
    strand=bpy.data.objects.new('feeding-visible-grip-connector-not-force',tissue)
    bpy.context.collection.objects.link(strand)
    tissue_material=bpy.data.materials.new('feeding-tissue-proxy-warm-red')
    tissue_material.diffuse_color=(.68,.20,.085,1.)
    tissue.materials.append(tissue_material)
    objects.append(strand)
    coupling=[]
    # Keep the lowest ellipsoid surface on the floor while its upper edge
    # yields under the two pull intervals. This is not a tissue solver.
    for sample in receipt['samples']:
        time=sample['time_seconds']
        f=time/receipt['duration_seconds']*6
        active=(1.95<=f<3.25) or (3.71<=f<4.375)
        lift=0.
        if 1.95<=f<3.25:
            lift=max(0.,1-abs(f-3.05)/.35)*.055
        elif 3.71<=f<4.375:
            lift=max(0.,1-abs(f-4.02)/.35)*.025
        prop.scale=(1.3,1.8,.72+lift/radius)
        prop.location.z=center.z-radius*.28+lift
        frame=1+time*fps
        prop.keyframe_insert(data_path='scale',frame=frame)
        prop.keyframe_insert(data_path='location',frame=frame)
        # Attach to an actual fully-skinned rostral lower-oral witness, not
        # the air midpoint inside a wide gape. The connecting strand is the
        # deformable item; the floor prop need not sit inside the open jaws.
        mouth=sample['lower_mouth']
        end=Vector((mouth[0],-mouth[2],mouth[1]))
        anchor=Vector((center.x,center.y,center.z-radius+radius*1.25+lift))
        middle=(anchor+end)*.5
        middle.z-=.015
        for point,value in zip(spline.points,(anchor,middle,end)):
            point.co=(*value,1.)
            point.keyframe_insert(data_path='co',frame=frame)
        tissue.bevel_depth=.035 if active else 0.
        tissue.keyframe_insert(data_path='bevel_depth',frame=frame)
        coupling.append({'time_seconds':time,'grip_active':active,'lower_oral_surface_centroid_canonical':mouth,
                         'authored_connector_endpoint_error_m':0.,'prop_bottom_canonical_y':receipt['target']['ground_y_m'],
                         'prop_edge_lift_m':lift})
    # Explicit visibility changes are events, not interpolated materialization.
    if tissue.animation_data and tissue.animation_data.action:
        for layer in tissue.animation_data.action.layers:
            for strip in layer.strips:
                for slot in tissue.animation_data.action.slots:
                    bag=strip.channelbag(slot,ensure=False)
                    if bag:
                        for fc in bag.fcurves:
                            if fc.data_path=='bevel_depth':
                                for point in fc.keyframe_points:point.interpolation='CONSTANT'
    (path.parent/'prop-coupling-receipt.json').write_text(json.dumps({'authority':'AUTHORED_PREVIEW_APPROXIMATION_NOT_PHYSICS','samples':coupling},indent=2)+'\n')
    timeline['previewTargetProp']['behavior']='grounded ellipsoid edge yield and explicit lower-oral-surface tissue connector; authored approximation, not mechanics'
    return root,objects,timeline


base.renderer.import_character=import_with_prop
if __name__=='__main__':
    raise SystemExit(base.renderer.main())
