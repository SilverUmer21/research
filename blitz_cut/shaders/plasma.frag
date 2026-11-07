#version 330 core
#include "common.glsl"
// lavaKind 0 cabin heart, 1 headlamps, 2 tail lamps, 3 lava channels, 4 booster core ring.
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
void main(){
 vec3 p=localPoint(W);float edge=dissolveEdge(p);if(edge<0.)discard;
 if(lavaKind<.5){
   vec3 q=(p-vec3(-.24,1.23,0.))*6.;
   float a=atan(q.z,q.y)+time*.9;float r=length(q.yz);
   vec3 w=vec3(q.x*1.2,r*1.5,a*1.2)+vec3(-time*1.4,0.,time*.3);
   float warp=fbm(w+fbm(w*1.7+time*.4)*2.2);
   float filament=pow(1.-abs(fract(warp*3.2-time*.35)-.5)*2.,10.);
   float t=heartI*(.30+.55*warp)+filament*.55*heartI;
   vec3 hue=prism(warp*1.6+a*.16-time*.2,mixW);
   vec3 col=heat(hue,t)*(.25+1.25*heartI)+heat(hue,1.)*filament*heartI*1.4;
   frag=vec4(col+heat(avgEnergy(mixW),.75)*edge*1.4,1.);return;
 }
 vec3 q=p*15.+vec3(-flowPhase*4.,time*.6,time*.25);
 float turb=noise3(q)+.5*noise3(q*2.3+time*.5);
 float band=1.-smoothstep(.02,.1,abs(fract(p.x*3.5+p.z*8.+turb*1.8-flowPhase*1.4)-.5));
 vec3 col;
 if(lavaKind<1.5){vec3 f=lin(vec3(.80,.70,1.));col=mix(f*1.6,vec3(2.6),band*.6)*lampI*(.94+.06*sin(time*40.));}
 else if(lavaKind<2.5){vec3 f=lin(vec3(1.,.26,.06));col=mix(f*1.4,f*3.,band)*max(lampI*.8,.04);}
 else if(lavaKind<3.5){col=heat(prism(p.x+flowPhase*.3,mixW),.35+.4*turb*charge+.25*band)*charge*alive;}
 else{vec3 h=prism(time*.6+p.z,mixW);col=mix(h*.4,heat(h,1.),band*.5)*(.12+boost*1.6+flash*2.);}
 frag=vec4(col+heat(avgEnergy(mixW),.75)*edge*1.4,1.);
}
