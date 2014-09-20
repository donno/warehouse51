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
// This sends three points to OpenGL which gets renders as a triangle.
//
// TODO: Add support loading in a vertex, fragment and geometry shader.
//
//===----------------------------------------------------------------------===//

#include "GL/gl3w.h"

#include "SDL.h"

#include <iostream>

const char* WindowTitle = "SDLSample";

// An array of 3 points which represents 3 vertices
static const GLfloat Points[] = {
   -1.0f, -1.0f, 0.0f,
   1.0f, -1.0f, 0.0f,
   0.0f,  1.0f, 0.0f,
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

      glDrawArrays(GL_TRIANGLES, 0, 3);
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
