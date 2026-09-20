"""BIRDS regression priors, Bishop et al. 2018, doi:10.1371/journal.pone.0192172.

Table 3 / S1 Code: measurements from birds, extrapolation for large theropods.
These priors never silently replace an animal's declared speed or stride.
"""
import math


def birds_prior(mass_kg, leg_length_m, speed_mps):
    for value in (mass_kg, leg_length_m, speed_mps):
        if isinstance(value, bool) or not math.isfinite(value) or value <= 0:
            raise ValueError('BIRDS inputs must be finite and positive')
    hip = leg_length_m*(1-10**(-.6306*math.log10(leg_length_m)-1.1332))
    if hip <= 0:
        raise ValueError('BIRDS regression outside positive hip-height domain')
    v = speed_mps/math.sqrt(9.81*hip)
    m = math.log10(mass_kg)
    duty = .52780422375284*v**(-.365104752160947)
    contact = (-.184074409*m+1.426471397)*v**(-.072544333*m-.826566689)*math.sqrt(hip/9.81)
    stride = ((-.222578494270505*m+1.49567259057578)*v+(-.105806577317077*m+1.20037956807526))*hip
    return dict(predicted_hip_height_m=hip,dimensionless_speed=v,duty_factor=duty,
                contact_s=contact,same_foot_stride_m=stride,
                vertical_coefficients=[.589745469*v+.872533513,
                    .889920213*v**.43699952-.532,-.216181615*v+.312681842,
                    -.069263155*v+.140078995,.003256995*v-.045581897,
                    -.026357637*v+.022511977])


def resolve_evidence(profile, gait, leg_length_m):
    mass = profile['authoring']['animalInstance']['measurements']['body_mass']
    if mass['unit'] != 'kg' or not mass.get('source', {}).get('citation'):
        raise ValueError('Running evidence requires a sourced mass proxy in kg')
    height = profile['authoring']['bodyHeightM']
    speed = gait.step_length_body_heights*height/gait.step_period_s
    prior = birds_prior(mass['value'],leg_length_m,speed)
    return dict(source='RUN-BIRDS-2018; Table 3 and S1 Code',
        classification='Bird regression extrapolation; selected aerial duty is an extant transfer, not a dinosaur measurement.',
        inputs=dict(mass_kg=mass['value'],mass_source=mass['source'],
                    admitted_leg_length_m=leg_length_m,speed_mps=speed),
        predicted=prior,applied=dict(duty_factor=gait.duty_factor,
                    contact_s=2*gait.duty_factor*gait.step_period_s,
                    same_foot_stride_m=2*gait.step_length_body_heights*height),
        reconciliation='Keep declared speed and stride; derive cadence exactly. Transfer measured aerial duty, normalize vertical impulse to the resulting contact duration. Predicted overlap is retained here as a reported conflict.')


class EmpiricalSupport:
    """Analytic force, impulse and displacement with a periodic velocity.

    Normalization changes force magnitude when the chosen aerial timing differs
    from BIRDS. It is a reduced body proxy, not articulated inverse dynamics.
    """
    def __init__(self, coefficients, contact):
        if not 0 < contact < 1:
            raise ValueError('Aerial support needs a nonzero flight interval')
        self.contact = contact
        area = sum(a*(1-(-1)**n)/(n*math.pi) for n,a in enumerate(coefficients,1))
        if not math.isfinite(area) or area <= 0:
            raise ValueError('Invalid empirical support integral')
        self.terms = [(a/(contact*area),n*math.pi/contact) for n,a in enumerate(coefficients,1)]
        if any(self.integrals(contact*i/1000)[0] < -1e-8 for i in range(1001)):
            raise ValueError('Regression predicts tensile ground support; outside supported domain')
        self.initial_velocity = .5-self.integrals(1.)[2]

    def integrals(self, phase):
        p = min(max(phase,0.),self.contact)
        load = sum(a*math.sin(k*p) for a,k in self.terms) if phase < self.contact else 0.
        impulse = sum(a/k*(1-math.cos(k*p)) for a,k in self.terms)
        displacement = sum(a/k*(p-math.sin(k*p)/k) for a,k in self.terms)
        return load,impulse,displacement+max(0.,phase-self.contact)

    def vertical(self, phase, gravity, step):
        p = phase % 1.
        load,impulse,displacement = self.integrals(p)
        return (gravity*step**2*(displacement-.5*p*p+self.initial_velocity*p),
                gravity*step*(impulse-p+self.initial_velocity),gravity*(load-1),load)
