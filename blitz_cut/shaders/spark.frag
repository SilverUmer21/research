#version 330 core
#include "common.glsl"
in vec2 U;in float A;in float T;in float S;out vec4 frag;
void main(){float r=length(U);if(r>1.)discard;frag=vec4(heat(prism(S*3.,mixW),.45+.6*T)*1.8,sq(1.-r)*A);}
