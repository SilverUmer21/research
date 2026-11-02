#version 330 core
#include "common.glsl"
in vec2 U;in float A;out vec4 frag;void main(){float r=length(U);if(r>1.)discard;vec3 c=theme<.5?vec3(1.,.40,.08):(theme<1.5?vec3(.25,.65,1.):vec3(.9,.15,1.));frag=vec4(c*2.5,pow(1.-r,2.)*A);}
