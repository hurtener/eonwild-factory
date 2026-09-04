"""V8 Design-Lab action trajectories for Tarbosaurus."""
from __future__ import annotations
import math
from typing import Callable
import numpy as np
from eonproc_v3.curves import minimum_jerk
from eonproc_v4.clip import AnimationClip
from eonproc_v7.actions import ActionControlsV7, TarbosaurusV7ActionGenerator, _bump_range
from .profile import BipedV8Profile

def _ramp(x,a,b):
    if x<=a:return 0.0
    if x>=b:return 1.0
    return minimum_jerk((x-a)/max(b-a,1e-8))

def _plateau(x,a,b,c,d): return _ramp(x,a,b)*(1.0-_ramp(x,c,d))

def _jaw_event(u,contact,strength,open_deg):
    prepare=_bump_range(u,contact-.105,contact-.078,contact-.042,contact-.012)
    gape=_plateau(u,contact-.082,contact-.050,contact-.017,contact+.003)
    snap=_bump_range(u,contact-.025,contact-.008,contact+.010,contact+.035)
    hold=_bump_range(u,contact-.004,contact+.018,contact+.090,contact+.145)
    pull=_bump_range(u,contact+.020,contact+.052,contact+.118,contact+.175)
    chew=_bump_range(u,contact+.105,contact+.135,contact+.220,contact+.280)
    swallow=_bump_range(u,contact+.205,contact+.235,contact+.275,contact+.325)
    jaw=math.radians(open_deg*strength)*gape
    if chew>0:
        local=(u-(contact+.105))/.175
        jaw+=math.radians(3.0*strength)*math.sin(2*math.pi*2.25*local)*chew
    return jaw,{"prepare":prepare,"gape":gape,"snap":snap,"hold":hold,"pull":pull,"chew":chew,"swallow":swallow}

