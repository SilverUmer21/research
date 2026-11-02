#version 330 core
layout(location=0)in vec3 pos;layout(location=1)in vec3 normal;layout(location=2)in vec3 color;layout(location=3)in float material;layout(location=4)in vec2 uv;
uniform mat4 model,vp,lightvp;uniform float reflectionPass;
out vec3 W,N,C;out vec2 U;out float M;out vec4 L;
void main(){vec4 p=model*vec4(pos,1.);N=normalize(transpose(inverse(mat3(model)))*normal);W=p.xyz;if(reflectionPass>.5){W.y=-W.y;N.y=-N.y;}C=color;M=material;U=uv;L=lightvp*vec4(W+N*.035,1.);gl_Position=vp*p;}
