"""Geometry witnesses for the reduced physical foot, independent of contact spheres."""
import numpy as np

def add_material_witnesses(model, metadata, admission, recipe):
    import opensim as o
    policy=recipe.get('material_foot_clearance')
    if not policy:
        return
    mid=np.asarray(metadata['foot_geometry']['toe_midpoint_m'])
    witnesses=[]
    for side,suffix in [('left','l'),('right','r')]:
        vertices=np.asarray(admission['foot_surface'][side]['vertices_m'])
        # Admission uses the forward/up/lateral frame. Preserve measured
        # side-specific geometry; no species or artist bone names.
        x_edges=np.linspace(vertices[:,0].min()-1e-9,vertices[:,0].max()+1e-9,policy['longitudinal_bins']+1)
        z_edges=np.linspace(vertices[:,2].min()-1e-9,vertices[:,2].max()+1e-9,policy['lateral_bins']+1)
        for xi in range(len(x_edges)-1):
            for zi in range(len(z_edges)-1):
                select=vertices[(vertices[:,0]>=x_edges[xi])&(vertices[:,0]<x_edges[xi+1])&
                                (vertices[:,2]>=z_edges[zi])&(vertices[:,2]<z_edges[zi+1])]
                if not len(select):
                    continue
                point=select[np.argmin(select[:,1])].copy()
                distal=point[0]>mid[0]
                body_name=('digit_' if distal else 'toe_')+suffix
                local=point-mid if distal else point
                name=f'material_{suffix}_{xi}_{zi}'
                body=model.getBodySet().get(body_name)
                frame=o.PhysicalOffsetFrame(name,body,o.Transform(o.Vec3(*map(float,local))))
                model.addComponent(frame)
                metadata['clearance_frames'].append(dict(path='/'+name,minimum_height_m=policy['minimum_height_m']))
                witnesses.append(dict(path='/'+name,body=body_name,local_m=local.tolist(),side=side))
    metadata['material_foot_witnesses']=dict(points=witnesses,
        classification='Measured lower-envelope samples in the reduced two-part foot. Source skin deforms around separate digit pivots; final full-skin verification remains separate.')
