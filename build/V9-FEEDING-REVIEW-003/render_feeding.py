"""Native fixed views with continuous grounded yield and mouth-held food proxy."""
import importlib.util
import json
from pathlib import Path
import sys
import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path.insert(0,str(ROOT/'build/V9-FEEDING-REVIEW-002'))
from channels import curve
spec=importlib.util.spec_from_file_location('feeding001_renderer',ROOT/'build/V9-FEEDING-REVIEW-001/render_feeding.py')
OLD=importlib.util.module_from_spec(spec)
spec.loader.exec_module(OLD)
original=OLD.base.renderer.import_character


def held_amount(time,windows):
    def smooth(x):
        x=max(0.,min(1.,x));return x*x*(3-2*x)
    return max((smooth((time-a)/.09)*smooth((b-time)/.09) for a,b in windows),default=0.)


def import_character(path,clip,frames,fps):
    root,objects,timeline=original(path,clip,frames,fps)
    receipt=json.loads(path.with_name('receipt.json').read_text())
    profile=json.loads(path.with_name('profile.json').read_text())
    prop=next(o for o in objects if o.name.startswith('feeding-soft-prop'))
    prop.animation_data_clear()
    center=Vector(receipt['target']['world_position_m'])
    base=Vector((center.x,-center.z,center.y))
    radius=receipt['target']['preview_prop_radius_m']
    strand=next(o for o in objects if o.name.startswith('feeding-visible-grip'))
    # Its oral endpoint remains bound to the emitted upper-oral anchor witness.
    strand.data.animation_data_clear()
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=1.)
    food=bpy.context.object
    food.name='held-food-fragment-AUTHORED-oral-proxy'
    food.data.materials.append(strand.data.materials[0])
    objects.append(food)
    coupling=[]
    for sample in receipt['samples']:
        t=sample['time_seconds'];phase=t*6/receipt['duration_seconds'];frame=1+t*fps
        yield_m=curve(phase,profile['prop_yield_keys_m'])
        prop.scale=(1.3,1.8,.72+yield_m/radius)
        prop.location=base+Vector((0.,0.,-radius*.28+yield_m))
        prop.keyframe_insert(data_path='scale',frame=frame)
        prop.keyframe_insert(data_path='location',frame=frame)
        upper=Vector(sample['upper_mouth']);lower=Vector(sample['lower_mouth'])
        release=profile['anchor']['release']
        blend=max(0.,min(1.,(phase-release)/.12));blend=blend*blend*(3-2*blend)
        location=(upper*.65+lower*.35)*(1-blend)+(lower*.90+upper*.10)*blend
        food.location=(location.x,-location.z,location.y)
        food_gain=held_amount(phase,profile['food_hold_windows'])
        r=profile['food_chunk_radius_m']
        food.scale=(r*food_gain,r*1.35*food_gain,r*.65*food_gain)
        food.keyframe_insert(data_path='location',frame=frame)
        food.keyframe_insert(data_path='scale',frame=frame)
        anchor=base+Vector((0,0,radius*.25+yield_m))
        end=Vector((upper.x,-upper.z,upper.y))
        middle=(anchor+end)*.5;middle.z-=.012
        for point,v in zip(strand.data.splines[0].points,(anchor,middle,end)):
            point.co=(*v,1.);point.keyframe_insert(data_path='co',frame=frame)
        strand.data.bevel_depth=.032*held_amount(phase,profile['grip_windows'])
        strand.data.keyframe_insert(data_path='bevel_depth',frame=frame)
        coupling.append({'time_seconds':t,'food_gain':food_gain,'food_center_canonical':list(location),
                         'connector_upper_oral_endpoint_canonical':list(upper),'prop_yield_m':yield_m,
                         'authority':'AUTHORED_NOT_PHYSICS'})
    (path.parent/'prop-coupling-receipt.json').write_text(json.dumps({'samples':coupling},indent=2)+'\n')
    timeline['previewTargetProp']['behavior']='Closed resisted oral anchor, then authored yield, backward return and chew fragment'
    return root,objects,timeline


OLD.base.renderer.import_character=import_character
if __name__=='__main__':raise SystemExit(OLD.base.renderer.main())
