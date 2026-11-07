#version 330 core
#include "common.glsl"
in vec3 W,N,C;in vec2 U;in float M;in vec4 L;
out vec4 frag;
uniform sampler2D shadowmap,atlas;
uniform vec4 pulses[24];uniform vec3 pulseColors[24];uniform int pulseCount;
uniform vec4 logoLights[3];
vec3 fresnel(float c,vec3 f0){return f0+(1.-f0)*pow(1.-c,5.);}
vec3 highlight(vec3 n,vec3 v,vec3 l,vec3 base,float rough,float metal){
 vec3 h=normalize(v+l);float nv=max(dot(n,v),.001),nl=max(dot(n,l),0.),nh=max(dot(n,h),0.);
 float a=rough*rough,a2=a*a;float den=nh*nh*(a2-1.)+1.;float D=a2/(PI*den*den);
 float k=(rough+1.)*(rough+1.)/8.;float G=(nv/(nv*(1.-k)+k))*(nl/(nl*(1.-k)+k));
 return D*G*fresnel(max(dot(h,v),0.),mix(vec3(.045),base,metal))*nl/(4.*nv*max(nl,.001));
}
void main(){
 vec3 lp=localPoint(W);float edge=dissolveEdge(lp);if(edge<0.)discard;
 vec3 n=normalize(N),v=normalize(viewEye()-W),base=lin(C);if(U.x>=0.)base=lin(texture(atlas,U).rgb);
 float grey=dot(base,vec3(.2126,.7152,.0722));base=mix(base,vec3(grey)*vec3(.92,.94,1.05),desat);
 vec3 s=L.xyz/L.w*.5+.5;float sh=0.;
 if(s.x>0.&&s.x<1.&&s.y>0.&&s.y<1.&&s.z<1.){for(int x=-1;x<=1;x++)for(int y=-1;y<=1;y++)sh+=step(texture(shadowmap,s.xy+vec2(x,y)*2.2/3072.).r,s.z-max(.0007,.0014*(1.-dot(n,lightDir))));sh/=9.;}
 float core=1.-smoothstep(-.25,1.,dot(n,lightDir));float shadow=max(core,sh);
 float bounce=smoothstep(-1.,1.,-n.y)*sq(max(0.,(1.7-max(W.y,0.))/1.7));
 vec3 bounced=mix(base,lin(vec3(.40,.10,.60)),bounce*.30);
 float wake=.30+.70*charge;
 vec3 col=mix(bounced*keyColor(),base*shadowColor(),shadow)*wake;
 float metal=M<-.5?.55:.06;float rough=M<-.5?.29:.32;
 col+=highlight(n,v,lightDir,base,rough,metal)*keyColor()*(1.-sh)*.64*wake;
 vec3 r=reflect(-v,n);
 float strip=pow(max(dot(r,normalize(vec3(.1,.92,.45))),0.),48.);
 float rose=pow(max(dot(r,normalize(vec3(-.55,.45,-.55))),0.),15.);
 vec3 F=fresnel(max(dot(n,v),0.),mix(vec3(.06),base,metal));
 vec3 accent=avgEnergy(mixW);
 col+=F*(lin(vec3(.62,.48,1.))*strip*2.0+mix(lin(vec3(.5,.3,.7)),accent,alive)*rose*1.3)*wake;
 // Cabin heart: colour follows the energies this car holds.
 for(int i=0;i<3;i++){
   vec3 src=worldPoint(vec3(-.52+float(i)*.28,1.19+.035*sin(time*5.+float(i)),0.));
   vec3 delta=src-W;float d2=dot(delta,delta);
   vec3 hc=prism(time*.25+float(i)*.33,mixW);
   col+=base*hc*max(0.,dot(n,normalize(delta)))*heartI*7./(1.+d2*8.);
   col+=highlight(n,v,normalize(delta),base,.25,.10)*hc*heartI*1.6/(1.+d2*4.);
 }
 for(int i=0;i<24;i++){
   if(i>=pulseCount)break;
   vec3 delta=pulses[i].xyz-W;float d2=dot(delta,delta);
   float nl=max(0.,dot(n,normalize(delta))*.8+.2);
   col+=base*pulseColors[i]*pulses[i].w*nl*1.2/(1.+d2*80.);
   col+=highlight(n,v,normalize(delta),base,.22,.1)*pulseColors[i]*pulses[i].w*.22/(1.+d2*60.);
 }
 vec3 delta=worldPoint(vec3(2.9,.62,0.))-W;float d2=dot(delta,delta);
 col+=base*lin(vec3(.76,.66,1.))*lampI*max(0.,dot(n,normalize(delta)))*1.3/(1.+d2*3.);
 // Light from the logo letters once they burn.
 for(int i=0;i<3;i++){
   vec3 dl=logoLights[i].xyz-W;float dd=dot(dl,dl);
   col+=base*toRed(ring(float(i)*.33+time*.15),float(i)*.3)*logoI*logoLights[i].w*max(0.,dot(n,normalize(dl)))*14./(1.+dd*.35);
 }
 float rim=pow(1.-max(0.,dot(n,v)),3.5)*max(0.,dot(n,normalize(vec3(-.5,.3,-.8))));
 col+=mix(lin(vec3(.40,.32,.9)),accent,.5*alive)*rim*.75*wake;
 if(M>.1){
   vec3 e=lin(C);e/=max(dot(e,vec3(.2126,.7152,.0722)),.08);
   if(M<1.3)e=mix(e,prism(lp.x*.2+time*.1,mixW)/max(dot(prism(lp.x*.2+time*.1,mixW),vec3(.2126,.7152,.0722)),.08),.6*alive);
   col=e*(M*(1.+charge*.65))*mix(.04,1.,alive);
 }
 for(int i=0;i<2;i++){
   delta=worldPoint(vec3(-2.85,.48,(float(i)*2.-1.)*.53))-W;d2=dot(delta,delta);
   float b=boost+flash*1.4;vec3 bc=prism(time*.7+float(i)*.5,mixW);
   col+=base*bc*b*max(0.,dot(n,normalize(delta)))*8./(1.+d2*3.);
   col+=highlight(n,v,normalize(delta),base,.25,.12)*mix(bc,vec3(1.),.3)*b*1.5/(1.+d2*3.);
 }
 col+=heat(avgEnergy(mixW),.75)*edge*1.4;
 float fog=smoothstep(18.,70.,length(eye-W));col=mix(col,sky(gl_FragCoord.xy/resolution),fog*.75);
 frag=vec4(col,1.);
}
