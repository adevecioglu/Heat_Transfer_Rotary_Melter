/* Separate fluid circuit; water never enters the product domain. */
(function(root){
'use strict';
const M=root.RotaryModel;
M.fluidCircuit=function(c){const massFlow=c.flow/3600*c.waterRho;return {waterRoute:['Rotary joint alt giriş','Mil besleme kanalı','Bombeli bölüm ceketi','Silindirik gövde ceketi','Mil ayrı dönüş kanalı','Rotary joint yan çıkış'],massFlowIn:massFlow,massFlowOut:massFlow,waterToProductMassFlow:0,thermalRoute:['Ceket suyu','316 iç metal cidar','Ürün'],assumption:'Sızdırmaz metal sınırı; kaçak ve su-ürün karışımı yok. Ceket içi dağıtım yaklaşık.'};};
function drawSvg(svg,c){svg.setAttribute('viewBox','0 0 850 590');svg.innerHTML=`<title>Kapalı sıcak su devresi: mil besleme, ceket ve ayrı mil dönüşü</title><defs><marker id="feedArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#c54f35"/></marker><marker id="returnArrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto"><path d="M0,0 L6,3 L0,6" fill="#2775be"/></marker></defs>
<text x="25" y="28" font-size="19" fill="#193343">Su yolu kesit şeması · Ölçülü CAD değildir</text>
<path d="M270 70 H640 V330 Q455 510 270 330 Z" fill="#e2f0f7" stroke="#627b86" stroke-width="6"/>
<path d="M290 90 H620 V330 Q455 460 290 330 Z" fill="#fff4db" stroke="#627b86" stroke-width="9"/>
<path d="M290 240 H620 V330 Q455 460 290 330 Z" fill="#e2bd7a"/>
<path d="M290 90 H620 V330 Q455 460 290 330 Z" fill="none" stroke="#627b86" stroke-width="9"/>
<rect x="422" y="423" width="65" height="130" rx="4" fill="#d6e0e5" stroke="#627b86" stroke-width="4"/>
<line x1="456" y1="435" x2="456" y2="550" stroke="#627b86" stroke-width="5"/>
<path d="M442 553 V425 Q270 425 270 330 V70 H640" fill="none" stroke="#c54f35" stroke-width="7"/>
<path d="M640 70 V330 Q640 420 470 425 V485 H760" fill="none" stroke="#2775be" stroke-width="7"/>
<path d="M442 540 V475" fill="none" stroke="#c54f35" stroke-width="5" marker-end="url(#feedArrow)"/>
<path d="M270 240 V160" fill="none" stroke="#c54f35" stroke-width="5" marker-end="url(#feedArrow)"/>
<path d="M640 170 V250" fill="none" stroke="#2775be" stroke-width="5" marker-end="url(#returnArrow)"/>
<path d="M650 485 H740" fill="none" stroke="#2775be" stroke-width="5" marker-end="url(#returnArrow)"/>
<text x="415" y="193" text-anchor="middle" font-size="25" fill="#6e481f">ÜRÜN</text><text x="415" y="220" text-anchor="middle" font-size="16" fill="#6e481f">Su bu hacme girmez</text>
<text x="30" y="120" font-size="20" fill="#193343">Bombe + gövde ceketi</text><path d="M230 124 H263" stroke="#526875"/>
<text x="30" y="280" font-size="19" fill="#193343">316 iç cidar</text><text x="30" y="307" font-size="16" fill="#526875">Isı yalnız metalden geçer</text><path d="M225 280 H288" stroke="#526875"/>
<text x="30" y="452" font-size="19" fill="#c54f35">Ayrı mil besleme kanalı</text><path d="M260 457 L435 475" stroke="#c54f35" fill="none"/>
<text x="550" y="449" font-size="19" fill="#2775be">Ayrı mil dönüş kanalı</text><text x="550" y="519" font-size="18" fill="#2775be">Yan port: dönüş suyu</text>
<text x="322" y="580" font-size="18" fill="#c54f35">Alt giriş: sıcak su</text><text x="25" y="555" font-size="16" fill="#526875">Ürün ile su arasında kütle geçişi: 0</text>`;}
function trace(c,profile){const sl=profile.profile,zmin=sl[0].z,zmax=sl.at(-1).z,offset=c.diameter/1000*.035,sep=offset*.45;const left=sl.map(s=>[s.z,s.r+offset]),right=sl.slice().reverse().map(s=>[s.z,-s.r-offset]);const red=[[zmin-.32,sep],[zmin-.055,sep],[zmin-.055,left[0][1]],...left,[zmax+offset,left.at(-1)[1]],[zmax+offset,0]];const blue=[[zmax+offset,0],[zmax+offset,right[0][1]],...right,[zmin-.055,right.at(-1)[1]],[zmin-.055,-sep],[zmin-.23,-sep],[zmin-.23,-.14]];return {red,blue};}
function drawCanvas(canvas,result,point,spin,speed){const c=result.c,ctx=canvas.getContext('2d'),theta=c.angle*Math.PI/180,R=c.diameter/2000,L=c.length/1000,zmid=L/2,lf=point.liquidFraction,fill=result.g.chargeMass*((1-lf)/(c.rhos*c.packing)+lf/c.rhol)/result.g.volume,p=M.fillProfile(c,fill,100),sl=p.profile;
 const scale=Math.min(610/(L+2*c.headDepth/1000+2*R+.35),360/(L*Math.sin(theta)+2*R*Math.cos(theta)+.4)),cx=canvas.width*.56,cy=canvas.height*.47;
 const xy=(z,v)=>[cx+scale*((z-zmid)*Math.cos(theta)-v*Math.sin(theta)),cy-scale*((z-zmid)*Math.sin(theta)+v*Math.cos(theta))];
 ctx.clearRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#f1f6f7';ctx.fillRect(0,0,canvas.width,canvas.height);ctx.fillStyle='#193343';ctx.font='21px Segoe UI, sans-serif';ctx.fillText('AISI 316 / 2B · '+c.angle+'° · '+c.rpm+' RPM',22,32);
 function envelope(){ctx.beginPath();sl.forEach((s,i)=>{const a=xy(s.z,s.r);i?ctx.lineTo(...a):ctx.moveTo(...a);});sl.slice().reverse().forEach(s=>ctx.lineTo(...xy(s.z,-s.r)));ctx.closePath();}
 envelope();ctx.lineWidth=24;ctx.strokeStyle='#b8dbe8';ctx.stroke();ctx.lineWidth=7;ctx.strokeStyle='#627b86';ctx.stroke();ctx.fillStyle='#f9f2e5';ctx.fill();
 ctx.save();envelope();ctx.clip();const levelY=cy-scale*(p.plane-zmid*Math.sin(theta));ctx.fillStyle=lf>.5?'#a67942':'#d9b77b';ctx.fillRect(0,levelY,canvas.width,canvas.height-levelY);
 for(let i=0;i<240*(1-lf);i++){const u=(i*.61803398875)%1,v=(i*.41421356237)%1,s=sl[Math.min(sl.length-1,Math.floor(u*sl.length))],vv=-s.r+2*s.r*((v+.04*Math.sin(spin+i)+1)%1),a=xy(s.z,vv);if(a[1]<levelY+4)continue;ctx.beginPath();ctx.arc(...a,Math.max(2,Math.min(6,scale*c.particle/2000)),0,2*Math.PI);ctx.fillStyle=i%5===0?'#b17439':'#f1d8a6';ctx.fill();}ctx.restore();
 const route=trace(c,p);function strokePath(points,color){ctx.beginPath();points.forEach((s,i)=>{const a=xy(...s);i?ctx.lineTo(...a):ctx.moveTo(...a);});ctx.strokeStyle=color;ctx.lineWidth=5;ctx.stroke();}
 // Shaft is outside the sealed product envelope. The two colored passages are distinct.
 strokePath([[sl[0].z-.32,0],[sl[0].z-.045,0]],'#8da4ae');ctx.lineWidth=18;ctx.stroke();strokePath(route.red,'#c54f35');strokePath(route.blue,'#2775be');
 function arrow(points,color,fraction){let length=0;const seg=points.slice(1).map((s,i)=>{const a=xy(...points[i]),b=xy(...s),d=Math.hypot(b[0]-a[0],b[1]-a[1]);length+=d;return {a,b,d};});let at=length*fraction;for(const q of seg){if(at>q.d){at-=q.d;continue;}const t=at/Math.max(q.d,1e-9),x=q.a[0]+t*(q.b[0]-q.a[0]),y=q.a[1]+t*(q.b[1]-q.a[1]),angle=Math.atan2(q.b[1]-q.a[1],q.b[0]-q.a[0]);ctx.save();ctx.translate(x,y);ctx.rotate(angle);ctx.beginPath();ctx.moveTo(9,0);ctx.lineTo(-6,-5);ctx.lineTo(-6,5);ctx.closePath();ctx.fillStyle=color;ctx.fill();ctx.restore();break;}}
 arrow(route.red,'#c54f35',.22);arrow(route.red,'#c54f35',.65);arrow(route.blue,'#2775be',.35);arrow(route.blue,'#2775be',.85);
 // A marker on the end rim shows rotation without drawing tubes through the product.
 const zmax=sl.at(-1).z,rr=sl.at(-1).r;ctx.beginPath();for(let i=0;i<=80;i++){const a=i/80*2*Math.PI,b=xy(zmax+.018+.12*R*Math.sin(a),Math.max(rr,R*.75)*Math.cos(a));i?ctx.lineTo(...b):ctx.moveTo(...b);}ctx.strokeStyle='#839aa4';ctx.lineWidth=2;ctx.stroke();const marker=xy(zmax+.018+.12*R*Math.sin(spin),Math.max(rr,R*.75)*Math.cos(spin));ctx.beginPath();ctx.arc(...marker,6,0,2*Math.PI);ctx.fillStyle='#ad6b2c';ctx.fill();
 ctx.font='18px Segoe UI, sans-serif';ctx.fillStyle='#c54f35';ctx.fillText('Alt giriş → mil → ceket',22,canvas.height-86);ctx.fillStyle='#2775be';ctx.fillText('Ceket → ayrı mil dönüşü → yan çıkış',22,canvas.height-60);ctx.fillStyle='#526875';ctx.font='16px Segoe UI, sans-serif';ctx.fillText('Su ve ürün ayrı · Dönüş 1× / Isıl zaman '+speed+'× · Hareket şematik',22,canvas.height-22);
}
root.RotaryCircuit={drawSvg,drawCanvas,trace};if(typeof module!=='undefined')module.exports=root.RotaryCircuit;
})(typeof globalThis!=='undefined'?globalThis:this);
