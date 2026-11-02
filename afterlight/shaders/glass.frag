#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
void main(){
 float f=field(W-origin);if(phase>.001&&f<phase)discard;
 vec3 n=normalize(N);if(!gl_FrontFacing)n=-n;
 vec3 v=normalize(viewEye()-W);float facing=abs(dot(n,v));float F=.035+.965*pow(1.-facing,5.);
 vec3 r=reflect(-v,n);float stripe=pow(max(dot(r,normalize(vec3(-.3,.85,.45))),0.),70.);
 vec3 col=lin(vec3(.12,.28,.52))*.35+lin(vec3(.28,.9,1.))*stripe*.8;
 float d=length(localPoint(W)-vec3(-.24,1.19,0.));
 col+=energyColor()*(2.8+charge*2.0)*exp(-d*d*2.1);
 float edge=phase>.001?1.-smoothstep(0.,.025,f-phase):0.;col+=lin(vec3(.12,1.,.9))*edge*2.;
 float alpha=.12+F*.34+stripe*.12;
 frag=vec4(col,alpha);
}
