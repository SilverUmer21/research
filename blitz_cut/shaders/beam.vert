#version 330 core
#include "common.glsl"
// A stolen-energy arc: a tube along a quadratic Bezier from one car's heart into another car.
layout(location=0)in vec3 param;
uniform mat4 vp;uniform vec3 bA,bB;uniform float arch,width;
out vec2 U;out float layer;
void main(){
 float u=param.x,a=param.y;layer=param.z;
 vec3 mid=(bA+bB)*.5+vec3(0.,arch,0.);
 vec3 p=mix(mix(bA,mid,u),mix(mid,bB,u),u);
 vec3 tg=normalize(mix(mid-bA,bB-mid,u));
 vec3 s1=normalize(cross(tg,vec3(0.,1.,0.)+vec3(.001)));vec3 s2=cross(tg,s1);
 float wob=.05*sin(u*19.-time*13.)+.03*sin(u*41.+time*9.);
 p+=s1*wob*sin(u*PI);
 float r=width*(layer<.5?1.:3.2)*(.6+.4*sin(u*PI))*(1.+.3*sin(u*30.-time*20.));
 p+=(s1*cos(a)+s2*sin(a))*r;
 if(reflectionPass>.5)p.y=-p.y;
 gl_Position=vp*vec4(p,1.);U=vec2(u,a);
}
