#version 330 core
#include "common.glsl"
layout(location=0)in vec3 param;layout(location=2)in vec3 sides;
uniform mat4 model,vp;
out vec3 P;out vec2 U;out float layer;
void main(){
 float u=param.x,a=param.y;layer=param.z;
 float len=(.20+boost*3.5)*(1.+.025*sin(time*47.));
 float shock=layer<.5?.90+.10*cos(u*10.*PI-time*.6):1.;
 float r=.135*pow(max(0.,1.-u),.50)*(1.+u*.35)*shock*(layer<.5?.40:1.35);
 r*=1.+.12*sin(a*3.+u*33.-time*27.);
 float sway=.009*sin(u*15.-time*12.)*u;
 vec3 p=vec3(-2.73-u*len,.48+cos(a)*r+sway,sides.x*.53+sin(a)*r);
 vec4 w=model*vec4(p,1.);P=w.xyz;if(reflectionPass>.5)P.y=-P.y;
 gl_Position=vp*w;U=vec2(u,a/(2.*PI));
}
