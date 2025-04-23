import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

def main():
    # 初始化Pygame
    pygame.init()
    
    # 设置显示模式
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF|OPENGL)
    pygame.display.set_caption("OpenGL基本测试")

    # 设置透视投影
    gluPerspective(45, (display[0]/display[1]), 0.1, 50.0)
    glTranslatef(0.0, 0.0, -5)  # 将观察点向后移动

    # 启用深度测试
    glEnable(GL_DEPTH_TEST)

    # 立方体顶点和面定义
    vertices = [
        [1, -1, -1],    # 0
        [1, 1, -1],     # 1
        [-1, 1, -1],    # 2
        [-1, -1, -1],   # 3
        [1, -1, 1],     # 4
        [1, 1, 1],      # 5
        [-1, -1, 1],    # 6
        [-1, 1, 1]      # 7
    ]

    surfaces = [
        (0,1,2,3),  # 前面
        (4,5,7,6),  # 后面
        (0,4,6,3),  # 左面
        (1,5,4,0),  # 右面
        (2,7,5,1),  # 顶面
        (3,6,7,2)   # 底面
    ]

    colors = [
        (1,0,0),  # 红
        (0,1,0),  # 绿
        (0,0,1),  # 蓝
        (1,1,0),  # 黄
        (1,0,1),  # 紫
        (0,1,1)   # 青
    ]

    rotation = [0, 0, 0]  # 旋转角度

    # 主循环
    while True:
        # 事件处理
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                quit()

        # 清空缓冲区
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)

        # 旋转立方体
        rotation[0] += 1
        rotation[1] += 1
        glRotatef(1, 3, 1, 1)

        # 绘制立方体
        glBegin(GL_QUADS)
        for i, surface in enumerate(surfaces):
            glColor3fv(colors[i])
            for vertex in surface:
                glVertex3fv(vertices[vertex])
        glEnd()

        # 更新显示
        pygame.display.flip()
        pygame.time.wait(10)

if __name__ == "__main__":
    main()