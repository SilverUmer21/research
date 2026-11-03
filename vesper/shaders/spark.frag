#version 330 core
#include "common.glsl"
in vec2 U;in float A;in float T;out vec4 frag;
void main(){float r=length(U);if(r>1.)discard;frag=vec4(magma(.45+.6*T)*1.8,pow(1.-r,2.)*A);}
