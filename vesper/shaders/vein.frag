#version 330 core
#include "common.glsl"
// Molten body arteries. U.x = distance from the artery root (m), U.y = -1..1 across.
// M = per-artery phase offset. The energy floods outward from the cabin (fillFront),
// carries pulses (flowPhase) and drains from the tips at the end (drainFront).
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
vec2 cell(vec2 p){vec2 i=floor(p),f=fract(p);float d1=8.,d2=8.;
 for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec2 g=vec2(x,y);vec2 o=vec2(hash2(i+g),hash2(i+g+17.3));o=.5+.42*sin(time*.6+6.28*o);
  float d=length(g+o-f);if(d<d1){d2=d1;d1=d;}else if(d<d2)d2=d;}
 return vec2(d1,d2-d1);}
void main(){
 float x=U.x,across=U.y;
 float cs=sqrt(max(0.,1.-across*across));
 // Flood front: a white-hot head with a short tail, then settled lava behind it.
 float filled=1.-smoothstep(fillFront-.05,fillFront+.02,x+M);
 float head=exp(-sq((x+M-fillFront)/.07))*step(.02,fillFront)*(1.-step(3.2,fillFront));
 float drained=smoothstep(drainFront-.25,drainFront+.05,x);
 float alive=filled*(1.-drained*.92);
 // Travelling pulse, phase-integrated on the CPU so it never jumps when boost changes.
 float flow=fract(x*.48-flowPhase+M);
 float pulse=exp(-sq((flow-.5)/.075));
 // Crust plates drift with the flow; cracks between them glow hotter than the plates.
 vec2 cp=vec2(x*26.-flowPhase*9.,across*1.6);
 vec2 vc=cell(cp);
 float crack=1.-smoothstep(.0,.16,vc.y);
 float churn=fbm(vec3(x*14.-flowPhase*6.,across*2.,time*.7));
 float temp=.50+.22*churn+.40*pulse+.16*boost+.08*charge;
 temp=mix(temp*.74,temp+.14,crack);
 temp*=mix(.78,1.,cs);
 temp-=cool*.35*(1.-pulse);
 vec3 col=magma(temp)*(.55+.45*cs)*alive;
 col+=magma(1.1)*head*2.6*cs;
 frag=vec4(col,1.);
}
