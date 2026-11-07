#version 330 core
#include "common.glsl"
// Light-painting: the comet head writes, the stroke stays as neon, then the pulses run round it.
in float Tau,Vis,Cid,Age;out vec4 frag;
uniform float solid,beatP;
void main(){
 if(Age<0.||Vis<.05)discard;
 vec3 c=Cid<.5?MAG():(Cid<1.5?CYA():ORA());
 float head=exp(-Age*9.);
 float loopFade=Vis<.9?exp(-Age*2.5):1.;          // the launch loop fades, the letters stay
 float dash=pow(.5+.5*sin(Tau*55.-time*14.),6.);
 vec3 hue=toRed(mix(c,ring(Tau*.9-time*.4+Cid*.33),solid*.7),Tau*.8-time*.5);
 float I=(.55+1.7*head+.9*dash*solid+.6*beatP)*loopFade;
 frag=vec4(heat(hue,(.62+.35*head)*(1.-.22*brandRed))*I,clamp(I,0.,1.));
}
