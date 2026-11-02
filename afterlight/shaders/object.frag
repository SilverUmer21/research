#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;
out vec4 frag;
uniform sampler2D shadowmap,atlas;
uniform float gate;
vec3 fresnel(float cosTheta,vec3 f0){return f0+(1.-f0)*pow(1.-cosTheta,5.);}
vec3 highlight(vec3 n,vec3 v,vec3 l,vec3 base,float rough,float metal){
 vec3 h=normalize(v+l);float nv=max(dot(n,v),.001),nl=max(dot(n,l),.0),nh=max(dot(n,h),0.);
 float a=rough*rough,a2=a*a;float den=nh*nh*(a2-1.)+1.;float D=a2/(PI*den*den);
 float k=(rough+1.)*(rough+1.)/8.;float G=(nv/(nv*(1.-k)+k))*(nl/(nl*(1.-k)+k));
 return D*G*fresnel(max(dot(h,v),0.),mix(vec3(.045),base,metal))*nl/(4.*nv*max(nl,.001));
}
void main(){
 vec3 n=normalize(N),v=normalize(viewEye()-W),base=lin(C);if(U.x>=0.)base=lin(texture(atlas,U).rgb);
 float f=field(W-origin),edge=0.;
 if(hero>.5&&phase>.001){if(f<phase)discard;edge=pow(1.-smoothstep(0.,.028,f-phase),1.5);}
 vec3 s=L.xyz/L.w*.5+.5;float sh=0.;
 if(s.x>0.&&s.x<1.&&s.y>0.&&s.y<1.&&s.z<1.){for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)sh+=step(texture(shadowmap,s.xy+vec2(x,y)*2.2/3072.).r,s.z-max(.00055,.0012*(1.-dot(n,lightDir))));sh/=9.;}
 // Folio's single combined colored shadow, with floor bounce in the lit term.
 float core=1.-smoothstep(-.25,1.,dot(n,lightDir));float shadow=max(core,sh);
 float bounce=smoothstep(-1.,1.,-n.y)*pow(max(0.,(1.7-max(W.y,0.))/1.7),2.);
 vec3 bounced=mix(base,lin(vec3(.48,.14,.64)),bounce*.30);
 vec3 col=mix(bounced*keyColor(),base*shadowColor(),shadow);
 float metal=M<-.5?.55:.06;float rough=M<-.5?.29:(hero>.5?.32:.72);float coat=hero>.5?1.:.13;
 col+=highlight(n,v,lightDir,base,rough,metal)*keyColor()*(1.-sh)*.64*coat;
 // Broad studio reflections make the shell read as enamel, not a uniformly lit sphere.
 vec3 r=reflect(-v,n);
 float strip=pow(max(dot(r,normalize(vec3(.1,.92,.45))),0.),48.);
 float rose=pow(max(dot(r,normalize(vec3(-.55,.45,-.55))),0.),15.);
 vec3 F=fresnel(max(dot(n,v),0.),mix(vec3(.06),base,metal));
 vec3 panelA=theme<.5?lin(vec3(.82,.92,1.)):(theme<1.5?lin(vec3(.46,1.,.96)):lin(vec3(.64,.42,1.)));
 vec3 panelB=theme<.5?lin(vec3(1.,.46,.17)):(theme<1.5?lin(vec3(.24,.55,.75)):lin(vec3(1.,.12,.52)));
 col+=coat*F*(panelA*strip*2.0+panelB*rose*1.4);
 // Opposing mint and rose lights have surface response and falloff.
 float localGain=hero>.5?1.:.23;
 vec3 delta=worldPoint(vec3(-2.3,3.4,-2.5))-W;float d2=dot(delta,delta);
 col+=base*(theme<.5?lin(vec3(1.,.30,.08)):(theme<1.5?lin(vec3(.12,.45,.68)):lin(vec3(1.,.10,.45))))*max(0.,dot(n,normalize(delta)))*4.0*localGain/(1.+d2*.4);
 delta=worldPoint(vec3(1.5,2.7,2.8))-W;d2=dot(delta,delta);
 col+=base*lin(vec3(.12,.95,1.))*max(0.,dot(n,normalize(delta)))*2.2*localGain/(1.+d2*.5);
 // The molten cabin throws warm light onto seats, glass frames and body panels.
 float heatPulse=1.+.16*sin(time*7.5)+charge*.8;
 for(int i=0;i<3;i++){
   vec3 source=worldPoint(vec3(-.52+float(i)*.28,1.19+.035*sin(time*5.+float(i)),0.));
   delta=source-W;d2=dot(delta,delta);
   col+=base*energyColor()*max(0.,dot(n,normalize(delta)))*heatPulse*9.5/(1.+d2*7.);
   col+=highlight(n,v,normalize(delta),base,.25,.10)*energyColor()*heatPulse*1.7/(1.+d2*4.);
 }
 // Cool grazing light sculpts the silhouette in the deep violet environment.
 float rim=pow(1.-max(0.,dot(n,v)),3.5)*max(0.,dot(n,normalize(vec3(-.5,.3,-.8))));
 col+=lin(vec3(.12,.66,1.))*rim*.8;
 if(M>.1){
   vec3 e=lin(C);e/=max(dot(e,vec3(.2126,.7152,.0722)),.08);
   col=e*(M*(1.+charge*.65));
   if(M<1.3&&hero<.5)col*=.40+.30*sin(W.x*1.3+W.z*1.8-time*.9)+charge*.45+warm*.55;
 }
 if(M>2.9){float rise=smoothstep(W.y-.15,W.y+.35,gate*7.);float travel=1.-smoothstep(.0,.42,abs(W.y-gate*7.));col*=rise;col+=lin(vec3(.1,1.,.8))*travel*3.;}
 // Booster light strikes the rear body, nozzle petals and wing supports.
 for(int i=0;i<2;i++){
   delta=worldPoint(vec3(-2.85,.48,(float(i)*2.-1.)*.53))-W;d2=dot(delta,delta);
   col+=base*(theme<.5?lin(vec3(1.,.38,.035)):(theme<1.5?lin(vec3(.08,.43,1.)):lin(vec3(.71,.05,1.))))*boost*max(0.,dot(n,normalize(delta)))*8./(1.+d2*3.);
   col+=highlight(n,v,normalize(delta),base,.25,.12)*(theme<.5?lin(vec3(1.,.60,.10)):(theme<1.5?lin(vec3(.12,.58,1.)):lin(vec3(.85,.12,1.))))*boost*1.5/(1.+d2*3.);
 }
 // Localized colored spill from the branching body arteries.
 for(int i=0;i<6;i++){
   vec3 q=i==0?vec3(1.04,.98,.40):(i==1?vec3(1.7,.86,-.56):(i==2?vec3(-.30,.74,1.02):(i==3?vec3(.3,.62,-1.02):(i==4?vec3(-1.70,.98,.5):vec3(-1.70,.98,-.5)))));
   delta=worldPoint(q)-W;d2=dot(delta,delta);
   col+=base*energyColor()*(1.4+boost*2.8)*max(0.,dot(n,normalize(delta)))/(1.+d2*55.);
 }
 float fog=smoothstep(15.,60.,length(eye-W));col=mix(col,sky(gl_FragCoord.xy/resolution),fog*.72);
 frag=vec4(col,1.);
}
