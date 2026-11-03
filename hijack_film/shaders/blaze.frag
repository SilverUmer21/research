#version 330 core
#include "common.glsl"
in vec2 U;in float layer;in float heatv;in float S;out vec4 frag;
void main(){
 float f=noise3(vec3(U.x*12.-time*7.,U.y*7.,time));
 float a=(1.-U.x)*(.10+boost*.60+charge*.18)*(.15+.85*heatv)*smoothstep(.12,.60,f)*(layer<.5?.55:.30)*alive;
 frag=vec4(heat(prism(S*.33+time*.2,mixW),1.-U.x*.6)*1.6,a);
}
