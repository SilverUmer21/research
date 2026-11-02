#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;out vec4 frag;
void main(){
 vec3 p=localPoint(W);float scale=lavaKind>.5?15.:5.4;
 vec3 q=p*scale+vec3(-time*(1.1+boost),time*.60,time*.25);
 float turbulence=noise3(q)+.5*noise3(q*2.3+time*.5);
 float flow=p.x*3.5+p.z*(lavaKind>.5?8.:0.)+turbulence*1.8-time*(.8+boost*.5);
 float vein=1.-smoothstep(.018,.100,abs(fract(flow)-.5));float hot=smoothstep(.48,1.28,turbulence);
 vec3 fire=energyColor(),core=mix(fire,vec3(1.),.66);vec3 ember=fire*.18;float intensity=1.;
 if(lavaKind>.5&&lavaKind<1.5){fire=theme<.5?lin(vec3(1.,.65,.20)):(theme<1.5?lin(vec3(.08,1.,.86)):lin(vec3(.62,.40,1.)));core=mix(fire,vec3(1.),.68);ember=fire*.16;intensity=.72;}
 else if(lavaKind>1.5&&lavaKind<2.5){fire=theme<.5?lin(vec3(1.,.02,.14)):(theme<1.5?lin(vec3(.45,.025,1.)):lin(vec3(1.,.26,.02)));core=mix(fire,vec3(1.),.50);ember=fire*.12;intensity=.65+brake*.6;}
 else if(lavaKind>2.5&&lavaKind<3.5){intensity=.5+boost*.2;}
 else if(lavaKind>3.5){fire=theme<.5?lin(vec3(1.,.38,.035)):(theme<1.5?lin(vec3(.06,.46,1.)):lin(vec3(.71,.05,1.)));core=mix(fire,vec3(1.),.65);ember=fire*.10;intensity=.20+boost*1.2;}
 vec3 col=mix(ember*.32,fire*1.8,hot);col=mix(col,core*(2.3+charge*2.3),vein);
 if(lavaKind>.5)col+=fire*.28;
 col*=intensity*(.93+.07*sin(time*8.+p.x*14.));frag=vec4(col,1.);
}
