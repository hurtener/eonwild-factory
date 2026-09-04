/* Eonwild Tarbosaurus V8 — dependency-free WebGL2 skeletal animation viewer.
 *
 * This intentionally avoids a framework/CDN so the validation build works offline.
 * It implements the GLB subset emitted by the V8 toolkit: one skinned primitive,
 * up to three JOINTS/WEIGHTS sets, standard LINEAR glTF animation channels,
 * embedded base-colour texture, 75-joint matrix-texture skinning, crossfades,
 * authored action sequences, orbit camera, procedural terrain, and contact shadows.
 */
(() => {
  "use strict";

  const $ = (id) => document.getElementById(id);
  const status = (message, kind = "") => {
    const el = $("status");
    if (el) { el.textContent = message; el.dataset.kind = kind; }
  };
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const mod = (v, p) => ((v % p) + p) % p;
  const mix = (a, b, t) => a + (b - a) * t;
  const smooth = (t) => { t = clamp(t, 0, 1); return t * t * (3 - 2 * t); };

  // ---------- compact math, column-major matrices ----------
  const V3 = {
    add: (a,b) => [a[0]+b[0],a[1]+b[1],a[2]+b[2]],
    sub: (a,b) => [a[0]-b[0],a[1]-b[1],a[2]-b[2]],
    scale: (a,s) => [a[0]*s,a[1]*s,a[2]*s],
    dot: (a,b) => a[0]*b[0]+a[1]*b[1]+a[2]*b[2],
    cross: (a,b) => [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]],
    len: (a) => Math.hypot(a[0],a[1],a[2]),
    norm: (a) => { const n=Math.hypot(a[0],a[1],a[2])||1; return [a[0]/n,a[1]/n,a[2]/n]; },
  };
  const M4 = {
    identity() { return new Float32Array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1]); },
    mul(a,b) {
      const o=new Float32Array(16);
      for(let c=0;c<4;c++) for(let r=0;r<4;r++) {
        o[c*4+r]=a[0*4+r]*b[c*4+0]+a[1*4+r]*b[c*4+1]+a[2*4+r]*b[c*4+2]+a[3*4+r]*b[c*4+3];
      }
      return o;
    },
    fromTRS(t,q,s) {
      const [x,y,z,w]=q, x2=x+x,y2=y+y,z2=z+z;
      const xx=x*x2,xy=x*y2,xz=x*z2, yy=y*y2,yz=y*z2,zz=z*z2, wx=w*x2,wy=w*y2,wz=w*z2;
      return new Float32Array([
        (1-(yy+zz))*s[0], (xy+wz)*s[0], (xz-wy)*s[0], 0,
        (xy-wz)*s[1], (1-(xx+zz))*s[1], (yz+wx)*s[1], 0,
        (xz+wy)*s[2], (yz-wx)*s[2], (1-(xx+yy))*s[2], 0,
        t[0],t[1],t[2],1,
      ]);
    },
    perspective(fovy,aspect,near,far) {
      const f=1/Math.tan(fovy/2), nf=1/(near-far), o=new Float32Array(16);
      o[0]=f/aspect;o[5]=f;o[10]=(far+near)*nf;o[11]=-1;o[14]=2*far*near*nf;return o;
    },
    lookAt(eye,target,up) {
      const z=V3.norm(V3.sub(eye,target)), x=V3.norm(V3.cross(up,z)), y=V3.cross(z,x);
      return new Float32Array([
        x[0],y[0],z[0],0, x[1],y[1],z[1],0, x[2],y[2],z[2],0,
        -V3.dot(x,eye),-V3.dot(y,eye),-V3.dot(z,eye),1,
      ]);
    },
    invert(a) {
      const o=new Float32Array(16);
      const a00=a[0],a01=a[1],a02=a[2],a03=a[3],a10=a[4],a11=a[5],a12=a[6],a13=a[7],a20=a[8],a21=a[9],a22=a[10],a23=a[11],a30=a[12],a31=a[13],a32=a[14],a33=a[15];
      const b00=a00*a11-a01*a10,b01=a00*a12-a02*a10,b02=a00*a13-a03*a10,b03=a01*a12-a02*a11,b04=a01*a13-a03*a11,b05=a02*a13-a03*a12,b06=a20*a31-a21*a30,b07=a20*a32-a22*a30,b08=a20*a33-a23*a30,b09=a21*a32-a22*a31,b10=a21*a33-a23*a31,b11=a22*a33-a23*a32;
      let det=b00*b11-b01*b10+b02*b09+b03*b08-b04*b07+b05*b06;if(!det)return M4.identity();det=1/det;
      o[0]=(a11*b11-a12*b10+a13*b09)*det;o[1]=(-a01*b11+a02*b10-a03*b09)*det;o[2]=(a31*b05-a32*b04+a33*b03)*det;o[3]=(-a21*b05+a22*b04-a23*b03)*det;
      o[4]=(-a10*b11+a12*b08-a13*b07)*det;o[5]=(a00*b11-a02*b08+a03*b07)*det;o[6]=(-a30*b05+a32*b02-a33*b01)*det;o[7]=(a20*b05-a22*b02+a23*b01)*det;
      o[8]=(a10*b10-a11*b08+a13*b06)*det;o[9]=(-a00*b10+a01*b08-a03*b06)*det;o[10]=(a30*b04-a31*b02+a33*b00)*det;o[11]=(-a20*b04+a21*b02-a23*b00)*det;
      o[12]=(-a10*b09+a11*b07-a12*b06)*det;o[13]=(a00*b09-a01*b07+a02*b06)*det;o[14]=(-a30*b03+a31*b01-a32*b00)*det;o[15]=(a20*b03-a21*b01+a22*b00)*det;return o;
    },
    translation(x,y,z) { const o=M4.identity();o[12]=x;o[13]=y;o[14]=z;return o; },
    scale(x,y,z) { const o=M4.identity();o[0]=x;o[5]=y;o[10]=z;return o; },
  };
  const Q = {
    norm(q) { const n=Math.hypot(...q)||1;return [q[0]/n,q[1]/n,q[2]/n,q[3]/n]; },
    nlerp(a,b,t) { let d=a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3]; const s=d<0?-1:1; return Q.norm([mix(a[0],b[0]*s,t),mix(a[1],b[1]*s,t),mix(a[2],b[2]*s,t),mix(a[3],b[3]*s,t)]); },
    slerp(a,b,t) { let d=a[0]*b[0]+a[1]*b[1]+a[2]*b[2]+a[3]*b[3],bb=b;if(d<0){d=-d;bb=[-b[0],-b[1],-b[2],-b[3]];}if(d>.9995)return Q.nlerp(a,bb,t);const th=Math.acos(clamp(d,-1,1)),sn=Math.sin(th),wa=Math.sin((1-t)*th)/sn,wb=Math.sin(t*th)/sn;return Q.norm([a[0]*wa+bb[0]*wb,a[1]*wa+bb[1]*wb,a[2]*wa+bb[2]*wb,a[3]*wa+bb[3]*wb]); },
  };

  const TYPE_WIDTH={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16};
  const COMPONENT={5120:Int8Array,5121:Uint8Array,5122:Int16Array,5123:Uint16Array,5125:Uint32Array,5126:Float32Array};
  const BYTES={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};

  function parseGLB(arrayBuffer) {
    const dv=new DataView(arrayBuffer);
    if(dv.getUint32(0,true)!==0x46546c67||dv.getUint32(4,true)!==2) throw new Error("Not a GLB 2.0 file");
    let p=12,json=null,bin=null;
    while(p<arrayBuffer.byteLength){const n=dv.getUint32(p,true),kind=dv.getUint32(p+4,true);p+=8;const chunk=arrayBuffer.slice(p,p+n);p+=n;if(kind===0x4e4f534a)json=JSON.parse(new TextDecoder().decode(chunk));else if(kind===0x004e4942)bin=chunk;}
    if(!json||!bin) throw new Error("GLB is missing JSON or BIN chunk");
    const access=(index) => {
      const a=json.accessors[index],v=json.bufferViews[a.bufferView],w=TYPE_WIDTH[a.type],Ctor=COMPONENT[a.componentType],bytes=BYTES[a.componentType],count=a.count;
      const offset=(v.byteOffset||0)+(a.byteOffset||0),stride=v.byteStride||w*bytes;
      if(stride===w*bytes && offset%bytes===0) return {data:new Ctor(bin,offset,count*w),count,width:w,componentType:a.componentType,type:a.type,normalized:!!a.normalized};
      const out=new Ctor(count*w),src=new DataView(bin);for(let i=0;i<count;i++)for(let j=0;j<w;j++){const o=offset+i*stride+j*bytes;let val;if(a.componentType===5126)val=src.getFloat32(o,true);else if(a.componentType===5125)val=src.getUint32(o,true);else if(a.componentType===5123)val=src.getUint16(o,true);else if(a.componentType===5122)val=src.getInt16(o,true);else if(a.componentType===5121)val=src.getUint8(o);else val=src.getInt8(o);out[i*w+j]=val;}return {data:out,count,width:w,componentType:a.componentType,type:a.type,normalized:!!a.normalized};
    };
    return {json,bin,access};
  }

  function compile(gl,type,source){const s=gl.createShader(type);gl.shaderSource(s,source);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw new Error(gl.getShaderInfoLog(s));return s;}
  function program(gl,vs,fs){const p=gl.createProgram();gl.attachShader(p,compile(gl,gl.VERTEX_SHADER,vs));gl.attachShader(p,compile(gl,gl.FRAGMENT_SHADER,fs));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw new Error(gl.getProgramInfoLog(p));return p;}
  function buffer(gl,target,data,usage=gl.STATIC_DRAW){const b=gl.createBuffer();gl.bindBuffer(target,b);gl.bufferData(target,data,usage);return b;}

  class TarbosaurusViewer {
    constructor(canvas) {
      this.canvas=canvas;this.gl=canvas.getContext("webgl2",{antialias:true,alpha:false,powerPreference:"high-performance"});
      if(!this.gl) throw new Error("WebGL2 is required");
      this.playing=true;this.speed=1;this.time=0;this.current=null;this.currentLoop=true;this.queue=[];this.pending=null;this.blend=null;this.rootOffset=[0,0,0];this.evaluatedPose=null;this.activeAction=null;this.playerState="loading";
      this.camera={yaw:.76,pitch:.24,distance:7.4,target:[0,.82,0]};this.drag=null;this.groundMode="flat";this.followRoot=true;this.rootPosition=[0,0,0];this.last=performance.now();
      this.installControls();this.initGL();
    }
    installControls(){
      const c=this.canvas;
      c.addEventListener("pointerdown",e=>{this.drag=[e.clientX,e.clientY,this.camera.yaw,this.camera.pitch];c.setPointerCapture(e.pointerId);});
      c.addEventListener("pointermove",e=>{if(!this.drag)return;this.camera.yaw=this.drag[2]-(e.clientX-this.drag[0])*.006;this.camera.pitch=clamp(this.drag[3]+(e.clientY-this.drag[1])*.004,-.12,1.1);});
      c.addEventListener("pointerup",()=>this.drag=null);c.addEventListener("pointercancel",()=>this.drag=null);
      c.addEventListener("wheel",e=>{e.preventDefault();this.camera.distance=clamp(this.camera.distance*Math.exp(e.deltaY*.001),3.8,14);},{passive:false});
    }
    initGL(){
      const gl=this.gl;gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.enable(gl.BLEND);gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
      this.skinProgram=program(gl,`#version 300 es
      precision highp float;precision highp int;uniform mat4 uView,uProj,uModel;uniform highp sampler2D uBones;
      in vec3 aPosition,aNormal;in vec2 aUV;in uvec4 aJoints0,aJoints1,aJoints2;in vec4 aWeights0,aWeights1,aWeights2;
      out vec3 vWorld,vNormal;out vec2 vUV;
      mat4 bone(uint i){int y=int(i);return mat4(texelFetch(uBones,ivec2(0,y),0),texelFetch(uBones,ivec2(1,y),0),texelFetch(uBones,ivec2(2,y),0),texelFetch(uBones,ivec2(3,y),0));}
      void main(){mat4 s=bone(aJoints0.x)*aWeights0.x+bone(aJoints0.y)*aWeights0.y+bone(aJoints0.z)*aWeights0.z+bone(aJoints0.w)*aWeights0.w+bone(aJoints1.x)*aWeights1.x+bone(aJoints1.y)*aWeights1.y+bone(aJoints1.z)*aWeights1.z+bone(aJoints1.w)*aWeights1.w+bone(aJoints2.x)*aWeights2.x+bone(aJoints2.y)*aWeights2.y+bone(aJoints2.z)*aWeights2.z+bone(aJoints2.w)*aWeights2.w;vec4 wp=uModel*s*vec4(aPosition,1.0);vWorld=wp.xyz;vNormal=normalize(mat3(uModel*s)*aNormal);vUV=aUV;gl_Position=uProj*uView*wp;}`,
      `#version 300 es
      precision highp float;uniform sampler2D uBase;uniform vec3 uEye;in vec3 vWorld,vNormal;in vec2 vUV;out vec4 outColor;
      void main(){vec3 base=texture(uBase,vUV).rgb;vec3 n=normalize(vNormal);vec3 l1=normalize(vec3(-.42,.78,-.47));vec3 l2=normalize(vec3(.55,.35,.62));float d1=max(dot(n,l1),0.0),d2=max(dot(n,l2),0.0);float hemi=.34+.24*(n.y*.5+.5);vec3 v=normalize(uEye-vWorld);vec3 h=normalize(l1+v);float spec=pow(max(dot(n,h),0.0),24.0)*.13;vec3 color=base*(hemi+d1*.72+d2*.18)+vec3(spec);float fog=clamp((length(uEye-vWorld)-8.0)/18.0,0.0,1.0);color=mix(color,vec3(.72,.78,.78),fog*.55);outColor=vec4(pow(color,vec3(1.0/2.2)),1.0);}`);
      this.groundProgram=program(gl,`#version 300 es
      precision highp float;uniform mat4 uView,uProj,uModel;in vec3 aPosition,aNormal;out vec3 vWorld,vNormal;void main(){vec4 w=uModel*vec4(aPosition,1);vWorld=w.xyz;vNormal=mat3(uModel)*aNormal;gl_Position=uProj*uView*w;}`,
      `#version 300 es
      precision highp float;uniform vec4 uColor;uniform vec3 uEye;in vec3 vWorld,vNormal;out vec4 outColor;void main(){float d=.46+.54*max(dot(normalize(vNormal),normalize(vec3(-.4,.8,-.35))),0.0);float fog=clamp((length(uEye-vWorld)-9.0)/20.0,0.0,1.0);vec3 c=mix(uColor.rgb*d,vec3(.72,.78,.78),fog*.7);outColor=vec4(c,uColor.a);}`);
    }
    async load(arrayBuffer,manifest){
      status("Parsing GLB…");this.asset=parseGLB(arrayBuffer);this.manifest=manifest;const {json,access,bin}=this.asset;this.nodes=json.nodes||[];this.parents=new Array(this.nodes.length).fill(-1);this.nodes.forEach((n,i)=>(n.children||[]).forEach(c=>this.parents[c]=i));this.nameToNode=new Map(this.nodes.map((n,i)=>[n.name||`node_${i}`,i]));
      this.restT=this.nodes.map(n=>(n.translation||[0,0,0]).slice());this.restR=this.nodes.map(n=>(n.rotation||[0,0,0,1]).slice());this.restS=this.nodes.map(n=>(n.scale||[1,1,1]).slice());this.localT=this.restT.map(v=>v.slice());this.localR=this.restR.map(v=>v.slice());this.localS=this.restS.map(v=>v.slice());this.world=this.nodes.map(()=>M4.identity());
      const meshNode=this.nodes.findIndex(n=>n.mesh!==undefined&&n.skin!==undefined);if(meshNode<0)throw new Error("No skinned mesh node");this.meshNode=meshNode;this.skinIndex=this.nodes[meshNode].skin;this.meshIndex=this.nodes[meshNode].mesh;this.primitive=json.meshes[this.meshIndex].primitives[0];this.skin=json.skins[this.skinIndex];this.skinNodes=this.skin.joints;this.inverseBind=access(this.skin.inverseBindMatrices).data;this.jointCount=this.skinNodes.length;
      this.buildAnimations();this.buildMesh();await this.buildTexture();this.buildGround();this.playClip("PROC_WALK_RELAXED_V8_1_INPLACE",true,0);this.playerState="playing";status(`Ready · ${this.clips.size} clips · ${this.jointCount} joints`,"ok");this.syncPlaybackUI();this.last=performance.now();requestAnimationFrame(t=>this.frame(t));
    }
    buildAnimations(){const {json,access}=this.asset;this.clips=new Map();const rootNode=this.nameToNode.get("Bone_000");for(const a of (json.animations||[])){const channels=[];let duration=0;for(const ch of a.channels){const s=a.samplers[ch.sampler],input=access(s.input).data,output=access(s.output).data;duration=Math.max(duration,input[input.length-1]||0);channels.push({node:ch.target.node,path:ch.target.path,times:input,values:output,width:ch.target.path==="rotation"?4:3});}const rootTranslation=channels.find(ch=>ch.node===rootNode&&ch.path==="translation");let rootCycleDelta=[0,0,0];if(rootTranslation&&rootTranslation.values.length>=6){const v=rootTranslation.values,n=v.length;rootCycleDelta=[v[n-3]-v[0],v[n-2]-v[1],v[n-1]-v[2]];}this.clips.set(a.name,{name:a.name,channels,duration,extras:a.extras||{},rootCycleDelta});} }
    attribute(name,index,integer=false){const gl=this.gl,a=this.asset.access(this.primitive.attributes[name]);const b=buffer(gl,gl.ARRAY_BUFFER,a.data);gl.bindBuffer(gl.ARRAY_BUFFER,b);gl.enableVertexAttribArray(index);const type=a.componentType===5126?gl.FLOAT:a.componentType===5125?gl.UNSIGNED_INT:a.componentType===5123?gl.UNSIGNED_SHORT:a.componentType===5121?gl.UNSIGNED_BYTE:gl.BYTE;if(integer)gl.vertexAttribIPointer(index,a.width,type,0,0);else gl.vertexAttribPointer(index,a.width,type,a.normalized,0,0);return b;}
    buildMesh(){const gl=this.gl,p=this.skinProgram;this.vao=gl.createVertexArray();gl.bindVertexArray(this.vao);const loc=n=>gl.getAttribLocation(p,n);this.attribute("POSITION",loc("aPosition"));this.attribute("NORMAL",loc("aNormal"));this.attribute("TEXCOORD_0",loc("aUV"));for(let i=0;i<3;i++){this.attribute(`JOINTS_${i}`,loc(`aJoints${i}`),true);this.attribute(`WEIGHTS_${i}`,loc(`aWeights${i}`));}const idx=this.asset.access(this.primitive.indices);this.indexBuffer=buffer(gl,gl.ELEMENT_ARRAY_BUFFER,idx.data);this.indexCount=idx.data.length;this.indexType=idx.componentType===5125?gl.UNSIGNED_INT:gl.UNSIGNED_SHORT;gl.bindVertexArray(null);
      this.boneTexture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.boneTexture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.NEAREST);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.CLAMP_TO_EDGE);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.CLAMP_TO_EDGE);this.boneData=new Float32Array(this.jointCount*16);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA32F,4,this.jointCount,0,gl.RGBA,gl.FLOAT,this.boneData);
    }
    async buildTexture(){const gl=this.gl,{json,bin}=this.asset;const mat=json.materials?.[this.primitive.material||0],ti=mat?.pbrMetallicRoughness?.baseColorTexture?.index??0,tex=json.textures?.[ti],image=json.images?.[tex?.source??0];this.baseTexture=gl.createTexture();gl.bindTexture(gl.TEXTURE_2D,this.baseTexture);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MIN_FILTER,gl.LINEAR_MIPMAP_LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_MAG_FILTER,gl.LINEAR);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_S,gl.REPEAT);gl.texParameteri(gl.TEXTURE_2D,gl.TEXTURE_WRAP_T,gl.REPEAT);if(image?.bufferView!==undefined){const v=json.bufferViews[image.bufferView],blob=new Blob([bin.slice(v.byteOffset||0,(v.byteOffset||0)+v.byteLength)],{type:image.mimeType||"image/jpeg"}),bmp=await createImageBitmap(blob);gl.pixelStorei(gl.UNPACK_FLIP_Y_WEBGL,false);gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,bmp.width,bmp.height,0,gl.RGBA,gl.UNSIGNED_BYTE,bmp);gl.generateMipmap(gl.TEXTURE_2D);}else{gl.texImage2D(gl.TEXTURE_2D,0,gl.RGBA,1,1,0,gl.RGBA,gl.UNSIGNED_BYTE,new Uint8Array([155,120,80,255]));}}
    terrainHeight(x,z){if(this.groundMode==="uneven")return .075*Math.sin(2*Math.PI*z/3.4)+.041*Math.sin(2*Math.PI*z/6.46+.7)+.018*Math.sin(2*Math.PI*(x+.35*z)/1.632+1.1);if(this.groundMode==="slope")return -.12*z;return 0;}
    buildGround(){const gl=this.gl,N=90,size=22,positions=[],normals=[],indices=[];for(let z=0;z<=N;z++)for(let x=0;x<=N;x++){const px=(x/N-.5)*size,pz=(z/N-.5)*size,eps=.03,h=this.terrainHeight(px,pz),dx=(this.terrainHeight(px+eps,pz)-this.terrainHeight(px-eps,pz))/(2*eps),dz=(this.terrainHeight(px,pz+eps)-this.terrainHeight(px,pz-eps))/(2*eps),n=V3.norm([-dx,1,-dz]);positions.push(px,h,pz);normals.push(...n);}for(let z=0;z<N;z++)for(let x=0;x<N;x++){const a=z*(N+1)+x,b=a+1,c=a+N+1,d=c+1;indices.push(a,c,b,b,c,d);}this.groundVAO=gl.createVertexArray();gl.bindVertexArray(this.groundVAO);const p=this.groundProgram;let b=buffer(gl,gl.ARRAY_BUFFER,new Float32Array(positions));gl.bindBuffer(gl.ARRAY_BUFFER,b);let l=gl.getAttribLocation(p,"aPosition");gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0);b=buffer(gl,gl.ARRAY_BUFFER,new Float32Array(normals));gl.bindBuffer(gl.ARRAY_BUFFER,b);l=gl.getAttribLocation(p,"aNormal");gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0);this.groundIB=buffer(gl,gl.ELEMENT_ARRAY_BUFFER,new Uint32Array(indices));this.groundCount=indices.length;gl.bindVertexArray(null);
      const seg=48,disc=[];for(let i=0;i<seg;i++){const a=2*Math.PI*i/seg,b=2*Math.PI*(i+1)/seg;disc.push(0,0,0,Math.cos(a),0,Math.sin(a),Math.cos(b),0,Math.sin(b));}this.discVAO=gl.createVertexArray();gl.bindVertexArray(this.discVAO);const db=buffer(gl,gl.ARRAY_BUFFER,new Float32Array(disc));gl.bindBuffer(gl.ARRAY_BUFFER,db);l=gl.getAttribLocation(p,"aPosition");gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0);const zeros=new Float32Array(disc.length);for(let i=1;i<zeros.length;i+=3)zeros[i]=1;const nb=buffer(gl,gl.ARRAY_BUFFER,zeros);gl.bindBuffer(gl.ARRAY_BUFFER,nb);l=gl.getAttribLocation(p,"aNormal");gl.enableVertexAttribArray(l);gl.vertexAttribPointer(l,3,gl.FLOAT,false,0,0);this.discCount=seg*3;gl.bindVertexArray(null);
    }
    rebuildGround(mode){if(this.groundMode===mode)return;this.groundMode=mode;this.buildGround();}
    sampleChannel(ch,t,loop){const ts=ch.times,dur=ts[ts.length-1];if(loop)t=mod(t,dur);else t=clamp(t,0,dur);let lo=0,hi=ts.length-1;while(lo+1<hi){const m=(lo+hi)>>1;if(ts[m]<=t)lo=m;else hi=m;}const t0=ts[lo],t1=ts[Math.min(lo+1,ts.length-1)],u=t1>t0?(t-t0)/(t1-t0):0,w=ch.width,o0=lo*w,o1=Math.min(lo+1,ts.length-1)*w,a=Array.from(ch.values.slice(o0,o0+w)),b=Array.from(ch.values.slice(o1,o1+w));return ch.path==="rotation"?Q.slerp(a,b,u):a.map((v,i)=>mix(v,b[i],u));}
    poseFor(clip,t,loop,offset=this.rootOffset){const T=this.restT.map(v=>v.slice()),R=this.restR.map(v=>v.slice());if(clip)for(const ch of clip.channels){const v=this.sampleChannel(ch,t,loop);if(ch.path==="translation")T[ch.node]=v;else if(ch.path==="rotation")R[ch.node]=v;}const root=this.nameToNode.get("Bone_000");if(root!==undefined&&clip&&loop&&clip.duration>0){const cycles=Math.floor(Math.max(0,t)/clip.duration);if(cycles>0){const d=clip.rootCycleDelta||[0,0,0];T[root]=[T[root][0]+d[0]*cycles,T[root][1]+d[1]*cycles,T[root][2]+d[2]*cycles];}}if(root!==undefined&&offset)T[root]=[T[root][0]+offset[0],T[root][1]+offset[1],T[root][2]+offset[2]];return {T,R};}
    blendPoses(a,b,f){const T=a.T.map((v,i)=>v.map((x,j)=>mix(x,b.T[i][j],f))),R=a.R.map((q,i)=>Q.slerp(q,b.R[i],f));return {T,R};}
    applyEvaluatedPose(pose){this.evaluatedPose=pose;this.localT=pose.T;this.localR=pose.R;for(let i=0;i<this.nodes.length;i++){const local=M4.fromTRS(pose.T[i],pose.R[i],this.restS[i]),p=this.parents[i];this.world[i]=p<0?local:M4.mul(this.world[p],local);}const meshWorld=this.world[this.meshNode],meshInv=M4.invert(meshWorld);for(let j=0;j<this.jointCount;j++){const node=this.skinNodes[j],ib=this.inverseBind.slice(j*16,j*16+16),sm=M4.mul(M4.mul(meshInv,this.world[node]),ib);this.boneData.set(sm,j*16);}const root=this.nameToNode.get("Bone_000");if(root!==undefined)this.rootPosition=[this.world[root][12],this.world[root][13],this.world[root][14]];}
    computeRootOffset(sourcePose,targetPose){const root=this.nameToNode.get("Bone_000");if(root===undefined)return [0,0,0];return sourcePose.T[root].map((v,i)=>v-targetPose.T[root][i]);}
    commitClip(name,loop=true,exactHandoff=false){const clip=this.clips.get(name);if(!clip){status(`Missing clip: ${name}`,"error");return false;}const source=this.evaluatedPose||this.poseFor(this.current,this.time,this.currentLoop);const raw=this.poseFor(clip,0,loop,[0,0,0]);this.rootOffset=source?this.computeRootOffset(source,raw):[0,0,0];this.current=clip;this.currentLoop=loop;this.time=0;this.blend=null;this.playing=true;this.playerState=exactHandoff?"exact handoff":"playing";this.setModeForClip(name);this.updateHUD(name);this.syncPlaybackUI();return true;}
    startSnapshotBlend(name,loop=true,duration=.28){const clip=this.clips.get(name);if(!clip){status(`Missing clip: ${name}`,"error");return false;}const source=this.evaluatedPose||this.poseFor(this.current,this.time,this.currentLoop);let targetTime=0;if(this.current&&this.currentLoop&&loop){targetTime=(mod(this.time,this.current.duration)/this.current.duration)*clip.duration;}const raw=this.poseFor(clip,targetTime,loop,[0,0,0]),offset=this.computeRootOffset(source,raw);this.blend={source,clip,loop,targetTime,elapsed:0,duration:Math.max(.08,duration),rootOffset:offset};this.playing=true;this.playerState="transitioning";this.setModeForClip(name);this.updateHUD(name);this.syncPlaybackUI();return true;}
    playClip(name,loop=true,blendDuration=.28,keepQueue=false){if(!keepQueue){this.queue=[];this.pending=null;this.activeAction=null;}if(!this.current||blendDuration<=0)return this.commitClip(name,loop,false);return this.startSnapshotBlend(name,loop,blendDuration);}
    queueSequence(items,actionName="sequence"){const valid=items.filter(name=>this.clips.has(name));if(!valid.length){status("No clips available for sequence","error");return;}this.queue=valid.slice(1).map((name,index)=>({name,loop:index===valid.length-2&&this.clips.get(name).extras.loop===true,exactHandoff:true}));this.activeAction=actionName;const first=this.clips.get(valid[0]),source=first.extras.sourceClip,phase=Number(first.extras.sourcePhase??0);if(this.current&&this.currentLoop&&source===this.current.name){const currentPhase=mod(this.time,this.current.duration)/this.current.duration,delay=mod(phase-currentPhase,1)*this.current.duration;this.pending={name:valid[0],loop:false,at:this.time+delay};this.playerState="waiting for contact-safe phase";status(`Queued ${actionName} · contact-safe entry`,"ok");this.syncPlaybackUI();}else this.startSnapshotBlend(valid[0],false,.24);}
    commitQueuedClip(){if(!this.queue.length){this.activeAction=null;this.playerState="playing";return false;}const item=this.queue.shift();this.commitClip(item.name,item.loop,true);if(!this.queue.length&&item.loop)this.activeAction=null;return true;}
    cancelSequence(){this.queue=[];this.pending=null;this.activeAction=null;this.playerState=this.playing?"playing":"paused";status("Sequence cancelled","ok");this.syncPlaybackUI();}
    updatePose(dt){if(!this.current)return;if(this.pending&&this.playing){this.time+=dt*this.speed;if(this.time>=this.pending.at){const p=this.pending;this.pending=null;this.commitClip(p.name,p.loop,true);}}else if(this.blend&&this.playing){this.blend.elapsed+=dt;this.blend.targetTime+=dt*this.speed;const target=this.poseFor(this.blend.clip,this.blend.targetTime,this.blend.loop,this.blend.rootOffset),f=smooth(this.blend.elapsed/this.blend.duration),pose=this.blendPoses(this.blend.source,target,f);this.applyEvaluatedPose(pose);if(f>=1){this.current=this.blend.clip;this.currentLoop=this.blend.loop;this.time=this.blend.targetTime;this.rootOffset=this.blend.rootOffset;this.blend=null;this.playerState="playing";}this.syncPlaybackUI();return;}else if(this.playing)this.time+=dt*this.speed;
      if(!this.blend){const ended=!this.currentLoop&&this.time>=this.current.duration;if(ended){this.time=this.current.duration;const pose=this.poseFor(this.current,this.time,false);this.applyEvaluatedPose(pose);if(!this.commitQueuedClip()){this.playing=false;this.playerState="ended";}this.syncPlaybackUI();return;}this.applyEvaluatedPose(this.poseFor(this.current,this.time,this.currentLoop));}this.syncPlaybackUI();}
    setModeForClip(name){if(name.includes("UNEVEN"))this.rebuildGround("uneven");else if(name.includes("UPSLOPE"))this.rebuildGround("slope");else this.rebuildGround("flat");this.followRoot=name.includes("ROOTMOTION")||name.includes("TURN")||name.includes("START")||name.includes("BRAKE");}
    updateHUD(name){if($("clipName"))$("clipName").textContent=name.replace(/^PROC_/,"").replace(/_V8.*/,"").replaceAll("_"," ");}
    syncPlaybackUI(){const button=$("playPause");if(button)button.textContent=this.playing?"Pause":"Play";if($("playerState"))$("playerState").textContent=this.playerState;if($("sequenceStatus"))$("sequenceStatus").textContent=this.activeAction?`${this.activeAction} · ${this.queue.length+(this.pending?1:0)} queued`:"none";document.querySelectorAll("[data-clip]").forEach(b=>{const active=(this.current&&b.dataset.clip===this.current.name)||(this.blend&&b.dataset.clip===this.blend.clip.name);b.classList.toggle("is-active",!!active);b.setAttribute("aria-pressed",active?"true":"false");});document.querySelectorAll("[data-action]").forEach(b=>{const active=b.dataset.action===this.activeAction;b.classList.toggle("is-active",active);b.setAttribute("aria-pressed",active?"true":"false");});const line=$("timeline");if(line&&this.current&&!this.blend){line.max=this.current.duration;line.value=this.currentLoop?mod(this.time,this.current.duration):Math.min(this.time,this.current.duration);}if($("timeLabel")&&this.current)$("timeLabel").textContent=`${(this.currentLoop?mod(this.time,this.current.duration):Math.min(this.time,this.current.duration)).toFixed(2)} / ${this.current.duration.toFixed(2)} s`;}
    action(kind){const map={normal:["PROC_WALK_TO_BITE_READY_V8_1","PROC_NORMAL_ATTACK_V8_1","PROC_BITE_TO_WALK_V8_1","PROC_WALK_RELAXED_V8_1_INPLACE"],normalMirrored:["PROC_WALK_TO_BITE_READY_MIRRORED_V8_1","PROC_NORMAL_ATTACK_MIRRORED_V8_1","PROC_BITE_MIRRORED_TO_WALK_V8_1","PROC_WALK_RELAXED_V8_1_INPLACE"],power:["PROC_WALK_TO_POWER_ATTACK_V8_1","PROC_POWER_ATTACK_V8_1","PROC_POWER_ATTACK_TO_EAT_V8_1","PROC_EAT_LOOP_V8_1"],powerMirrored:["PROC_WALK_TO_POWER_ATTACK_MIRRORED_V8_1","PROC_POWER_ATTACK_MIRRORED_V8_1","PROC_POWER_ATTACK_MIRRORED_TO_EAT_V8_1","PROC_EAT_LOOP_V8_1"],roar:["PROC_WALK_TO_ROAR_READY_V8_1","PROC_ROAR_V8_1","PROC_ROAR_TO_WALK_V8_1","PROC_WALK_RELAXED_V8_1_INPLACE"],eat:["PROC_WALK_TO_EAT_V8_1","PROC_EAT_LOOP_V8_1","PROC_EAT_TO_WALK_V8_1","PROC_WALK_RELAXED_V8_1_INPLACE"],alert:["PROC_WALK_TO_ALERT_WALK_V8_1","PROC_ALERT_WALK_V8_1_INPLACE"]};this.queueSequence(map[kind]||map.normal,kind);}
    frame(now){const dt=Math.min(.05,(now-this.last)/1000);this.last=now;if(this.playing)this.updatePose(dt);this.draw();requestAnimationFrame(t=>this.frame(t));}
    draw(){const gl=this.gl,w=this.canvas.clientWidth,h=this.canvas.clientHeight,dpr=Math.min(devicePixelRatio||1,2);if(this.canvas.width!==Math.round(w*dpr)||this.canvas.height!==Math.round(h*dpr)){this.canvas.width=Math.round(w*dpr);this.canvas.height=Math.round(h*dpr);}gl.viewport(0,0,this.canvas.width,this.canvas.height);gl.clearColor(.70,.77,.78,1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);
      const target=this.followRoot?[this.rootPosition[0],this.rootPosition[1]+.85,this.rootPosition[2]]:[0,.85,0];this.camera.target=target;const cp=Math.cos(this.camera.pitch),eye=[target[0]+this.camera.distance*cp*Math.cos(this.camera.yaw),target[1]+this.camera.distance*Math.sin(this.camera.pitch),target[2]+this.camera.distance*cp*Math.sin(this.camera.yaw)],view=M4.lookAt(eye,target,[0,1,0]),proj=M4.perspective(Math.PI/4,this.canvas.width/this.canvas.height,.03,80);
      gl.useProgram(this.groundProgram);gl.uniformMatrix4fv(gl.getUniformLocation(this.groundProgram,"uView"),false,view);gl.uniformMatrix4fv(gl.getUniformLocation(this.groundProgram,"uProj"),false,proj);gl.uniform3fv(gl.getUniformLocation(this.groundProgram,"uEye"),eye);gl.uniformMatrix4fv(gl.getUniformLocation(this.groundProgram,"uModel"),false,M4.identity());gl.uniform4f(gl.getUniformLocation(this.groundProgram,"uColor"),.32,.38,.32,1);gl.bindVertexArray(this.groundVAO);gl.drawElements(gl.TRIANGLES,this.groundCount,gl.UNSIGNED_INT,0);
      // Contact-shadow discs under the semantic feet.
      gl.depthMask(false);gl.uniform4f(gl.getUniformLocation(this.groundProgram,"uColor"),.02,.025,.02,.20);gl.bindVertexArray(this.discVAO);for(const name of ["Bone_008","Bone_012"]){const n=this.nameToNode.get(name);if(n===undefined)continue;const x=this.world[n][12],z=this.world[n][14],y=this.terrainHeight(x,z)+.006,model=M4.mul(M4.translation(x,y,z),M4.scale(.34,1,.58));gl.uniformMatrix4fv(gl.getUniformLocation(this.groundProgram,"uModel"),false,model);gl.drawArrays(gl.TRIANGLES,0,this.discCount);}gl.depthMask(true);
      gl.useProgram(this.skinProgram);gl.uniformMatrix4fv(gl.getUniformLocation(this.skinProgram,"uView"),false,view);gl.uniformMatrix4fv(gl.getUniformLocation(this.skinProgram,"uProj"),false,proj);gl.uniformMatrix4fv(gl.getUniformLocation(this.skinProgram,"uModel"),false,this.world[this.meshNode]);gl.uniform3fv(gl.getUniformLocation(this.skinProgram,"uEye"),eye);gl.activeTexture(gl.TEXTURE0);gl.bindTexture(gl.TEXTURE_2D,this.boneTexture);gl.texSubImage2D(gl.TEXTURE_2D,0,0,0,4,this.jointCount,gl.RGBA,gl.FLOAT,this.boneData);gl.uniform1i(gl.getUniformLocation(this.skinProgram,"uBones"),0);gl.activeTexture(gl.TEXTURE1);gl.bindTexture(gl.TEXTURE_2D,this.baseTexture);gl.uniform1i(gl.getUniformLocation(this.skinProgram,"uBase"),1);gl.bindVertexArray(this.vao);gl.disable(gl.CULL_FACE);gl.drawElements(gl.TRIANGLES,this.indexCount,this.indexType,0);gl.bindVertexArray(null);
      if($("timeLabel")&&this.current)$("timeLabel").textContent=`${(this.currentLoop?mod(this.time,this.current.duration):Math.min(this.time,this.current.duration)).toFixed(2)} / ${this.current.duration.toFixed(2)} s`;
    }
  }

  async function loadBytes(){
    if(window.__EONWILD_V8_1_1_GLB_BASE64){status("Decoding embedded animation pack…");const s=window.__EONWILD_V8_1_1_GLB_BASE64,chunk=1<<20,parts=[];for(let i=0;i<s.length;i+=chunk){const raw=atob(s.slice(i,i+chunk)),a=new Uint8Array(raw.length);for(let j=0;j<raw.length;j++)a[j]=raw.charCodeAt(j);parts.push(a);}const total=parts.reduce((n,a)=>n+a.length,0),all=new Uint8Array(total);let p=0;for(const a of parts){all.set(a,p);p+=a.length;}return all.buffer;}
    const response=await fetch("./tarbosaurus_procedural_v8_1_animation_pack.glb");if(!response.ok)throw new Error(`GLB fetch failed: ${response.status}`);return response.arrayBuffer();
  }
  async function loadManifest(){if(window.__EONWILD_V8_1_1_MANIFEST)return window.__EONWILD_V8_1_1_MANIFEST;const r=await fetch("./animation-manifest.v8.1.json");return r.json();}
  async function boot(){try{const viewer=new TarbosaurusViewer($("stage"));window.v8Viewer=viewer;const [bytes,manifest]=await Promise.all([loadBytes(),loadManifest()]);await viewer.load(bytes,manifest);
      document.querySelectorAll("[data-clip]").forEach(b=>b.addEventListener("click",()=>viewer.playClip(b.dataset.clip,b.dataset.loop!=="false",.28)));
      document.querySelectorAll("[data-action]").forEach(b=>b.addEventListener("click",()=>viewer.action(b.dataset.action)));
      $("playPause")?.addEventListener("click",()=>{if(!viewer.playing&&viewer.playerState==="ended"){viewer.time=0;viewer.playerState="playing";}viewer.playing=!viewer.playing;viewer.playerState=viewer.playing?"playing":"paused";viewer.syncPlaybackUI();});
      $("cancelSequence")?.addEventListener("click",()=>viewer.cancelSequence());
      $("timeline")?.addEventListener("input",e=>{if(!viewer.current)return;viewer.playing=false;viewer.blend=null;viewer.time=Number(e.target.value);viewer.applyEvaluatedPose(viewer.poseFor(viewer.current,viewer.time,viewer.currentLoop));viewer.playerState="scrubbing";viewer.syncPlaybackUI();});
      $("speed")?.addEventListener("input",e=>{viewer.speed=Number(e.target.value);$("speedLabel").textContent=`${viewer.speed.toFixed(2)}×`;});
      $("resetCamera")?.addEventListener("click",()=>viewer.camera={yaw:.76,pitch:.24,distance:7.4,target:[0,.82,0]});
    }catch(error){console.error(error);status(error.message||String(error),"error");}}
  window.addEventListener("DOMContentLoaded",boot);
})();
