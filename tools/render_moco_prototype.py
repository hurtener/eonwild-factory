#!/usr/bin/env python3
"""Render the exact-model replay as a labeled mechanical video and figure."""
import argparse,json
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.animation import FFMpegWriter

p=argparse.ArgumentParser();p.add_argument('directory',type=Path);p.add_argument('--seconds',type=float,default=6);a=p.parse_args();root=a.directory
d=json.loads((root/'replay.json').read_text());frames=d['frames'];meta=d['metadata'];report=d['report'];period=frames[-1]['time_s'];bw=meta['mass_kg']*9.80665
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'text.color':'#dddfe0','axes.labelcolor':'#dddfe0','xtick.color':'#aab4b9','ytick.color':'#aab4b9'})
fig,ax=plt.subplots(figsize=(12.8,7.2),dpi=100);fig.patch.set_facecolor('#182127');ax.set_facecolor('#182127');fig.subplots_adjust(.03,.08,.98,.86)

def draw(t):
    half=int(t/period);local=t%period;i=min(int(round(local/period*(len(frames)-1))),len(frames)-1);r=frames[i]
    ax.clear();ax.set_facecolor('#182127');ax.set_xlim(-6.3,4);ax.set_ylim(-.35,4.6);ax.set_aspect('equal');ax.axis('off')
    rootx=r['bodies']['trunk']['origin'][0]
    ax.axhline(0,color='#82908e',linewidth=1)
    shift=(rootx+half*meta['admission']['step_length_m'])%1
    for x in np.arange(-7,6):ax.plot([x-shift,x+.15-shift],[0,-.1],color='#4e5c60',lw=.8)
    def xy(p):return [p[0]-rootx,p[1]]
    body=r['bodies'];tr=xy(body['trunk']['origin']);neck=xy(body['neck']['origin'])
    ax.plot([tr[0]-.22,neck[0]],[tr[1]+.08,neck[1]],color='#789e97',linewidth=38,solid_capstyle='round',alpha=.58)
    for name in ['tail_proximal','tail_distal','neck']:
        b=body[name];s,e=xy(b['origin']),xy(b['end']);width={'tail_proximal':17,'tail_distal':8,'neck':19}[name]
        ax.plot([s[0],e[0]],[s[1],e[1]],color='#8db5ab',lw=width,solid_capstyle='round',alpha=.85)
        ax.scatter(*s,s=27,color='#def5eb',zorder=4)
    h=xy(body['neck']['end']);ax.plot([h[0]-.15,h[0]+.4],[h[1],h[1]-.02],color='#aac8bb',lw=20,solid_capstyle='round')
    # Alternating half-strides swap the visual side, with no invented lateral motion.
    for suffix in (['r','l'] if half%2==0 else ['l','r']):
        near=(suffix=='l') != bool(half%2)
        col='#ecba78' if near else '#6c7f8e'
        for part,width in [('thigh',16),('shin',10),('metatarsus',7),('toe',5)]:
            b=body[part+'_'+suffix];s,e=xy(b['origin']),xy(b['end']);ax.plot([s[0],e[0]],[s[1],e[1]],color=col,lw=width,solid_capstyle='round');ax.scatter(*s,s=35,color='#e9e2d5' if near else '#93a6b4',zorder=5)
    for c in r['contacts']:
        s=xy(c['center']);f=np.array(c['force_N'])/bw
        if f[1]>.01:ax.arrow(s[0],0,f[0]*1.2,f[1]*1.2,color='#b2dbaa',width=.017,head_width=.09,length_includes_head=True,alpha=.85)
    com=xy(r['com_m']);ax.scatter(*com,s=60,marker='+',color='white',zorder=7)
    force=sum(c['force_N'][1] for c in r['contacts'])/bw
    ax.text(-6.1,4.35,'TARBO • MOCO MECHANICS PROTOTYPE',fontsize=16,weight='bold')
    ax.text(-6.1,4.0,f'{meta["mass_kg"]:,.0f} kg  ·  {meta["admission"]["preferred_speed_mps"]:.1f} m/s  ·  native time  ·  no root actuation',fontsize=11,color='#becacb')
    ax.text(-6.1,-.31,f'Contact support  {force:.2f} × body weight     |     arrows = computed ground forces',fontsize=10,color='#b2dbaa')
    ax.text(3.8,3.82,'PLANAR / TORQUE-DRIVEN\nEstimated strength and inertia\nNot Unity-retargeted or biologically validated',ha='right',va='top',fontsize=9,color='#c9b18f')
    if not report['optimizer']['success']:ax.text(3.8,4.35,'UNCONVERGED DIAGNOSTIC',ha='right',color='#ffb29b',weight='bold')

writer=FFMpegWriter(fps=24,codec='libx264',bitrate=3500,extra_args=['-pix_fmt','yuv420p','-movflags','+faststart'])
with writer.saving(fig,str(root/'tarbo-moco-prototype.mp4'),100):
    for i in range(round(a.seconds*24)):
        draw(i/24);writer.grab_frame()
draw(.15);fig.savefig(root/'preview.png',facecolor=fig.get_facecolor());plt.close(fig)

t=np.array([r['time_s'] for r in frames]);fig,axes=plt.subplots(2,2,figsize=(12,7),dpi=150);fig.patch.set_facecolor('#182127')
for ax in axes.flat:
    ax.set_facecolor('#182127');ax.grid(alpha=.15);ax.spines[['top','right']].set_visible(False);ax.set_xlabel('Time in half-stride (s)')
for side,col in [('l','#ecba78'),('r','#7eaccc')]:
    axes[0,0].plot(t,[180+np.degrees(r['coordinates']['knee_'+side]['value']) for r in frames],color=col,label=side.upper())
    axes[0,1].plot(t,[sum(c['force_N'][1] for c in r['contacts'] if c['name'].endswith('_'+side))/bw for r in frames],color=col,label=side.upper())
axes[0,0].set_ylabel('Knee opening (degrees)');axes[0,0].legend(facecolor='#182127',labelcolor='white');axes[0,1].set_ylabel('Vertical ground force / body weight')
axes[1,0].plot(t,[r['com_m'][1] for r in frames],color='#b2dbaa');axes[1,0].set_ylabel('Center of mass height (m)')
for name,col in [('pitch','#ecba78'),('tail_proximal','#b2dbaa'),('tail_distal','#7eaccc')]:axes[1,1].plot(t,[np.degrees(r['coordinates'][name]['value']) for r in frames],color=col,label=name.replace('_',' '))
axes[1,1].set_ylabel('Rotation (degrees)');axes[1,1].legend(facecolor='#182127',labelcolor='white',fontsize=8)
fig.suptitle('Moco prototype: motion and forces solved together\nEstimated physical parameters · half-stride symmetry · state replay',fontsize=14,color='white');fig.tight_layout(rect=[0,0,1,.93]);fig.savefig(root/'mechanics.png',facecolor=fig.get_facecolor());plt.close(fig)
print(root/'tarbo-moco-prototype.mp4')
