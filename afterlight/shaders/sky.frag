#version 330 core
#include "common.glsl"
in vec2 uv;out vec4 frag;void main(){frag=vec4(sky(uv),1.);}
