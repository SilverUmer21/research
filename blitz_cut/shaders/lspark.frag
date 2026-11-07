#version 330 core
#include "common.glsl"
in vec2 Uv;in float A;in float Cid;in float T;out vec4 frag;
void main(){float r=length(Uv);if(r>1.)discard;vec3 c=Cid<.5?MAG():(Cid<1.5?CYA():ORA());frag=vec4(heat(c,.5+.5*T)*2.,sq(1.-r)*A);}
