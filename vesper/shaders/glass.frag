#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
void main(){
 vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;
 vec3 v=normalize(viewEye()-W);float facing=abs(dot(n,v));float F=.035+.965*pow(1.-facing,5.);
 vec3 r=reflect(-v,n);float stripe=pow(max(dot(r,normalize(vec3(-.3,.85,.45))),0.),70.);
 float slide=pow(max(dot(r,normalize(vec3(sin(travel*.11),.8,.55))),0.),120.)*smoothstep(.5,6.,speed);
 vec3 col=lin(vec3(.16,.10,.40))*.35+lin(vec3(.75,.55,1.))*(stripe*.8+slide*1.5);
 float d=length(localPoint(W)-vec3(-.24,1.19,0.));
 col+=energyColor()*(.6+3.2*heartI)*exp(-d*d*2.1);
 float alpha=.10+F*.34+stripe*.12+slide*.2;
 frag=vec4(col,alpha);
}
