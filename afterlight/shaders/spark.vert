#version 330 core
#include "common.glsl"
layout(location=0)in vec3 rnd;layout(location=2)in vec3 side;layout(location=3)in float seed;layout(location=4)in vec2 uv;
uniform mat4 model,vp;uniform vec3 cameraRight,cameraUp;out vec2 U;out float A;
void main(){
 float age=fract(rnd.x+time*(1.3+rnd.y));float len=.2+boost*3.5;
 float theta=rnd.y*2.*PI;float spread=.03+age*age*.20;
 vec3 p=vec3(-2.73-age*(len+1.0),.48+cos(theta)*spread+age*.10,side.x*.53+sin(theta)*spread);
 vec4 w=model*vec4(p,1.);vec3 tangent=normalize(mat3(model)*vec3(-1,0,0));
 float sz=.004+rnd.z*.008;w.xyz+=tangent*uv.x*sz*3.+cameraUp*uv.y*sz;
 gl_Position=vp*w;U=uv;A=pow(1.-age,1.5)*boost*.7;
}
