#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
uniform sampler2D shadowmap,reflectionMap;
uniform float boardSpacing,ringN,ringFlash,vBoost;
uniform vec3 vesperW;
uniform vec4 cars[3];        // x, z, alive, kind (0 orange, 1 cyan, 2 vesper)
uniform vec4 streamA[4];     // x0 z0 x1 z1
uniform vec4 streamB[4];     // rgb, head 0..1
uniform vec4 streamC[4];     // tail 0..1, intensity, width, hue mode (1 = prism)
uniform vec3 flood;          // x, z, radius
uniform vec4 rings[4];       // x, ., z, age (<0 off)
uniform vec4 nozzle;         // vesper nozzle centre xz, rear direction xz
uniform float travel,speed,beatPulse,ringOn;
float alquerque(vec2 g){
 g.x=mod(g.x+2.,4.)-2.;            // the 5x5 board repeats endlessly along the highway
 vec2 a=abs(g-round(g));float d=min(a.x,a.y);
 float s1=g.x-g.y,s2=g.x+g.y;
 float e1=clamp(2.*round(s1*.5),-2.,2.),e2=clamp(2.*round(s2*.5),-2.,2.);
 d=min(d,abs(s1-e1)*.7071);d=min(d,abs(s2-e2)*.7071);
 float outside=max(abs(g.x),abs(g.y))-2.;
 return outside>0.?max(d,outside):d;
}
vec3 carColor(vec4 c){return c.w<.5?ORA():(c.w<1.5?CYA():avgEnergy(vesperW));}
void main(){
 vec3 v=normalize(eye-W);vec3 s=L.xyz/L.w*.5+.5;float sh=0.;
 for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)sh+=step(texture(shadowmap,s.xy+vec2(x,y)*2.8/3072.).r,s.z-.0008);sh/=9.;
 vec2 P=W.xz;vec2 B=P+vec2(travel,0.);
 float wet=smoothstep(.45,.7,fbm(vec3(B*.22,1.3)));
 vec2 uv=gl_FragCoord.xy/resolution;vec3 reflected=vec3(0.);
 float blur=mix(.0030,.0008,wet)*(1.+3.*smoothstep(15.,19.,P.x)*logoI);
 vec2 ripple=vec2(noise3(vec3(B*3.,time*.5)),noise3(vec3(B*3.+9.,time*.5)))-.5;
 for(int k=0;k<6;k++){float a=float(k)*1.0472;reflected+=texture(reflectionMap,uv+vec2(cos(a),sin(a))*blur+ripple*.004*wet).rgb/6.;}
 float fr=pow(1.-abs(v.y),4.);
 vec3 base=lin(vec3(.028,.022,.046));
 vec3 col=base*(.85-sh*.6)+reflected*(.10+fr*.20+wet*.22);
 // --- the board: each car tints the lines around it with the energy it holds
 vec2 g=B/boardSpacing;float dl=alquerque(g)*boardSpacing;
 // Lines across the direction of travel are box-filtered over the shutter (analytic motion blur).
 float blurLen=speed*.5/30.;float wcore=.038+blurLen;
 vec2 gx=vec2(mod(g.x+2.,4.)-2.,g.y);float across=abs(gx.x-round(gx.x))*boardSpacing;
 float lineCore=exp(-dl*dl*700.);
 if(across<=dl+.001&&blurLen>.02)lineCore=exp(-sq(max(0.,across-blurLen*.5))*700.)*(.038/wcore);
 float lineGlow=exp(-dl*dl*25.);
 vec3 zone=vec3(0.);float zw=0.;
 for(int i=0;i<3;i++){float d=length(P-cars[i].xy);float wgt=exp(-d*d/40.)*cars[i].z;zone+=carColor(cars[i])*wgt;zw+=wgt;}
 vec3 lc=zw>.001?zone/zw:lin(vec3(.3,.2,.5));
 float lb=.10+.55*clamp(zw,0.,1.);
 float pulseRun=pow(.5+.5*sin(length(B)*1.4-time*3.),6.);
 vec3 latt=heat(lc,.42+.25*pulseRun)*lb;
 // Owned: after the capture, the prism floods the board from the landing point.
 float fd=length(P-flood.xy);
 float owned=1.-smoothstep(flood.z-1.5,flood.z,fd);
 float floodEdge=exp(-sq((fd-flood.z)/1.2))*step(.1,flood.z);
 latt=mix(latt,heat(ring(fd*.05+atan(P.y-flood.y,P.x-flood.x)*.16-time*.35),.62+.3*pulseRun),owned);
 latt+=heat(vec3(1.),.9)*floodEdge*.6;
 col+=latt*(lineCore*.9+lineGlow*.10)*(1.+beatPulse*1.6);
 vec2 node=abs(gx-round(gx))*boardSpacing;float nd=length(node);
 float onBoard=step(abs(round(g.y)),2.);
 col+=heat(mix(lc,ring(fd*.05-time*.3),owned),.75)*exp(-nd*nd*6.)*.35*onBoard*(lb+owned);
 // --- the Switch ring: 12 notches around the board fill up, then flash
 float R=boardSpacing*2.75;float rr=length(P);float ang=atan(P.y,P.x);
 float seg=fract((ang/(2.*PI))*12.+.5);float idx=floor(mod((ang/(2.*PI))*12.+12.5,12.));
 float notch=exp(-sq((rr-R)/.16))*smoothstep(.06,.12,seg)*smoothstep(.06,.12,1.-seg);
 float lit=step(idx+.5,ringN);
 col+=mix(lin(vec3(.25,.18,.4))*.12,heat(MAG(),.8),lit)*notch*ringOn;
 col+=heat(ring(ang/(2.*PI)-time*.4),.8)*exp(-sq((rr-R)/.5))*ringFlash*1.1*ringOn;
 // --- energy streams racing along board lines
 for(int i=0;i<4;i++){
   if(streamC[i].y<=0.)continue;
   vec2 a=streamA[i].xy,b=streamA[i].zw,ab=b-a;float len=length(ab);
   float t=clamp(dot(P-a,ab)/(len*len),0.,1.);float d=length(P-a-ab*t);
   float on=step(streamC[i].x,t)*step(t,streamB[i].w);
   float w=streamC[i].z;
   float dash=pow(.5+.5*sin(t*len*2.6-time*16.),3.);
   float headGlow=exp(-sq((t-streamB[i].w)*len/.5));
   vec3 sc=streamC[i].w>.5?ring(t*len*.08-time*.9):streamB[i].rgb;
   float core=exp(-d*d/(w*w));
   col+=heat(sc,.6+.35*dash+.4*headGlow)*(core*(.5+.8*dash)+exp(-d*d/(w*w*30.))*.15)*on*streamC[i].y;
   col+=heat(sc,1.1)*headGlow*exp(-d*d*2.)*on*streamC[i].y*1.5;
 }
 // --- pools of light under each live car, the plumes and the logo
 for(int i=0;i<3;i++){float d=length(P-cars[i].xy);col+=carColor(cars[i])*exp(-d*d*.35)*.05*cars[i].z;}
 for(int k=0;k<2;k++){
   vec2 side=vec2(-nozzle.w,nozzle.z)*((float(k)*2.-1.)*.53);float len=.2+vBoost*3.6;
   vec2 q=P-(nozzle.xy+side+nozzle.zw*len*.45);
   vec2 qa=vec2(dot(q,nozzle.zw),dot(q,vec2(-nozzle.w,nozzle.z)));
   col+=prism(time*.7+float(k)*.5,vesperW)*exp(-qa.x*qa.x/(len*len*.25+.2)-qa.y*qa.y*4.)*(vBoost*.22+flash*.5);
 }
 col+=ring(P.y*.05+time*.15)*exp(-sq((P.x-21.)/2.2)-pow(abs(P.y)/7.5,8.))*logoI*.16;
 for(int i=0;i<4;i++){
   if(rings[i].w<0.)continue;
   float age=rings[i].w;float d=abs(length(P-rings[i].xz)-age*7.);
   col+=heat(ring(atan(P.y-rings[i].z,P.x-rings[i].x)/(2.*PI)+age),.9)*exp(-d*d*40.)*exp(-age*3.)*.6;
 }
 col=mix(col,sky(uv),smoothstep(16.,60.,length(eye-W))*.92);
 frag=vec4(col,1.);
}
