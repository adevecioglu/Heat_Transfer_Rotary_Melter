/* All physical particles are rendered. This module never advances solver state.
   A depth-buffered point pass replaces tens of thousands of Canvas arc/stroke calls.
   Software fallback uses a depth/image buffer and retains all particles. */
(function(root){'use strict';
const caches=new WeakMap(),colors=new Map();
function rgb(css){if(colors.has(css))return colors.get(css);let a;if(css[0]==='#'){a=[1,3,5].map(i=>parseInt(css.slice(i,i+2),16)/255);}else a=css.match(/[\d.]+/g).slice(0,3).map(x=>Number(x)/255);colors.set(css,a);return a;}
function shader(gl,type,code){const s=gl.createShader(type);gl.shaderSource(s,code);gl.compileShader(s);if(!gl.getShaderParameter(s,gl.COMPILE_STATUS))throw Error(gl.getShaderInfoLog(s));return s;}
function create(canvas){
 const layer=document.createElement('canvas'),q={layer,mode:'sprites',buffer:null,data:null,version:null,sprites:new Map(),order:null,orderKey:null};
 try{const gl=layer.getContext('webgl',{alpha:true,depth:true,antialias:false,preserveDrawingBuffer:true,premultipliedAlpha:true});if(gl){const p=gl.createProgram();gl.attachShader(p,shader(gl,gl.VERTEX_SHADER,'attribute vec4 a_position; attribute vec4 a_color; uniform vec2 u_size; varying vec4 v_color; varying float v_size; void main(){gl_Position=vec4(a_position.x/u_size.x*2.0-1.0,1.0-a_position.y/u_size.y*2.0,a_position.z,1.0);gl_PointSize=a_position.w;v_color=a_color;v_size=a_position.w;}'));gl.attachShader(p,shader(gl,gl.FRAGMENT_SHADER,'precision mediump float; varying vec4 v_color; varying float v_size; void main(){float d=length(gl_PointCoord*2.0-1.0);if(d>1.0)discard;float ring=max(0.1,2.0/max(1.0,v_size));vec3 edge=v_color.a>0.5?vec3(0.663,0.310,0.082):vec3(0.294,0.216,0.125);vec3 c=d>1.0-ring?edge:v_color.rgb;gl_FragColor=vec4(c,1.0);}'));gl.linkProgram(p);if(!gl.getProgramParameter(p,gl.LINK_STATUS))throw Error(gl.getProgramInfoLog(p));gl.useProgram(p);q.gl=gl;q.program=p;q.buffer=gl.createBuffer();q.position=gl.getAttribLocation(p,'a_position');q.color=gl.getAttribLocation(p,'a_color');q.size=gl.getUniformLocation(p,'u_size');q.pointRange=gl.getParameter(gl.ALIASED_POINT_SIZE_RANGE);q.mode='webgl';layer.addEventListener('webglcontextlost',e=>{e.preventDefault();q.mode='sprites';q.version=null;});}}
 catch(error){q.reason=String(error);}
 caches.set(canvas,q);return q;
}
function draw(canvas,s,options,xy,scale){
 const q=caches.get(canvas)||create(canvas),ctx=canvas.getContext('2d'),r=s.radius,thermal=options.thermal,pr=thermal?r*scale:Math.max(2,r*scale),trackedStep=Math.max(1,Math.floor(s.count/12));
 if(!(pr>0)||s.liquid>=1){q.drawnCount=0;return q.mode;}
 const pos0=xy(0,0,0),px=xy(1,0,0),py=xy(0,1,0),pz=xy(0,0,1),matrix=[pos0[0],pos0[1],px[0]-pos0[0],px[1]-pos0[1],py[0]-pos0[0],py[1]-pos0[1],pz[0]-pos0[0],pz[1]-pos0[1]];
 const color=thermal?root.RotaryView.color(thermal.product,Math.min(s.c.initial,s.c.solidus),Math.max(s.c.target,s.c.liquidus)):'';
 const key=[s.count,s.seconds,s._renderRevision||0,s.liquid,r,canvas.width,canvas.height,options.velocity?1:0,color,...matrix].join(':');
 if(q.system!==s||q.version!==key){
  if(q.system!==s)q.orderKey=null;q.system=s;q.version=key;q.drawnCount=s.count;
  if(q.layer.width!==canvas.width||q.layer.height!==canvas.height){q.layer.width=canvas.width;q.layer.height=canvas.height;}
  const gl=q.gl;
  if(q.mode==='webgl'&&pr*2>=q.pointRange[0]&&pr*2<=q.pointRange[1]&&!gl.isContextLost()){
   if(!q.data||q.data.length!==s.count*8)q.data=new Float32Array(s.count*8);
   const base=thermal?rgb(color):null;let i=0;
   for(const p of s.particles){const tracked=p.id%trackedStep===0,c=base||rgb(options.velocity?(Math.hypot(p.vx,p.vy,p.vz)>.3?'#d8984c':'#76b8a5'):(tracked?'#e9ad35':'#d8b37b'));q.data[i++]=matrix[0]+p.x*matrix[2]+p.y*matrix[4]+p.z*matrix[6];q.data[i++]=matrix[1]+p.x*matrix[3]+p.y*matrix[5]+p.z*matrix[7];q.data[i++]=-p.x/(s.R*1.01);q.data[i++]=pr*2;q.data[i++]=c[0];q.data[i++]=c[1];q.data[i++]=c[2];q.data[i++]=tracked?1:0;}
   gl.viewport(0,0,canvas.width,canvas.height);gl.clearColor(0,0,0,0);gl.clearDepth(1);gl.clear(gl.COLOR_BUFFER_BIT|gl.DEPTH_BUFFER_BIT);gl.enable(gl.DEPTH_TEST);gl.depthFunc(gl.LEQUAL);gl.useProgram(q.program);gl.uniform2f(q.size,canvas.width,canvas.height);gl.bindBuffer(gl.ARRAY_BUFFER,q.buffer);gl.bufferData(gl.ARRAY_BUFFER,q.data,gl.DYNAMIC_DRAW);gl.enableVertexAttribArray(q.position);gl.vertexAttribPointer(q.position,4,gl.FLOAT,false,32,0);gl.enableVertexAttribArray(q.color);gl.vertexAttribPointer(q.color,4,gl.FLOAT,false,32,16);gl.drawArrays(gl.POINTS,0,s.count);q.lastBackend='webgl';
  }else{
   // Rasterize every circle into a reusable depth/image buffer. This avoids
   // tens of thousands of Canvas draw calls even when WebGL is unavailable.
   if(!q.softLayer)q.softLayer=document.createElement('canvas');const layer=q.softLayer,W=canvas.width,H=canvas.height;
   if(layer.width!==W||layer.height!==H){layer.width=W;layer.height=H;q.image=null;}
   const c=layer.getContext('2d');if(!q.image){q.image=c.createImageData(W,H);q.depth=new Float32Array(W*H);}const image=q.image.data,depth=q.depth;image.fill(0);depth.fill(Infinity);
   const base=thermal?rgb(color):null,pr2=pr*pr,inner2=Math.max(0,pr-1)**2;
   for(const p of s.particles){const tracked=p.id%trackedStep===0,col=base||rgb(options.velocity?(Math.hypot(p.vx,p.vy,p.vz)>.3?'#d8984c':'#76b8a5'):(tracked?'#e9ad35':'#d8b37b')),red=Math.round(col[0]*255),green=Math.round(col[1]*255),blue=Math.round(col[2]*255),x=matrix[0]+p.x*matrix[2]+p.y*matrix[4]+p.z*matrix[6],y=matrix[1]+p.x*matrix[3]+p.y*matrix[5]+p.z*matrix[7],z=-p.x;
    const x0=Math.max(0,Math.ceil(x-pr-.5)),x1=Math.min(W-1,Math.floor(x+pr-.5)),y0=Math.max(0,Math.ceil(y-pr-.5)),y1=Math.min(H-1,Math.floor(y+pr-.5));
    for(let yy=y0;yy<=y1;yy++){const dy=yy+.5-y,dy2=dy*dy;for(let xx=x0;xx<=x1;xx++){const dx=xx+.5-x,d2=dx*dx+dy2,index=yy*W+xx;if(d2>pr2||z>depth[index])continue;depth[index]=z;const i=index*4,border=d2>inner2;image[i]=border?(tracked?169:75):red;image[i+1]=border?(tracked?79:55):green;image[i+2]=border?(tracked?21:32):blue;image[i+3]=255;}}
   }c.putImageData(q.image,0,0);q.lastBackend='raster';
  }
 }
 ctx.drawImage(q.lastBackend==='webgl'?q.layer:q.softLayer,0,0);return q.lastBackend;
}
root.ParticleRenderer={draw,info:canvas=>{const q=caches.get(canvas);return q?{backend:q.lastBackend,count:q.drawnCount,capacity:q.data?.length/8||0}:null;},forceFallback:canvas=>{const q=caches.get(canvas)||create(canvas);q.mode='sprites';q.version=null;}};
})(typeof globalThis!=='undefined'?globalThis:this);
