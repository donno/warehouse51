/*
 *  Typer
 *      A simpletyping tester.
 *      In no way should this be used for determine if someone is has superior
 *      typing skills then another and should not be used for hiring a person
 *      based on there score.
 */

/*
    Copyright (c) 2007 Sean Donnellan

    Permission is hereby granted, free of charge, to any person obtaining a copy
    of this software and associated documentation files (the "Software"), to deal
    in the Software without restriction, including without limitation the rights
    to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
    copies of the Software, and to permit persons to whom the Software is
    furnished to do so, subject to the following conditions:

    The above copyright notice and this permission notice shall be included in
    all copies or substantial portions of the Software.

    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
    THE SOFTWARE.
 **/



#include <windows.h>

#define IDC_MAIN_EDIT   101
#define IDC_MAIN_BUTTON 102

HWND hwnd;  /*  Main window handle */
HWND hEdit; 
const char g_szClassName[] = "Typer 0.1";

int keyIndex = 0;

void GenerateKey(HWND hwnd) {
    SetDlgItemText(hwnd, IDC_MAIN_EDIT, "Hello");
};

LRESULT CALLBACK WndProc(HWND hwnd, UINT msg, WPARAM wParam, LPARAM lParam) {
    
    switch(msg) {
        case WM_COMMAND:
            switch(LOWORD(wParam)) {
                case IDC_MAIN_BUTTON:
                    GenerateKey(hwnd);
                    break;
            }
            break;
        case WM_CLOSE:
            DestroyWindow(hwnd);
            break;
        case WM_DESTROY:
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hwnd, msg, wParam, lParam);
    }
    return 0;
};

HWND windowCreate(HINSTANCE hInst, int nCmdShow, int width, int height) {
    HWND hwnd;
    WNDCLASSEX wc;
    wc.cbSize        = sizeof(WNDCLASSEX);
    wc.style         = 0;
    wc.cbClsExtra    = wc.cbWndExtra = 0;
    wc.hInstance     = hInst;
    wc.hCursor       = LoadCursor(NULL, IDC_ARROW);
    wc.hIcon         = LoadIcon(NULL, IDI_APPLICATION);
    wc.hbrBackground = (HBRUSH)(COLOR_WINDOW+1);
    wc.lpszMenuName  = NULL;
    wc.lpszClassName = g_szClassName;
    wc.lpfnWndProc   = WndProc;
    wc.hIconSm       = LoadIcon(NULL, IDI_APPLICATION);

    if(!RegisterClassEx(&wc)) {
        MessageBox(NULL, "Window Registration Failed!", "Error!", MB_ICONEXCLAMATION | MB_OK);
        return 0;
    }

    hwnd = CreateWindowEx( WS_EX_CLIENTEDGE, g_szClassName, g_szClassName,
        WS_OVERLAPPEDWINDOW - (WS_MINIMIZEBOX | WS_MAXIMIZEBOX | WS_THICKFRAME), CW_USEDEFAULT, CW_USEDEFAULT, width, height, NULL, NULL, hInst, NULL);
    if(hwnd == NULL) {
        MessageBox(NULL, "Window Creation Failed!", "Error!", MB_ICONEXCLAMATION | MB_OK);
        return 0;
    }

    return hwnd;
};

int WINAPI WinMain(HINSTANCE hInst, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    MSG Msg;
    HWND hButt;
    HWND hwnd = windowCreate(hInst, nCmdShow, 300, 96);

    hEdit = CreateWindowEx(WS_EX_CLIENTEDGE, "EDIT", "", WS_CHILD | WS_VISIBLE, 0, 0, 300-10, 30, hwnd, (HMENU)IDC_MAIN_EDIT, GetModuleHandle(NULL), NULL);
    hButt = CreateWindowEx(0, "BUTTON", "Generate", WS_CHILD|WS_VISIBLE, 0,30,300-10,30, hwnd,(HMENU)IDC_MAIN_BUTTON,NULL,0);
    ShowWindow(hwnd, nCmdShow);
    UpdateWindow(hwnd);
    
    SetDlgItemText(hwnd, IDC_MAIN_EDIT, "Hey");
    while(GetMessage(&Msg, NULL, 0, 0) > 0) {
        TranslateMessage(&Msg);
        DispatchMessage(&Msg);
    }
    return Msg.wParam;
}

