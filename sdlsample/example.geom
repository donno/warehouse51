#version 330

layout (points) in;
layout (triangle_strip, max_vertices=3) out;

void main()
{
  for (int i = 0; i < gl_in.length(); i++)
  {
    gl_Position = gl_in[i].gl_Position;
    EmitVertex();

    gl_Position = gl_in[i].gl_Position + vec4(0.5, 0.5, 0.0, 0.0);
    EmitVertex();

    gl_Position = gl_in[i].gl_Position + vec4(0.5, 0.0, 0.0, 0.0);
    EmitVertex();
    EndPrimitive();
  }
}
