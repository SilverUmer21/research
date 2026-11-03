#version 330 core
#include "common.glsl"
// Final grade: two bloom radii, an anamorphic streak on the hottest pixels,
// plume heat haze, lens chromatic fringe, hue-preserving shoulder, grain, vignette.
in vec2 uv;out vec4 frag;uniform sampler2D src,glowA,glowB,streak;uniform vec2 pixel,heatA0,heatB0,heatA1,heatB1;
uniform float shake,frameSeed;
float segment(vec2 p,vec2 a,vec2 b){vec2 d=b-a;float t=clamp(dot(p-a,d)/max(dot(d,d),.00001),0.,1.);return length(p-a-d*t);}
void main(){
 float hd=min(segment(uv,heatA0,heatB0),segment(uv,heatA1,heatB1));
 float heat=exp(-pow(hd/.03,2.))*boost;
 vec2 wob=vec2(noise3(vec3(uv*60.,time*9.))-.5,noise3(vec3(uv*60.+7.,time*9.))-.5);
 vec2 q=uv+wob*heat*.006;
 vec2 dc=q-.5;float ca=(.0012+shake*.002)*dot(dc,dc)*4.;
 vec3 col;
 col.r=texture(src,q+dc*ca).r;col.g=texture(src,q).g;col.b=texture(src,q-dc*ca).b;
 col+=texture(glowA,q).rgb*.30+texture(glowB,q).rgb*.22;
 col+=texture(streak,q).rgb*lin(vec3(.85,.45,1.))*.30;
 col+=lin(vec3(1.,.55,.95))*flash*.35;
 float lum=dot(col,vec3(.2126,.7152,.0722));float shoulder=lum/(1.+max(0.,lum-.85)*.45);
 col*=shoulder/max(lum,.00001);
 col=max(col,lin(vec3(.012,.006,.022)));
 col=srgb(col);
 col*=1.-.20*pow(length((uv-.5)*vec2(1.,.8)),1.4);
 col+=(hash(vec3(uv*resolution,frameSeed))-.5)*.022;
 frag=vec4(col,1.);
}
