#version 330 core
#include "common.glsl"
layout(location=0)in vec3 pos;layout(location=1)in vec3 dir;layout(location=2)in vec3 info;layout(location=4)in vec2 uv;
uniform mat4 vp;uniform vec3 cameraRight,cameraUp;uniform float tnow;
out vec2 Uv;out float A;out float Cid;out float T;
void main(){
 Cid=info.x;float age=tnow-info.y;float life=.5+info.z*.9;
 float on=step(0.,age)*step(age,life);T=clamp(1.-age/life,0.,1.);
 vec3 p=pos+dir*age*(.8+info.z*1.6)+vec3(0.,-1.8*age*age+.4*age,0.);
 float sz=(.012+info.z*.022)*on;
 p+=cameraRight*uv.x*sz+cameraUp*uv.y*sz;if(reflectionPass>.5)p.y=-p.y;
 gl_Position=vp*vec4(p,1.);Uv=uv;A=on*T;
}
