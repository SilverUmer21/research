#version 330 core
#include "common.glsl"
layout(location=0)in vec3 pos;layout(location=1)in vec3 offs;layout(location=2)in vec3 info;
uniform mat4 vp;uniform float tnow,solid;
out float Tau,Vis,Cid,Age;
void main(){
 Cid=info.x;Tau=info.y;Vis=info.z;Age=tnow-Tau;
 float head=Age>=0.?exp(-Age*7.):0.;
 float r=mix(.030,.022,solid)+.085*head+.012*sin(Tau*40.-time*10.)*solid;
 vec3 p=pos+offs*r;if(reflectionPass>.5)p.y=-p.y;
 gl_Position=vp*vec4(p,1.);
}