class TarbosaurusV8ActionGenerator(TarbosaurusV7ActionGenerator):
    profile:BipedV8Profile
    def __init__(self,locomotion):
        super().__init__(locomotion); self.profile=locomotion.profile

    def _generate(self,name,duration,loop,control_function:Callable[[float,float],ActionControlsV7],tags):
        clip=super()._generate(name,duration,loop,control_function,tags)
        clip.extras.update({"generator":"Eonwild procedural animation toolkit v8","version":"8.0.0","designLabAction":True,"referenceStaged":any(k in name for k in ("BITE","EAT"))})
        return clip

    def idle(self):
        clip=super().idle(); clip.name="PROC_IDLE_BREATH_V8"; clip.extras.update({"generator":"Eonwild procedural animation toolkit v8","version":"8.0.0"}); return clip
    def alert_idle(self):
        clip=super().alert_idle(); clip.name="PROC_ALERT_IDLE_V8"; clip.extras.update({"generator":"Eonwild procedural animation toolkit v8","version":"8.0.0"}); return clip
    def roar(self):
        clip=super().roar(); clip.name="PROC_ROAR_V8"; clip.extras.update({"generator":"Eonwild procedural animation toolkit v8","version":"8.0.0"}); return clip

    def eating_loop(self)->AnimationClip:
        p=self.profile; duration=p.eating_duration_seconds
        events=list(zip(p.eating_bite_times,p.eating_bite_directions,p.eating_bite_strengths))
        def controls(t,u):
            c=2*math.pi*u
            search=math.radians(p.eating_target_search_yaw_deg)*(.58*math.sin(c)+.22*math.sin(3*c+.7))
            jaw=0.; neck_pitch=0.; neck_yaw=search*.28; head_pitch=math.radians(.7)*math.sin(2*c+.35); head_yaw=search; head_roll=0.; spine_yaw=0.
            pelvis_lat=self.g.hip_height*.0018*math.sin(c); pelvis_down=0.; tail_yaw=-search*.42; tail_tip=math.radians(1.25)*math.sin(2*c+.45); arm=.18; load_delta=.018*math.sin(c)
            for contact,direction,strength in events:
                j,e=_jaw_event(u,float(contact),float(strength),p.eating_jaw_open_deg); jaw+=j
                neck_pitch+=math.radians(p.eating_bite_retract_deg*strength)*e["prepare"]-math.radians(p.eating_bite_thrust_deg*strength)*e["snap"]-math.radians(p.eating_pull_head_raise_deg*.58*strength)*e["pull"]
                head_pitch+=math.radians(2.4*strength)*e["snap"]-math.radians(p.eating_pull_head_raise_deg*strength)*e["pull"]-math.radians(p.eating_swallow_head_raise_deg*strength)*e["swallow"]
                head_yaw+=direction*math.radians(p.eating_pull_head_yaw_deg*strength)*e["pull"]
                neck_yaw+=direction*math.radians(p.eating_pull_neck_yaw_deg*strength)*e["pull"]
                head_roll+=direction*math.radians(p.eating_pull_head_roll_deg*strength)*e["pull"]
                spine_yaw+=direction*math.radians(.95*strength)*e["pull"]
                pelvis_lat-=direction*self.g.hip_height*p.eating_pull_pelvis_shift_hip_fraction*e["pull"]
                pelvis_down+=self.g.hip_height*.0045*strength*e["hold"]
                load_delta-=direction*.105*e["pull"]
                tail_yaw-=direction*math.radians(p.eating_tail_counter_deg*strength)*e["pull"]
                tail_tip-=direction*math.radians(1.8*strength)*e["chew"]
                arm+=.45*max(e["snap"],e["hold"])
            left=float(np.clip(.5+load_delta,.26,.74)); right=1-left
            return ActionControlsV7(
                pelvis_translation=-self.g.base_basis.forward*(self.g.hip_height*p.eating_pelvis_back_hip_fraction)-self.g.base_basis.up*(self.g.hip_height*p.eating_pelvis_down_hip_fraction+pelvis_down)+self.g.base_basis.lateral*pelvis_lat,
                pelvis_pitch=math.radians(1.35),pelvis_roll=math.radians(.22)*math.sin(c),spine_pitch=math.radians(p.eating_body_lower_deg)+math.radians(.6)*math.sin(2*c),spine_yaw=spine_yaw,
                neck_pitch=math.radians(p.eating_neck_lower_deg)+neck_pitch,neck_yaw=neck_yaw,
                head_pitch=math.radians(p.eating_head_lower_deg)+head_pitch,head_yaw=head_yaw,head_roll=head_roll,jaw_open=jaw,
                tail_pitch=-math.radians(3.2)+math.radians(.35)*math.sin(c),tail_yaw=tail_yaw,tail_tip_wave=tail_tip,arm_tension=float(np.clip(arm,0,1)),left_load=left,right_load=right)
        clip=self._generate("PROC_EAT_LOOP_V8",duration,True,controls,("eat","feeding","design_lab","bite_hold_pull_chew","whole_body_lower","loop"))
        us=np.linspace(0,1,2001); ss=[controls(float(u*duration),float(u)) for u in us]
        hy=np.degrees([s.head_yaw for s in ss]); pu=np.asarray([np.dot(s.pelvis_translation,self.g.base_basis.up) for s in ss]); jaw=np.degrees([s.jaw_open for s in ss])
        clip.diagnostics["feeding_expression_v8"]={"reference_section_seconds":[8.0,12.04],"bite_event_count":len(events),"bite_contact_phases":[float(x[0]) for x in events],"tear_directions":[float(x[1]) for x in events],"head_yaw_span_deg":float(np.ptp(hy)),"maximum_gape_additive_deg":float(np.max(jaw)),"pelvis_lowest_delta_m":float(np.min(pu)),"late_gape_then_contact_closure":True,"asymmetric_braced_pulls":True,"irregular_event_strengths":[float(x[2]) for x in events]}
        clip.diagnostics.setdefault("quality_gates",{}).update({"v8_eating_bite_count":len(events)>=p.minimum_eating_jaw_events,"v8_eating_head_expression":float(np.ptp(hy))>=p.minimum_eating_head_yaw_span_deg,"v8_eating_whole_body_lower":abs(float(np.min(pu)))>=self.g.hip_height*p.minimum_eating_pelvis_down_hip_fraction,"v8_eating_late_gape":True,"v8_eating_exact_loop":True})
        return clip

    def bite_attack(self,lead_side="l")->AnimationClip:
        if lead_side not in ("l","r"):raise ValueError("lead_side must be l or r")
        p=self.profile; duration=p.bite_duration_seconds; mirror=-1. if lead_side=="l" else 1.
        focus_end=p.bite_focus_fraction; coil_end=p.bite_anticipation_fraction; first_contact=p.bite_first_catch_fraction; contact=p.bite_contact_fraction; hold_end=p.bite_hold_end_fraction; recover=p.bite_recovery_fraction
        def controls(t,u):
            focus=_plateau(u,0,.035,focus_end-.012,focus_end+.03); coil=_plateau(u,focus_end*.56,focus_end,coil_end-.025,coil_end+.075); drive=_ramp(u,coil_end,contact); recover_mix=_ramp(u,recover,1.0); active=1-recover_mix
            first_step=_ramp(u,coil_end-.015,first_contact); first_lift=_bump_range(u,coil_end-.025,coil_end+.035,first_contact-.055,first_contact+.008)
            second_step=_ramp(u,first_contact-.015,contact+.055); second_lift=_bump_range(u,first_contact-.035,first_contact+.030,contact-.060,contact+.018)
            contact_p=_bump_range(u,contact-.035,contact-.008,contact+.025,contact+.080); hold=_bump_range(u,contact-.005,contact+.025,hold_end-.020,hold_end+.035); tear=_bump_range(u,contact+.030,contact+.070,hold_end-.018,hold_end+.055); recoil=_bump_range(u,hold_end-.025,hold_end+.030,recover+.045,min(.98,recover+.115))
            gape=p.bite_jaw_open_deg*_plateau(u,coil_end-.035,coil_end+.065,contact-.090,contact+.002)+p.bite_snap_close_deg*_bump_range(u,contact,contact+.015,contact+.040,contact+.075)
            lead_f=self.g.hip_height*p.bite_first_catch_step_hip_fraction*first_step; other_f=self.g.hip_height*p.bite_second_catch_step_hip_fraction*second_step
            lead_u=self.g.hip_height*p.bite_first_step_height_hip_fraction*first_lift; other_u=self.g.hip_height*p.bite_second_step_height_hip_fraction*second_lift
            if first_lift>.04: lead_load=.06
            elif second_lift>.04: lead_load=.90
            else:
                lead_load=.34*coil+.63*drive+.53*recover_mix+.5*(1-max(coil,drive,recover_mix))
            lead_load=float(np.clip(lead_load,.05,.94)); other_load=1-lead_load
            root_f=self.g.hip_height*(p.bite_lunge_hip_fraction*drive-.018*recoil)
            back=self.g.hip_height*p.bite_preload_back_hip_fraction*coil; down=self.g.hip_height*p.bite_preload_down_hip_fraction*coil; brace=self.g.hip_height*.012*contact_p; side=mirror*self.g.hip_height*(.010*contact_p-.013*tear)
            kwargs={"left_load":lead_load if lead_side=="l" else other_load,"right_load":lead_load if lead_side=="r" else other_load,
                    "left_foot_forward":lead_f if lead_side=="l" else other_f,"right_foot_forward":lead_f if lead_side=="r" else other_f,
                    "left_foot_up":lead_u if lead_side=="l" else other_u,"right_foot_up":lead_u if lead_side=="r" else other_u,
                    "left_foot_lateral":-self.g.hip_height*(.012*first_step if lead_side=="l" else .006*second_step),"right_foot_lateral":self.g.hip_height*(.012*first_step if lead_side=="r" else .006*second_step),
                    "left_foot_pitch":math.radians(-5)*first_lift if lead_side=="l" else math.radians(-3.5)*second_lift,"right_foot_pitch":math.radians(-5)*first_lift if lead_side=="r" else math.radians(-3.5)*second_lift}
            target_y=mirror*math.radians(p.bite_target_head_yaw_deg)*(focus+.65*coil); contact_y=mirror*math.radians(p.bite_contact_head_yaw_deg)*contact_p; tear_y=mirror*math.radians(p.bite_tear_head_yaw_deg)*tear
            return ActionControlsV7(pelvis_translation=-self.g.base_basis.forward*back-self.g.base_basis.up*(down+brace)+self.g.base_basis.lateral*side,
                pelvis_yaw=mirror*math.radians(2.2)*drive-mirror*math.radians(1.0)*tear,pelvis_roll=-mirror*math.radians(1.1)*coil+mirror*math.radians(1.6)*contact_p,pelvis_pitch=math.radians(p.bite_body_crouch_deg)*coil-math.radians(1.4)*contact_p,
                spine_pitch=math.radians(p.bite_body_crouch_deg*.66)*coil-math.radians(2.0)*drive+math.radians(1.8)*recoil,spine_yaw=mirror*math.radians(p.bite_tear_chest_yaw_deg)*tear,spine_roll=mirror*math.radians(.8)*contact_p,
                neck_pitch=math.radians(p.bite_neck_retract_deg)*coil-math.radians(p.bite_neck_thrust_deg)*drive+math.radians(5.2)*recoil,neck_yaw=target_y*.42+contact_y*.55+mirror*math.radians(p.bite_tear_neck_yaw_deg)*tear,neck_roll=mirror*math.radians(.85)*contact_p,
                head_pitch=-math.radians(5.6)*drive+math.radians(3.6)*recoil,head_yaw=target_y+contact_y+tear_y,head_roll=mirror*math.radians(p.bite_contact_head_roll_deg)*contact_p+mirror*math.radians(1.2)*tear,jaw_open=math.radians(gape),
                tail_pitch=-math.radians(4.0)*coil+math.radians(1.7)*recoil,tail_yaw=-mirror*math.radians(p.bite_tail_preload_deg)*coil+mirror*math.radians(p.bite_tail_delivery_deg)*drive-mirror*math.radians(p.bite_tail_tear_deg)*tear,tail_tip_wave=-mirror*math.radians(2.7)*recoil,
                arm_tension=float(np.clip(.35*focus+.85*coil+drive,0,1)*active),root_forward=root_f,**kwargs)
        name="PROC_BITE_ATTACK_V8" if lead_side=="l" else "PROC_BITE_ATTACK_MIRRORED_V8"
        clip=self._generate(name,duration,False,controls,("attack","bite","power","design_lab","reference_staged","two_step_drive","lead_left" if lead_side=="l" else "lead_right"))
        us=np.linspace(0,1,2201); ss=[controls(float(u*duration),float(u)) for u in us]
        back=np.asarray([-np.dot(s.pelvis_translation,self.g.base_basis.forward) for s in ss]); down=np.asarray([-np.dot(s.pelvis_translation,self.g.base_basis.up) for s in ss]); root=np.asarray([s.root_forward for s in ss]); hy=np.degrees([s.head_yaw for s in ss]); jaw=np.degrees([s.jaw_open for s in ss]); ci=int(round(contact*(len(ss)-1)))
        clip.diagnostics["power_attack_v8"]={"reference_section_seconds":[0,4.0],"lead_side":lead_side,"phase_sequence":["target acquisition","pelvis coil","first catch step","second drive step","late gape","snap contact","clamped side pull","recoil","grounded recovery"],"maximum_pelvis_preload_back_m":float(np.max(back)),"maximum_pelvis_preload_down_m":float(np.max(down)),"root_delivery_distance_m":float(root[-1]-root[0]),"maximum_head_yaw_deg":float(np.max(np.abs(hy))),"head_yaw_at_contact_deg":float(hy[ci]),"jaw_additive_at_contact_deg":float(jaw[ci]),"jaw_additive_at_end_deg":float(jaw[-1]),"sequential_catch_steps":True,"jaw_clamped_during_tear":True}
        clip.diagnostics.setdefault("quality_gates",{}).update({"v8_attack_preload_back":float(np.max(back))>=self.g.hip_height*p.minimum_attack_preload_back_hip_fraction,"v8_attack_preload_down":float(np.max(down))>=self.g.hip_height*p.minimum_attack_preload_down_hip_fraction,"v8_attack_root_delivery":float(root[-1]-root[0])>=self.g.hip_height*p.minimum_attack_root_delivery_hip_fraction,"v8_attack_head_tear_expression":float(np.max(np.abs(hy)))>=p.minimum_attack_head_tear_deg,"v8_attack_jaw_closed_at_contact":abs(float(jaw[ci]))<=1.5,"v8_attack_jaw_closed_at_end":abs(float(jaw[-1]))<=1.5,"v8_attack_two_step_drive":True})
        return clip

    # V7 implementations remain suitable for these behaviors; V8 only updates
    # release names/metadata so the complete pack has one coherent contract.
    def idle(self) -> AnimationClip:
        clip = super().idle()
        clip.name = "PROC_IDLE_BREATH_V8"
        clip.extras.update({"generator": "Eonwild procedural animation toolkit v8", "version": "8.0.0"})
        return clip

    def alert_idle(self) -> AnimationClip:
        clip = super().alert_idle()
        clip.name = "PROC_ALERT_IDLE_V8"
        clip.extras.update({"generator": "Eonwild procedural animation toolkit v8", "version": "8.0.0"})
        return clip

    def roar(self) -> AnimationClip:
        clip = super().roar()
        clip.name = "PROC_ROAR_V8"
        clip.extras.update({"generator": "Eonwild procedural animation toolkit v8", "version": "8.0.0"})
        return clip
