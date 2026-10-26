(function(root){
'use strict';
const viewCache21=new WeakMap();
function geometry21(canvas,s){
 const c=s.c,W=canvas.width,H=canvas.height,L=s.L,theta=c.angle*Math.PI/180,key=[W,H,c.angle,c.diameter,c.length,c.headDepth,c.heads].join(':');let g=viewCache21.get(canvas);if(g?.key===key)return g;
 const profile=root.RotaryModel.fillProfile(c,.5,60).profile,z0=profile[0].z,z1=profile.at(-1).z,camera=.34,proj=(x,y,z)=>[((z-L/2)*Math.cos(theta)-y*Math.sin(theta))*Math.cos(camera)+x*Math.sin(camera),-(z-L/2)*Math.sin(theta)-y*Math.cos(theta)];
 const points=profile.flatMap(p=>Array.from({length:24},(_,i)=>proj(p.r*Math.sin(i*2*Math.PI/24),p.r*Math.cos(i*2*Math.PI/24),p.z)));points.push(proj(0,0,z0-.37));const minx=Math.min(...points.map(p=>p[0])),maxx=Math.max(...points.map(p=>p[0])),miny=Math.min(...points.map(p=>p[1])),maxy=Math.max(...points.map(p=>p[1])),scale=Math.min((W-245)/(maxx-minx),(H-170)/(maxy-miny)),ox=210+(W-245)/2-scale*(minx+maxx)/2,oy=68+(H-170)/2-scale*(miny+maxy)/2,xy=(x,y,z)=>{const p=proj(x,y,z);return [ox+scale*p[0],oy+scale*p[1]];};
 const boundary=profile.flatMap(p=>Array.from({length:24},(_,i)=>xy(p.r*Math.sin(i*2*Math.PI/24),p.r*Math.cos(i*2*Math.PI/24),p.z))).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);const cross=(a,b,c)=>(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);let lower=[],upper=[];for(const p of boundary){while(lower.length>=2&&cross(lower.at(-2),lower.at(-1),p)<=0)lower.pop();lower.push(p);}for(const p of boundary.slice().reverse()){while(upper.length>=2&&cross(upper.at(-2),upper.at(-1),p)<=0)upper.pop();upper.push(p);}const outline=lower.slice(0,-1).concat(upper.slice(0,-1));g={key,profile,z0,z1,scale,ox,oy,xy,outline};viewCache21.set(canvas,g);return g;
}

function materialPoint(r,offset,physicalPhase){const a=offset-physicalPhase;return [r*Math.sin(a),r*Math.cos(a)];}
function draw(canvas,s,options={}){
 const ctx=canvas.getContext('2d'),tr=(a,b)=>options.lang==='en'?b:a,W=canvas.width,H=canvas.height,c=s.c,R=s.R,L=s.L,theta=c.angle*Math.PI/180,cut=options.cutaway!==false,spin=-s.angle,lf=s.liquid;
 const {profile,z0,z1,scale,ox,oy,xy,outline}=geometry21(canvas,s);
 ctx.fillStyle='#eff5f7';ctx.fillRect(0,0,W,H);
 ctx.fillStyle='#183747';ctx.font='bold 22px Segoe UI, sans-serif';ctx.fillText(options.thermal?tr('Analiz boyunca ısınma ve erime','Heating and melting over the analysis'):options.bodyOnly?tr('Gövde dönüşü · ürün hesabı ayrı','Vessel rotation · separate product solve'):tr('Dönen kap ve ürün hareketi','Rotating vessel and product motion'),20,31);
 ctx.fillStyle='#55717e';ctx.font='15px Segoe UI, sans-serif';ctx.fillText(c.angle.toFixed(0)+'° · '+c.rpm+' RPM · '+(c.rotationDirection===-1?'CW':'CCW')+' · '+(options.thermal?(s.seconds/60).toFixed(2)+' min':s.seconds.toFixed(1)+' s')+' · '+tr('Katı/sıvı ','Solid/liquid ')+(100*(1-s.liquid)).toFixed(0)+' / '+(100*s.liquid).toFixed(0)+'%',20,55);
 function line(pts,col,width=1){ctx.beginPath();pts.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.strokeStyle=col;ctx.lineWidth=width;ctx.stroke();}
 function rim(z,r,color,width=2){line(Array.from({length:65},(_,i)=>{const a=i*2*Math.PI/64;return xy(r*Math.sin(a),r*Math.cos(a),z);}),color,width);}
 function hull(){ctx.beginPath();outline.forEach((p,i)=>i?ctx.lineTo(...p):ctx.moveTo(...p));ctx.closePath();}
 // Stationary support and rotary joint. The rotating shaft ends before the stationary side port.
 const j=xy(0,0,z0-.28),end=xy(0,0,z0),lower=xy(0,0,z0-.38);line([lower,end],'#90a5af',17);line([lower,end],'#d3dee3',9);
 for(let k=0;k<4;k++){const a=spin+k*Math.PI/2;line([xy(.025*Math.sin(a),.025*Math.cos(a),z0-.26),xy(.025*Math.sin(a),.025*Math.cos(a),z0-.01)],Math.sin(a)>0?'#507987':'#a7bdc7',2);}
 ctx.fillStyle='#657f8d';ctx.fillRect(j[0]-13,j[1]-12,26,24);ctx.strokeStyle='#e2b25a';ctx.lineWidth=3;ctx.strokeRect(j[0]-13,j[1]-12,26,24);
 const inlet=xy(0,0,z0-.4),back=xy(0,0,z0-.29);line([inlet,back],'#c45136',4);line([j,[j[0]+42,j[1]+23],[j[0]+70,j[1]+23]],'#287bb6',4);
 hull();const steel=ctx.createLinearGradient(ox-100,oy-160,ox+120,oy+140);steel.addColorStop(0,'#bed0d8');steel.addColorStop(.45,'#f7fbfd');steel.addColorStop(1,'#91aab7');ctx.fillStyle=steel;ctx.fill();ctx.strokeStyle='#6d8998';ctx.lineWidth=5;ctx.stroke();
 // Back half: longitudinal material seams rotate at omega*t; axis and tilt stay fixed.
 for(let k=0;k<12;k++){const a=spin+k*2*Math.PI/12;if(Math.sin(a)>0)continue;line(profile.map(p=>xy(p.r*Math.sin(a),p.r*Math.cos(a),p.z)),'rgba(68,105,124,.22)',1.3);}
 if(cut){hull();ctx.save();ctx.clip();ctx.fillStyle='rgba(250,244,227,.78)';ctx.fillRect(0,0,W,H);
  let liquidLevel=null;if(lf>0){let plane=s.liquidPlane;if(!Number.isFinite(plane))plane=root.RotaryMotion.liquidPlane(s);liquidLevel=oy-scale*(plane-L/2*Math.sin(theta));}
  if(lf>0){ctx.fillStyle='rgba(118,71,25,.40)';ctx.fillRect(0,liquidLevel,W,H-liquidLevel);}
  const r=s.radius,tracked=p=>p.id%Math.max(1,Math.floor(s.count/12))===0;
  if(options.thermal?r>0:r>s.baseRadius*.035)root.ParticleRenderer.draw(canvas,s,options,xy,scale);
  if(options.trails&&lf<1){for(const p of s.particles.filter(tracked)){if(p.path.length>1)line(p.path.map(v=>xy(...v)),'rgba(198,83,40,.7)',1.5);}}
  if(lf>0){ctx.fillStyle='rgba(119,66,21,.22)';ctx.fillRect(0,liquidLevel,W,H-liquidLevel);ctx.strokeStyle='#c98124';ctx.lineWidth=1.5;ctx.beginPath();ctx.moveTo(0,liquidLevel);ctx.lineTo(W,liquidLevel);ctx.stroke();}
  // Fully liquid: prescribed rotating/slipping tracers explicitly distinguished from particle contacts.
  if(lf>.001&&!options.thermal){const plane=s.liquidPlane??root.RotaryMotion.liquidPlane(s);for(let k=0;k<40;k++){const a=k*2.39996+spin*s.settings.liquidSlip,rad=R*(.2+.65*((k*.618)%1)),z=Math.max(z0*.5,Math.min(L,(k*.137%1)*L)),x=rad*Math.sin(a),y=rad*Math.cos(a);if(y*Math.cos(theta)+z*Math.sin(theta)>plane)continue;const q=xy(x,y,z);ctx.fillStyle='#f6cc87';ctx.beginPath();ctx.arc(...q,2.8,0,2*Math.PI);ctx.fill();}}
  ctx.restore();
 }
 // Visible front rim and rotating seams, including an indexed band so symmetry does not hide rotation.
 for(let k=0;k<12;k++){const a=spin+k*2*Math.PI/12;if(Math.sin(a)<0)continue;const col=k%3===0?'rgba(35,106,129,.85)':'rgba(68,105,124,.25)';line(profile.map(p=>xy(p.r*Math.sin(a),p.r*Math.cos(a),p.z)),col,k%3===0?2.5:1);}
 for(const z of [0,L])rim(z,R,'#678693',2.6);
 for(let k=0;k<24;k++){const a=spin+k*2*Math.PI/24,p1=xy(R*Math.sin(a),R*Math.cos(a),L-.03),p2=xy(R*Math.sin(a),R*Math.cos(a),L+.006);line([p1,p2],k%6===0?'#b77b25':'#648797',k%6===0?5:2);}
 for(const [offset,color]of [[0,'#e89420'],[Math.PI,'#287eb3']]){const a=spin+offset;line(profile.filter(p=>p.z>=0).map(p=>xy(p.r*1.012*Math.sin(a),p.r*1.012*Math.cos(a),p.z)),color,4);}
 const indexed=materialPoint(R,0,s.angle),mark=xy(indexed[0],indexed[1],L);ctx.beginPath();ctx.arc(...mark,7,0,2*Math.PI);ctx.fillStyle='#e49529';ctx.fill();
 const pivot=xy(0,0,z0-.03);ctx.setLineDash([5,4]);line([pivot,[pivot[0]+100,pivot[1]]],'#8c9fac',1);ctx.setLineDash([]);ctx.beginPath();ctx.arc(...pivot,42,0,-theta,true);ctx.strokeStyle='#9c752e';ctx.lineWidth=2;ctx.stroke();ctx.font='bold 14px Segoe UI, sans-serif';ctx.fillStyle='#785b27';ctx.fillText(c.angle.toFixed(0)+'°',pivot[0]+48*Math.cos(theta/2),pivot[1]-48*Math.sin(theta/2));
 ctx.save();ctx.translate(options.thermal?225:182,options.thermal?420:315);ctx.strokeStyle='#416f96';ctx.lineWidth=2;ctx.beginPath();ctx.moveTo(0,0);ctx.lineTo(0,60);ctx.lineTo(-5,50);ctx.moveTo(0,60);ctx.lineTo(5,50);ctx.stroke();ctx.font='14px Segoe UI';ctx.fillStyle='#416f96';ctx.fillText('g',9,35);ctx.restore();
 // Live motion telemetry, left of the vessel.
 const stat=options.thermal||s.native?{count:s.count,proxyDiameterMm:s.baseRadius*2000,meanSpeed:s.native?.meanSpeed||0,contacts:s.contacts}:(s._viewStats21||(s._viewStats21=root.RotaryMotion.stats(s)));ctx.font='bold 16px Segoe UI, sans-serif';ctx.fillStyle='#183747';ctx.fillText(options.thermal?tr('Hesaplanan ısıl durum','Computed thermal state'):tr('Hareket modeli','Motion model'),20,98);ctx.font='14px Segoe UI, sans-serif';ctx.fillStyle='#55717e';
 (options.thermal?[tr('En soğuk merkez: ','Coldest center: ')+options.thermal.coreProduct.toFixed(2)+' °C',tr('Yakın yatak: ','Near-wall bed: ')+options.thermal.nearProduct.toFixed(2)+' °C',tr('Katı: ','Solid: ')+(s.c.mass*(1-lf)).toFixed(2)+' kg',tr('Sıvı: ','Liquid: ')+(s.c.mass*lf).toFixed(2)+' kg',tr('Eşdeğer çap: ','Equivalent diameter: ')+(s.radius*2000).toFixed(2)+' mm','Tin: '+options.thermal.waterIn.toFixed(2)+' °C','Tout: '+options.thermal.waterOut.toFixed(2)+' °C',tr('Ürüne: ','To product: ')+options.thermal.productKW.toFixed(2)+' kW',tr('Isı kaybı: ','Heat loss: ')+options.thermal.lossKW.toFixed(2)+' kW']:[tr('Yerçekimi + temas','Gravity + contacts'),tr('Duvar sürtünmesi','Wall friction')+' μ='+s.settings.muWall,stat.count+tr(' gerçek çaplı küre',' physical-diameter spheres'),tr('Ortalama hız: ','Mean speed: ')+stat.meanSpeed.toFixed(3)+' m/s',tr('Temas çifti: ','Contact pairs: ')+stat.contacts,tr('Dönüş fazı: ','Rotation phase: ')+(s.angle*180/Math.PI).toFixed(0)+'°',tr('Erime: ','Melt: ')+(s.liquid*100).toFixed(0)+'%',tr('Granül ort. devir: ','Granule mean orbit: ')+(s.native?.meanOrbitalRPM??0).toFixed(2)+' RPM']).forEach((t,i)=>ctx.fillText(t,20,124+i*25));
 ctx.font='13px Segoe UI, sans-serif';ctx.fillStyle='#8a602b';ctx.fillText((options.thermal?tr('Başlangıç granülü: ','Initial granule: '):tr('Fiziksel granül çapı: ','Physical granule diameter: '))+stat.proxyDiameterMm.toFixed(1)+' mm',20,H-70);ctx.fillText(tr('Sıvı: ','Liquid: ')+(s.g.chargeMass*lf/c.rhol*1000).toFixed(2)+' L · '+tr('Katı yer değiştirme hacmi seviyeye dahildir.','Level includes displaced solid volume.'),20,H-46);ctx.fillStyle='#55717e';ctx.fillText(options.thermal?tr('Isıl sonuçların eşdeğer hacimli gösterimi · geometrik çökme; tüm süre için mekanik/CFD çözümü değil.','Volume-equivalent thermal replay · geometric settlement; not a full-duration mechanics/CFD solution.'):tr('Su yalnız mil/ceket içindedir. Sıvı izleri varsayımsal akıştır; CFD değildir.','Water stays in shaft/jacket. Liquid tracers use prescribed flow; not CFD.'),20,H-21);
 return stat;
}
root.RotaryMotionView={draw,materialPoint};
})(typeof globalThis!=='undefined'?globalThis:this);
