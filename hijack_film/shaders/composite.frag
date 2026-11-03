#version 330 core
#include "common.glsl"
in vec2 uv;out vec4 frag;uniform sampler2D src,glowA,glowB,streak;uniform vec2 pixel,heatA0,heatB0,heatA1,heatB1;
uniform float shake,frameSeed,fade;
float segment(vec2 p,vec2 a,vec2 b){vec2 d=b-a;float t=clamp(dot(p-a,d)/max(dot(d,d),.00001),0.,1.);return length(p-a-d*t);}
void main(){
 float hd=min(segment(uv,heatA0,heatB0),segment(uv,heatA1,heatB1));
 float hz=exp(-sq(hd/.03))*boost;
 vec2 wob=vec2(noise3(vec3(uv*60.,time*9.))-.5,noise3(vec3(uv*60.+7.,time*9.))-.5);
 vec2 q=uv+wob*hz*.006;
 vec2 dc=q-.5;float ca=(.0014+shake*.003)*dot(dc,dc)*4.;
 vec3 col;
 col.r=texture(src,q+dc*ca).r;col.g=texture(src,q).g;col.b=texture(src,q-dc*ca).b;
 col+=texture(glowA,q).rgb*.32+texture(glowB,q).rgb*.26;
 col+=texture(streak,q).rgb*.32;
 col+=lin(vec3(1.,.8,1.))*flash*flash*.07;
 float lum=dot(col,vec3(.2126,.7152,.0722));float shoulder=lum/(1.+max(0.,lum-.85)*.45);
 col*=shoulder/max(lum,.00001);
 col=max(col,lin(vec3(.010,.005,.020)));
 col=srgb(col);
 col*=1.-.22*pow(length((uv-.5)*vec2(1.,.8)),1.4);
 col+=(hash(vec3(uv*resolution,frameSeed))-.5)*.022;
 frag=vec4(col*fade,1.);
}
