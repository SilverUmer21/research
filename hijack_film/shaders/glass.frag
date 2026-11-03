#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
void main(){
 vec3 lp=localPoint(W);if(dissolveEdge(lp)<0.)discard;
 vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;
 vec3 v=normalize(viewEye()-W);float facing=abs(dot(n,v));float F=.035+.965*pow(1.-facing,5.);
 vec3 r=reflect(-v,n);float stripe=pow(max(dot(r,normalize(vec3(-.3,.85,.45))),0.),70.);
 vec3 col=lin(vec3(.14,.10,.36))*.35+lin(vec3(.75,.6,1.))*stripe*.8;
 float d=length(lp-vec3(-.24,1.19,0.));
 col+=prism(time*.2,mixW)*(.3+3.2*heartI)*exp(-d*d*2.1);
 frag=vec4(col,.10+F*.34+stripe*.12);
}
