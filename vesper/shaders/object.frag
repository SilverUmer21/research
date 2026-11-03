#version 330 core
#include "common.glsl"
// Lit car surfaces: folio-style single tinted shadow, enamel studio reflections,
// and light that comes from the energy itself (cabin heart, travelling vein pulses,
// boosters, ignition flash, headlamps).
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;
out vec4 frag;
uniform sampler2D shadowmap,atlas;
uniform vec4 pulses[24];
uniform int pulseCount;
vec3 fresnel(float c,vec3 f0){return f0+(1.-f0)*pow(1.-c,5.);}
vec3 highlight(vec3 n,vec3 v,vec3 l,vec3 base,float rough,float metal){
 vec3 h=normalize(v+l);float nv=max(dot(n,v),.001),nl=max(dot(n,l),0.),nh=max(dot(n,h),0.);
 float a=rough*rough,a2=a*a;float den=nh*nh*(a2-1.)+1.;float D=a2/(PI*den*den);
 float k=(rough+1.)*(rough+1.)/8.;float G=(nv/(nv*(1.-k)+k))*(nl/(nl*(1.-k)+k));
 return D*G*fresnel(max(dot(h,v),0.),mix(vec3(.045),base,metal))*nl/(4.*nv*max(nl,.001));
}
void main(){
 vec3 n=normalize(N),v=normalize(viewEye()-W),base=lin(C);if(U.x>=0.)base=lin(texture(atlas,U).rgb);
 vec3 s=L.xyz/L.w*.5+.5;float sh=0.;
 if(s.x>0.&&s.x<1.&&s.y>0.&&s.y<1.&&s.z<1.){for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)sh+=step(texture(shadowmap,s.xy+vec2(x,y)*2.2/3072.).r,s.z-max(.00055,.0012*(1.-dot(n,lightDir))));sh/=9.;}
 float core=1.-smoothstep(-.25,1.,dot(n,lightDir));float shadow=max(core,sh);
 float bounce=smoothstep(-1.,1.,-n.y)*sq(max(0.,(1.7-max(W.y,0.))/1.7));
 vec3 bounced=mix(base,lin(vec3(.48,.10,.64)),bounce*.32);
 // The key light is dimmed while the car is "asleep" so the energy can light it.
 float wake=.30+.70*smoothstep(.0,1.,charge);
 vec3 col=mix(bounced*keyColor(),base*shadowColor(),shadow)*wake;
 float metal=M<-.5?.55:.06;float rough=M<-.5?.29:.32;
 col+=highlight(n,v,lightDir,base,rough,metal)*keyColor()*(1.-sh)*.64*wake;
 vec3 r=reflect(-v,n);
 float strip=pow(max(dot(r,normalize(vec3(.1,.92,.45))),0.),48.);
 float rose=pow(max(dot(r,normalize(vec3(-.55,.45,-.55))),0.),15.);
 // A travelling softbox: the long top highlight slides along the body with travel.
 float slide=pow(max(dot(r,normalize(vec3(sin(travel*.07),.85,.5))),0.),90.)*smoothstep(.5,6.,speed);
 vec3 F=fresnel(max(dot(n,v),0.),mix(vec3(.06),base,metal));
 col+=F*(lin(vec3(.64,.42,1.))*(strip*2.0+slide*2.5)+lin(vec3(1.,.12,.52))*rose*1.4)*wake;
 vec3 delta=worldPoint(vec3(-2.3,3.4,-2.5))-W;float d2=dot(delta,delta);
 col+=base*lin(vec3(1.,.10,.45))*max(0.,dot(n,normalize(delta)))*4.0*wake/(1.+d2*.4);
 delta=worldPoint(vec3(1.5,2.7,2.8))-W;d2=dot(delta,delta);
 col+=base*lin(vec3(.30,.55,1.))*max(0.,dot(n,normalize(delta)))*1.6*wake/(1.+d2*.5);
 // Cabin heart: three wandering point lights whose strength follows the heartbeat.
 for(int i=0;i<3;i++){
   vec3 src=worldPoint(vec3(-.52+float(i)*.28,1.19+.035*sin(time*5.+float(i)),0.));
   delta=src-W;d2=dot(delta,delta);
   col+=base*energyColor()*max(0.,dot(n,normalize(delta)))*heartI*7./(1.+d2*8.);
   col+=highlight(n,v,normalize(delta),base,.25,.10)*energyColor()*heartI*1.9/(1.+d2*4.);
 }
 // Travelling vein pulses are real lights: the paint around a pulse brightens as it passes.
 for(int i=0;i<24;i++){
   if(i>=pulseCount)break;
   delta=pulses[i].xyz-W;d2=dot(delta,delta);
   float nl=max(0.,dot(n,normalize(delta))*.8+.2);
   col+=base*mix(energyColor(),vec3(1.,.7,.95),.25)*pulses[i].w*nl*1.15/(1.+d2*90.);
   col+=highlight(n,v,normalize(delta),base,.22,.1)*energyColor()*pulses[i].w*.20/(1.+d2*60.);
 }
 // Headlamp spill on the nose and the floor-facing aero.
 delta=worldPoint(vec3(2.9,.62,0.))-W;d2=dot(delta,delta);
 col+=base*lin(vec3(.76,.63,1.))*lampI*max(0.,dot(n,normalize(delta)))*1.4/(1.+d2*3.);
 float rim=pow(1.-max(0.,dot(n,v)),3.5)*max(0.,dot(n,normalize(vec3(-.5,.3,-.8))));
 col+=lin(vec3(.45,.30,1.))*rim*.8*wake;
 if(M>.1){
   vec3 e=lin(C);e/=max(dot(e,vec3(.2126,.7152,.0722)),.08);
   float on=M<1.3?mix(.15,1.,charge):1.;
   col=e*(M*(1.+charge*.65))*on;
 }
 // Booster light and the ignition flash strike the rear body, petals and wing.
 for(int i=0;i<2;i++){
   delta=worldPoint(vec3(-2.85,.48,(float(i)*2.-1.)*.53))-W;d2=dot(delta,delta);
   float b=boost+flash*1.6;
   col+=base*boosterColor()*b*max(0.,dot(n,normalize(delta)))*8./(1.+d2*3.);
   col+=highlight(n,v,normalize(delta),base,.25,.12)*lin(vec3(.95,.25,1.))*b*1.5/(1.+d2*3.);
 }
 float fog=smoothstep(14.,55.,length(eye-W));col=mix(col,sky(gl_FragCoord.xy/resolution),fog*.75);
 frag=vec4(col,1.);
}
