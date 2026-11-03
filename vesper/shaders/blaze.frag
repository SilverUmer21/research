#version 330 core
#include "common.glsl"
in vec2 U;in float layer;in float heat;out vec4 frag;
void main(){
 float f=noise3(vec3(U.x*12.-time*7.,U.y*7.,time));
 float a=(1.-U.x)*(.10+boost*.60+charge*.18)*(.15+.85*heat)*smoothstep(.12,.60,f)*(layer<.5?.55:.30);
 frag=vec4(magma(1.-U.x*.6)*1.6,a);
}
