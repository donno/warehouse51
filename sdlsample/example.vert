#version 150
#extension GL_ARB_separate_shader_objects : enable

layout(location = 0) in vec3 position;

void main(void) {
  // Pass the point straight through..
  gl_Position = vec4(position, 1.0);
}
