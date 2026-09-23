// Diagnostic probe (ours, not author code): links the AUTHOR's FFT.cpp/load_shaders.cpp unchanged,
// transforms a unit impulse, reads the FFT texture back and prints link status of every GLSL program.
// Purpose: find out why the glare PSF is black under Mesa. Writes nothing but stdout.
#include <cstdio>
#include <cmath>
#include <GL/glew.h>
#include <GL/glut.h>
#include "FFT.h"
#include "../SOIL/SOIL.h"
#include <cstring>
#include <cstdlib>
static const int N = 512;
static int input_kind = 0;  // 0 impulse, 1 full-field constant (1,0,0,0) like the app's aperture polygon
static void draw_impulse() {
  if (input_kind == 1) {
    glClearColor(0,0,0,0); glClear(GL_COLOR_BUFFER_BIT);
    glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(-1,1,-1,1,-1,1); glMatrixMode(GL_MODELVIEW); glLoadIdentity();
    glColor4f(1,0,0,0); glBegin(GL_POLYGON); glVertex2f(-0.5f,-0.5f); glVertex2f(0.5f,-0.5f); glVertex2f(0.5f,0.5f); glVertex2f(-0.5f,0.5f); glEnd();
    return;
  }
  glClearColor(0,0,0,0); glClear(GL_COLOR_BUFFER_BIT);
  glMatrixMode(GL_PROJECTION); glLoadIdentity(); glOrtho(0,N,0,N,-1,1); glMatrixMode(GL_MODELVIEW); glLoadIdentity();
  glColor4f(1,0,0,0); glBegin(GL_POLYGON); glVertex2f(5,7); glVertex2f(6,7); glVertex2f(6,8); glVertex2f(5,8); glEnd();
}
int main(int argc, char** argv) {
  glutInit(&argc, argv); glutInitWindowSize(N,N); bool app_mode = argc > 1 && !strcmp(argv[1], "app");
  if (argc > 3) input_kind = atoi(argv[3]);
  glutInitDisplayMode(app_mode ? (GLUT_DOUBLE|GLUT_RGBA|GLUT_DEPTH|GLUT_ALPHA) : (GLUT_DOUBLE|GLUT_RGBA)); glutCreateWindow("probe");
  glewInit();
  printf("GL_VERSION %s\nGL_RENDERER %s\nGLSL %s\n", glGetString(GL_VERSION), glGetString(GL_RENDERER), glGetString(GL_SHADING_LANGUAGE_VERSION));
  glEnable(GL_CULL_FACE);
  if (app_mode) {  // reproduce the app's state before its FFT is built: point smoothing + SOIL rectangle textures
    glEnable(GL_POINT_SMOOTH);
    unsigned t = SOIL_load_OGL_texture(argc > 2 ? argv[2] : "candle.png", SOIL_LOAD_AUTO, SOIL_CREATE_NEW_ID, SOIL_FLAG_INVERT_Y | SOIL_FLAG_TEXTURE_RECTANGLE);
    printf("app mode: SOIL texture %u\n", t);
  }
  FFT fft(N, N); fft.set_input(draw_impulse);
  // input only (no transform) -> read input texture
  fft.do_fft();
  for (unsigned p = 1; p < 20; ++p) if (glIsProgram(p)) {
    GLint ok=0; glGetProgramiv(p, GL_LINK_STATUS, &ok); char log[2048]; GLsizei n=0; glGetProgramInfoLog(p, 2047, &n, log); log[n]=0;
    printf("program %u link=%d %s\n", p, ok, log);
  }
  static float buf[N*N*4];
  glBindTexture(GL_TEXTURE_RECTANGLE_ARB, fft.get_output());
  glGetTexImage(GL_TEXTURE_RECTANGLE_ARB, 0, GL_RGBA, GL_FLOAT, buf);
  double s[4]={0,0,0,0}, mx=0, mn=1e30; int nan=0;
  for (int i=0;i<N*N;++i){ for(int c=0;c<4;++c){ float v=buf[4*i+c]; if(std::isnan(v)) nan++; else s[c]+=fabs(v);} double m=hypot(buf[4*i],buf[4*i+1]); if(m>mx) mx=m; if(m<mn) mn=m; }
  printf("FFT(impulse): mean|R|=%g mean|G|=%g mean|B|=%g mean|A|=%g max|RG|=%g min|RG|=%g nan=%d  (impulse at x=5,y=7: expected |RG|=1 everywhere, i.e. mean|R|~0.64, min|RG|=1)\n", s[0]/N/N, s[1]/N/N, s[2]/N/N, s[3]/N/N, mx, mn, nan);
  printf("input_kind=%d DC=(%g,%g) (expected for kind 1: 65536)\n", input_kind, buf[0], buf[1]);
  printf("samples: [0]=(%g,%g) [1]=(%g,%g) [N*N/2+N/2]=(%g,%g)\n", buf[0],buf[1],buf[4],buf[5],buf[4*(N*N/2+N/2)],buf[4*(N*N/2+N/2)+1]);
  printf("glGetError=0x%x\n", glGetError());
  return 0;
}
