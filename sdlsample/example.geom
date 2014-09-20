#version 330

layout (triangles) in;
layout (triangle_strip, max_vertices=3) out;

void main()
{
  for (int i = 0;i < gl_in.length();i++)
  {
    gl_Position = gl_in[i].gl_Position;

    // The following will cause the bottom of the triangle to be drawn at -0.8
    // instead of at -1.0.
    gl_Position.y = max(gl_Position.y, -0.8);
    EmitVertex();
  }
  EndPrimitive();
}
