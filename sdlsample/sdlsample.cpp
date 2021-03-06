//===----------------------------------------------------------------------===//
//
// NAME         : SDLSample
// NAMESPACE    : Global namespace.
// PURPOSE      : Provides a simple SDL sample that can be built upon.
// COPYRIGHT    : (c) 2014 Sean Donnellan. All Rights Reserved.
// AUTHORS      : Sean Donnellan (darkdonno@gmail.com)
// DESCRIPTION  : Creates a window and an OpenGL render and draws a triangle.
//
// Uses OpenGL 3/4 functions via gl3w (https://github.com/shakesoda/gl3w).
//
// This sends two points to OpenGL each of witch gets rendered as a triangle
// thanks to the geometry shader.
// The triangle is coloured blue by a fragment shader.
//
//===----------------------------------------------------------------------===//

#include "GL/gl3w.h"

#include "SDL.h"

#include <fstream>
#include <iostream>
#include <string>
#include <vector>

const char* WindowTitle = "SDLSample";

class ShaderProgram
{
  GLuint myVertexShader;
  GLuint myFragmentShader;
  GLuint myGeometryShader;
  GLuint myShaderProgram;

  // Read the entire contents of a file into a string.
  static std::string Read(const char* FilePath);

public:
  ShaderProgram(const char* VertexFilePath,
                const char* FragmentFilePath,
                const char* GeometryFilePath = nullptr);
  ~ShaderProgram();

  operator GLuint() { return myShaderProgram; }
};

// Implementation detail for ShaderProgram.
std::string ShaderProgram::Read(const char* FilePath)
{
  std::string contents;
  std::ifstream stream(FilePath, std::ios::in);
  if (stream.is_open())
  {
     std::string line;
     while (std::getline(stream, line))
     {
       contents += '\n';
       contents += line;
     }
     stream.close();
  }
  return contents;
}

ShaderProgram::ShaderProgram(
  const char* VertexFilePath,
  const char* FragmentFilePath,
  const char* GeometryFilePath)
  : myVertexShader(0),
    myFragmentShader(0),
    myGeometryShader(0),
    myShaderProgram(0)
{
  // TODO: Make the following exception safe to ensure CreateShader is reversed
  // if something later fails (i.e are deleted)

  GLint result = GL_FALSE;
  int logLength;

  // Create the vertex shader.
  {
    const std::string vertexShaderSource = Read(VertexFilePath);
    const char * const source = vertexShaderSource.c_str();

    myVertexShader = glCreateShader(GL_VERTEX_SHADER);
    glShaderSource(myVertexShader, 1, (const GLchar**)&source, 0);

    glCompileShader(myVertexShader);

    // Check the shader.
    glGetShaderiv(myVertexShader, GL_COMPILE_STATUS, &result);
    glGetShaderiv(myVertexShader, GL_INFO_LOG_LENGTH, &logLength);
    if (result == GL_FALSE || logLength > 1)
    {
      std::unique_ptr<char[]> errorMessage(new char[logLength]);
      glGetShaderInfoLog(myVertexShader, logLength, nullptr, errorMessage.get());
      fprintf(stdout, "%s\n", errorMessage.get());
    }
  }

  // Create the fragment shader.
  {
    const std::string fragmentShaderSource = Read(FragmentFilePath);
    const char * const source = fragmentShaderSource.c_str();

    myFragmentShader = glCreateShader(GL_FRAGMENT_SHADER);
    glShaderSource(myFragmentShader, 1, (const GLchar**)&source, 0);

    glCompileShader(myFragmentShader);

    // Check the shader.
    glGetShaderiv(myFragmentShader, GL_COMPILE_STATUS, &result);
    glGetShaderiv(myFragmentShader, GL_INFO_LOG_LENGTH, &logLength);
    if (result == GL_FALSE || logLength > 1)
    {
      std::unique_ptr<char[]> errorMessage(new char[logLength]);
      glGetShaderInfoLog(myFragmentShader, logLength, nullptr, errorMessage.get());
      fprintf(stdout, "%s\n", errorMessage.get());
    }
  }

  // Create the optional geometry shader shader.
  if (GeometryFilePath)
  {
    const std::string geometryShaderSource = Read(GeometryFilePath);
    const char * const source = geometryShaderSource.c_str();

    myGeometryShader = glCreateShader(GL_GEOMETRY_SHADER);
    glShaderSource(myGeometryShader, 1, (const GLchar**) &source, 0);

    glCompileShader(myGeometryShader);

    // Check the shader.
    glGetShaderiv(myGeometryShader, GL_COMPILE_STATUS, &result);
    glGetShaderiv(myGeometryShader, GL_INFO_LOG_LENGTH, &logLength);
    if (result == GL_FALSE || logLength > 1)
    {
      std::unique_ptr<char[]> errorMessage(new char[logLength]);
      glGetShaderInfoLog(myGeometryShader, logLength, nullptr, errorMessage.get());
      fprintf(stdout, "%s\n", errorMessage.get());
    }
  }

  // Compile the shaders.
  myShaderProgram = glCreateProgram();

  glAttachShader(myShaderProgram, myFragmentShader);
  glAttachShader(myShaderProgram, myVertexShader);
  if (GeometryFilePath) glAttachShader(myShaderProgram, myGeometryShader);

  glLinkProgram(myShaderProgram);

  glGetProgramiv(myShaderProgram, GL_LINK_STATUS, &result);
  glGetProgramiv(myShaderProgram, GL_INFO_LOG_LENGTH, &logLength);
  if (result == GL_FALSE || logLength > 1)
  {
    std::unique_ptr<char []> errorMessage(new char[logLength]);
    glGetProgramInfoLog(myShaderProgram, logLength, nullptr, errorMessage.get());
    fprintf(stdout, "%s\n", errorMessage.get());
  }
}

