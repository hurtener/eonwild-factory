/** V5 runtime contract: one snapshot blend for arbitrary changes, exact handoff for authored bridges. */
export interface ClipInfo {
  name: string;
  duration: number;
  loop: boolean;
  extras?: Record<string, unknown>;
}

export interface PoseSnapshot {
  translations: Float32Array;
  rotations: Float32Array;
}

export interface AnimationBackend {
  clip(name: string): ClipInfo | undefined;
  sample(name: string, time: number, loop: boolean, rootOffset: [number, number, number]): PoseSnapshot;
  display(pose: PoseSnapshot): void;
  blend(source: PoseSnapshot, target: PoseSnapshot, weight: number): PoseSnapshot;
  root(pose: PoseSnapshot): [number, number, number];
}

export type PlayerState = "loading" | "playing" | "paused" | "queued_contact" | "transitioning" | "sequence" | "ended";

interface QueueItem { name: string; loop: boolean; }
interface PendingTransition { name: string; sourcePhase: number; }
interface SnapshotBlend { source: PoseSnapshot; target: ClipInfo; targetTime: number; targetLoop: boolean; rootOffset: [number,number,number]; elapsed: number; duration: number; }

const clamp01 = (value: number): number => Math.max(0, Math.min(1, value));
const minimumJerk = (value: number): number => { const t=clamp01(value); return t*t*t*(10+t*(-15+6*t)); };
const mod = (value: number, divisor: number): number => ((value % divisor) + divisor) % divisor;

export class AnimationControllerV5 {
  state: PlayerState = "loading";
  speed = 1;
  playing = false;
  current?: ClipInfo;
  time = 0;
  rootOffset: [number,number,number] = [0,0,0];
  queue: QueueItem[] = [];
  pending?: PendingTransition;
  blend?: SnapshotBlend;
  displayed?: PoseSnapshot;
  onState?: (controller: AnimationControllerV5) => void;

  constructor(private readonly backend: AnimationBackend) {}

  private notify(): void { this.onState?.(this); }
  private rootOffsetFor(source: PoseSnapshot, target: PoseSnapshot): [number,number,number] {
    const a=this.backend.root(source),b=this.backend.root(target);return [a[0]-b[0],a[1]-b[1],a[2]-b[2]];
  }

  start(name: string, loop: boolean, blendSeconds=0.28): void {
    const clip=this.backend.clip(name);if(!clip)throw new Error(`Unknown animation ${name}`);
    const source=this.displayed ?? this.backend.sample(name,0,loop,[0,0,0]);
    const raw=this.backend.sample(name,0,loop,[0,0,0]);
    const offset=this.rootOffsetFor(source,raw);
    if(!this.current||blendSeconds<=0){this.current=clip;this.time=0;this.rootOffset=offset;this.blend=undefined;this.displayed=this.backend.sample(name,0,loop,offset);}
    else this.blend={source,target:clip,targetTime:0,targetLoop:loop,rootOffset:offset,elapsed:0,duration:blendSeconds};
    this.playing=true;this.state=this.blend?"transitioning":"playing";this.notify();
  }

  queueAuthored(names: string[], returnClip: string): void {
    const clips=names.map(name=>this.backend.clip(name)).filter((value): value is ClipInfo => !!value);
    if(!clips.length)return;
    this.queue=clips.slice(1).map(clip=>({name:clip.name,loop:clip.name===returnClip}));
    const first=clips[0],sourcePhase=Number(first.extras?.sourcePhase ?? 0);
    if(this.current?.loop && first.extras?.transition===true && first.extras?.sourceClip===this.current.name){
      this.pending={name:first.name,sourcePhase};this.playing=true;this.state="queued_contact";this.notify();return;
    }
    this.start(first.name,false,0.28);this.state="sequence";this.notify();
  }

  private exactHandoff(item: QueueItem): void {
    if(!this.displayed)return;const clip=this.backend.clip(item.name);if(!clip)return;
    const raw=this.backend.sample(item.name,0,item.loop,[0,0,0]);
    this.rootOffset=this.rootOffsetFor(this.displayed,raw);this.current=clip;this.time=0;this.blend=undefined;
    this.displayed=this.backend.sample(item.name,0,item.loop,this.rootOffset);
  }

  update(deltaSeconds: number): void {
    if(!this.playing||!this.current)return;
    if(this.blend){const b=this.blend;b.elapsed+=deltaSeconds;b.targetTime+=deltaSeconds*this.speed;const target=this.backend.sample(b.target.name,b.targetTime,b.targetLoop,b.rootOffset);this.displayed=this.backend.blend(b.source,target,minimumJerk(b.elapsed/b.duration));this.backend.display(this.displayed);if(b.elapsed>=b.duration){this.current=b.target;this.time=b.targetTime;this.rootOffset=b.rootOffset;this.blend=undefined;this.state="playing";this.notify();}return;}
    const previous=this.time;this.time+=deltaSeconds*this.speed;
    if(this.pending&&this.current.loop){const duration=this.current.duration,target=this.pending.sourcePhase*duration,a=mod(previous,duration),b=mod(this.time,duration),crossed=a<=b?(a<=target&&target<=b):(target>=a||target<=b);if(crossed){this.time=target;this.displayed=this.backend.sample(this.current.name,target,true,this.rootOffset);const name=this.pending.name;this.pending=undefined;this.exactHandoff({name,loop:false});this.state="sequence";this.notify();}}
    if(!this.current.loop&&this.time>=this.current.duration){this.time=this.current.duration;this.displayed=this.backend.sample(this.current.name,this.time,false,this.rootOffset);if(this.queue.length){const next=this.queue.shift()!;this.exactHandoff(next);this.state=this.queue.length||!next.loop?"sequence":"playing";}else{this.playing=false;this.state="ended";}this.notify();}
    else this.displayed=this.backend.sample(this.current.name,this.time,this.current.loop,this.rootOffset);
    if(this.displayed)this.backend.display(this.displayed);
  }

  pause(): void { this.playing=false;this.state="paused";this.notify(); }
  resume(): void { this.playing=true;this.state="playing";this.notify(); }
  cancelQueue(): void { this.queue=[];this.pending=undefined;this.blend=undefined;this.state=this.playing?"playing":"paused";this.notify(); }
}
