#version 330 core
#include "common.glsl"
in vec2 U;in float layer;in float heat;out vec4 frag;
void main(){
 float f=noise3(vec3(U.x*12.-time*7.,U.y*7.,time));
 float a=(1.-U.x)*(.18+boost*.60+charge*.18)*(.25+.75*heat)*smoothstep(.12,.60,f)*(layer<.5?.55:.30);
 vec3 c=mix(energyColor(),vec3(1.),(1.-U.x)*(layer<.5?.68:.10));frag=vec4(c*3.2,a);
}