ShaderProgram::~ShaderProgram()
{
  glDetachShader(myShaderProgram, myVertexShader);
  glDetachShader(myShaderProgram, myFragmentShader);
  glDeleteProgram(myShaderProgram);
  glDeleteShader(myVertexShader);
  glDeleteShader(myFragmentShader);
}

// An array of 3 points which represents 3 vertices
static const GLfloat Points[][3] = {
  { -0.5f, -0.5f, -0.5f },
  { 0.0f, 0.0f, -0.5f },
};

void HandleEvent(const SDL_Event& Event)
{
  // Handle user input.
}

#if defined(_WIN32)
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <windows.h>
int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance,
                   LPSTR lpCmdLine, int nCmdShow)
#else
int main(int argc, char *argv[])
#endif
{
  // Initialise the SDL library
  if (SDL_Init(SDL_INIT_VIDEO) < 0) {
    std::cerr << "Couldn't initialise SDL: " << SDL_GetError() << std::endl;
    return -1;
  }

  SDL_Window* const window = SDL_CreateWindow(
    WindowTitle, SDL_WINDOWPOS_UNDEFINED, SDL_WINDOWPOS_UNDEFINED, 720, 576,
    SDL_WINDOW_OPENGL | SDL_WINDOW_SHOWN);

  if (window == nullptr) {
    std::cerr << "Unable to create window: " << SDL_GetError() << std::endl;
    return -2;
  }

  const SDL_GLContext context = SDL_GL_CreateContext(window);

  if (gl3wInit()) {
    std::cerr << "Failed to initialize OpenGL" << std::endl;
    return -3;
  }

  if (!gl3wIsSupported(3, 2))
  {
    std::cerr << "Failed - OpenGL 3.2 is not supported by your machine."
              << std::endl;
    return -4;
  }

  std::cout << "OpenGL " << glGetString(GL_VERSION)
            << ", GLSL " << glGetString(GL_SHADING_LANGUAGE_VERSION)
            << std::endl;

  // Create a buffer in OpenGL and give it our point data.
  GLuint vertexBuffer;
  glGenBuffers(1, &vertexBuffer);
  glBindBuffer(GL_ARRAY_BUFFER, vertexBuffer);
  glBufferData(GL_ARRAY_BUFFER, sizeof(Points), Points, GL_STATIC_DRAW);

  ShaderProgram program("example.vert", "example.frag", "example.geom");

  glUseProgram(program);

  // Enter the main game loop.
  bool running = true;
  for (SDL_Event event; running;)
  {
    // Handle drawing.
    {
      glClearColor(0, 255, 0, 1);
      glClear(GL_COLOR_BUFFER_BIT);

      // 1rst attribute buffer : vertices
      glEnableVertexAttribArray(0);
      glBindBuffer(GL_ARRAY_BUFFER, vertexBuffer);
      glVertexAttribPointer(
        0, // attribute (i.e layout in a shader)
        3, // the number of elements.
        GL_FLOAT,
        GL_FALSE, // normalized?
        0,        // stride
        (void*) 0  // array buffer offset
        );
      glDrawArrays(GL_POINTS, 0, 2);
      glDisableVertexAttribArray(0);
    }

    SDL_GL_SwapWindow(window);

    while (SDL_PollEvent(&event)) {
      if (event.type == SDL_QUIT) {
        running = false;
        break;
      } else if (event.key.type == SDL_KEYUP) {
        if (event.key.keysym.sym == SDLK_F4 &&
            event.key.keysym.mod & KMOD_ALT) {
          running = false;
          break;
        }
        HandleEvent(event);
      } else {
        HandleEvent(event);
      }
    }

    // If the application is minimised put the game to sleep. This way
    // it won't use as many CPU cycles.
    if (SDL_GetWindowFlags(window) & SDL_WINDOW_MINIMIZED)
    {
      SDL_Delay(1000);
    }
  }

  SDL_GL_DeleteContext(context);
  SDL_DestroyWindow(window);
  SDL_Quit();
  return 0;
}

//===----------------------------------------------------------------------===//
