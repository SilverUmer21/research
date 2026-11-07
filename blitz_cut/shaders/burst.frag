#version 330 core
#include "common.glsl"
in vec2 U;in float A;in float T;out vec4 frag;
void main(){float r=length(U);if(r>1.)discard;frag=vec4(heat(avgEnergy(mixW),.42+.38*T)*1.5,pow(1.-r,1.6)*A*.8);}
