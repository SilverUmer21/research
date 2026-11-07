#version 330 core
#include "common.glsl"
// Molten arteries carrying whichever energies the car holds. U.x = distance from root, U.y across.
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
vec2 cell(vec2 p){vec2 i=floor(p),f=fract(p);float d1=8.,d2=8.;
 for(int y=-1;y<=1;y++)for(int x=-1;x<=1;x++){vec2 g=vec2(x,y);vec2 o=vec2(hash2(i+g),hash2(i+g+17.3));o=.5+.42*sin(time*.6+6.28*o);
  float d=length(g+o-f);if(d<d1){d2=d1;d1=d;}else if(d<d2)d2=d;}
 return vec2(d1,d2-d1);}
void main(){
 vec3 lp=localPoint(W);float edge=dissolveEdge(lp);if(edge<0.)discard;
 float x=U.x,across=U.y,cs=sqrt(max(0.,1.-across*across));
 vec3 w=localMix(lp);
 // Magenta arrives from the heart (fillFront); stolen energies arrive through localMix.
 float filled=1.-smoothstep(fillFront-.05,fillFront+.02,x+M);
 w.x*=filled;
 float present=clamp(w.x+w.y+w.z,0.,1.);
 float head=exp(-sq((x+M-fillFront)/.07))*step(.02,fillFront)*(1.-step(3.2,fillFront));
 float hc=exp(-sq((lp.x-fronts.x)/.10))*mixW.y*step(-2.9,fronts.x)*(1.-step(2.9,fronts.x));
 float ho=exp(-sq((lp.x-fronts.y)/.10))*mixW.z*step(-2.9,fronts.y)*(1.-step(2.9,fronts.y));
 float drained=smoothstep(drainFront-.25,drainFront+.05,x);
 float flow=fract(x*.48-flowPhase+M);
 float pulse=exp(-sq((flow-.5)/.075));
 vec2 vc=cell(vec2(x*26.-flowPhase*9.,across*1.6));
 float crack=1.-smoothstep(.0,.16,vc.y);
 float churn=fbm(vec3(x*14.-flowPhase*6.,across*2.,time*.7));
 float temp=.50+.22*churn+.40*pulse+.16*boost+.08*charge;
 temp=mix(temp*.74,temp+.14,crack)*mix(.78,1.,cs)-cool*.35*(1.-pulse);
 float band=x*.9-flowPhase*.55+churn*.7+M*3.;
 vec3 hue=prism(band,w);
 vec3 col=heat(hue,temp)*(.55+.45*cs)*present*(1.-drained*.94)*mix(.03,1.,alive);
 col+=heat(MAG(),1.1)*head*2.6*cs+heat(CYA(),1.1)*hc*2.4*cs+heat(ORA(),1.1)*ho*2.4*cs;
 col+=heat(avgEnergy(mixW),.75)*edge*1.4;
 frag=vec4(col,1.);
}
