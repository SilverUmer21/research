#version 330 core
#include "common.glsl"
// Barah Goti beads for the final reveal: glass domes with a living core.
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
uniform vec3 beadCenter;uniform float beadTeam,beadPop;
void main(){
 vec3 n=normalize(N),v=normalize(viewEye()-W);
 float F=pow(1.-max(dot(n,v),0.),3.);
 vec3 q=(W-beadCenter)*5.;
 float sw=fbm(q+vec3(0.,time*.8,beadTeam*3.));
 vec3 team=beadTeam<.5?magma(.55+.35*sw):lin(vec3(.05,.85,1.))*(1.2+1.8*sw);
 vec3 col=team*(.35+.9*(1.-F))+lin(vec3(.9,.8,1.))*F*.9;
 float top=pow(max(dot(reflect(-v,n),normalize(vec3(.1,.95,.3))),0.),40.);
 col+=vec3(1.)*top*.8;
 frag=vec4(col*beadPop,1.);
}
