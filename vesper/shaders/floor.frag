#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
uniform sampler2D shadowmap,reflectionMap;
uniform vec4 rings[4];      // xyz = world centre, w = age (s); negative age = off
uniform float boardSpacing;
// Distance (grid units) to the Alquerque lines of a 5x5 board: orthogonals plus
// the diagonals through the strong points (i-j and i+j even, |.|<=2).
float alquerque(vec2 g){
 vec2 a=abs(g-round(g));float d=min(a.x,a.y);
 float s1=g.x-g.y,s2=g.x+g.y;
 float e1=clamp(2.*round(s1*.5),-2.,2.),e2=clamp(2.*round(s2*.5),-2.,2.);
 d=min(d,abs(s1-e1)*.7071);d=min(d,abs(s2-e2)*.7071);
 float outside=max(abs(g.x),abs(g.y))-2.;
 return outside>0.?max(d,outside):d;
}
void main(){
 vec3 v=normalize(eye-W);vec3 s=L.xyz/L.w*.5+.5;float sh=0.;
 for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)sh+=step(texture(shadowmap,s.xy+vec2(x,y)*2.8/3072.).r,s.z-.0006);sh/=9.;
 vec2 P=vec2(W.x+travel,W.z);
 // Wet patches: sharper, stronger reflections where the floor is wet.
 float wet=smoothstep(.45,.7,fbm(vec3(P*.22,1.3)));
 vec2 uv=gl_FragCoord.xy/resolution;vec3 reflected=vec3(0.);
 float blur=mix(.0030,.0008,wet);
 vec2 ripple=vec2(noise3(vec3(P*3.,time*.5)),noise3(vec3(P*3.+9.,time*.5)))-.5;
 for(int k=0;k<6;k++){float a=float(k)*1.0472;reflected+=texture(reflectionMap,uv+vec2(cos(a),sin(a))*blur+ripple*.004*wet).rgb/6.;}
 float fr=pow(1.-abs(v.y),4.);
 vec3 base=lin(vec3(.030,.024,.050));
 // Panel seams stream past with travel: the only cue of speed on a mirror floor.
 // Seams across the direction of travel are box-filtered over the shutter (analytic motion blur).
 float blurLen=speed*.5/30.;
 float dx=abs(fract(P.x/3.2)-.5)*3.2,dz=abs(fract(P.y/2.6)-.5)*2.6;
 float wx=.012+blurLen;float seamX=(1.-smoothstep(wx*.5,wx*.5+.006,dx))*(.012/wx);
 float seamZ=1.-smoothstep(.006,.012,dz);
 float seam=max(seamX,seamZ);
 base*=1.-seam*.55;
 vec3 col=base*(.85-sh*.6);
 col+=lin(vec3(.55,.12,.75))*seam*(.010+.035*charge)*(1.-board);
 col+=reflected*(.10+fr*.20+wet*.22);
 // Lane dashes at the edges, glowing faintly magenta, smeared by speed.
 float lane=exp(-sq((abs(W.z)-3.1)/.05));
 float dash=smoothstep(.0,.15,sin(P.x*1.3))*(1.-speed*.02)+speed*.02;
 col+=energyColor()*lane*dash*(.05+.10*charge)*(1.-board);
 // Light pools: the heart through the glass, headlamps ahead, plumes behind.
 vec2 c=W.xz;
 col+=energyColor()*exp(-length(c-vec2(-.24,0.))*2.2)*.05*heartI;
 col+=lin(vec3(.70,.55,1.))*lampI*exp(-sq((c.x-4.2)/2.2)-sq(c.y/1.2))*.10;
 for(int i=0;i<2;i++){
   float zz=(float(i)*2.-1.)*.53;float len=.2+boost*3.4;
   vec2 q=c-vec2(-2.9-len*.45,zz);float p=exp(-q.x*q.x/(len*len*.25+.2)-q.y*q.y*4.);
   col+=boosterColor()*p*(boost*.22+flash*.6);
 }
 // Ignition shock rings expand from each nozzle on every pop.
 for(int i=0;i<4;i++){
   if(rings[i].w<0.)continue;
   float age=rings[i].w;float R=age*7.;float d=abs(length(c-rings[i].xz)-R);
   col+=magma(.9)*exp(-d*d*40.)*exp(-age*3.2)*.55;
 }
 // The board: Barah Goti's lattice lights up in a wave from under the car.
 if(board>0.){
   vec2 g=c/boardSpacing;float dl=alquerque(g)*boardSpacing;
   float rad=length(c);float front=board*16.;
   float reached=1.-smoothstep(front-1.2,front,rad);
   float core=exp(-dl*dl*900.),glow=exp(-dl*dl*35.);
   float pulseRun=pow(.5+.5*sin(rad*2.2-time*5.),8.);
   float edge=exp(-sq((rad-front)/.6));
   vec3 lc=magma(.55+.35*pulseRun+.3*edge);
   col+=lc*(core*.9+glow*.10)*reached;
   vec2 node=abs(g-round(g))*boardSpacing;float nd=length(node);
   col+=magma(.8)*exp(-nd*nd*30.)*.6*reached*step(max(abs(round(g.x)),abs(round(g.y))),2.);
   col*=1.;
 }
 col=mix(col,sky(uv),smoothstep(10.,48.,length(eye-W))*.92);frag=vec4(col,1.);
}
