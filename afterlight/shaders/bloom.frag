#version 330 core
in vec2 uv;out vec4 frag;uniform sampler2D src;uniform vec2 stepv;uniform float extract;
vec3 readC(vec2 p){vec3 c=texture(src,p).rgb;return extract>.5?max(c-1.,0.):c;}
void main(){const float w[5]=float[5](.227027,.1945946,.1216216,.054054,.016216);vec3 c=readC(uv)*w[0];for(int i=1;i<5;i++)c+=(readC(uv+stepv*float(i))+readC(uv-stepv*float(i)))*w[i];frag=vec4(c,1.);}
