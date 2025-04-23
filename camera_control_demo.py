import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
import numpy as np

class Config:
    WIDTH, HEIGHT = 1000, 800
    BACKGROUND_COLOR = (0.0, 0.0, 0.05, 1.0)
    INIT_CAMERA_DISTANCE = 600

class IntegratedCameraTest:
    def __init__(self):
        pygame.init()
        self._init_opengl()
        self.clock = pygame.time.Clock()
        self._init_camera()
        self._init_debug_objects()

    def _init_opengl(self):
        import sys  # 确保导入sys模块
        glutInit(sys.argv)  # 初始化GLUT
        pygame.display.set_mode((Config.WIDTH, Config.HEIGHT), DOUBLEBUF|OPENGL)
        gluPerspective(45, Config.WIDTH/Config.HEIGHT, 1.0, 5000.0)
        glEnable(GL_DEPTH_TEST)
        glClearColor(*Config.BACKGROUND_COLOR)

    def _init_camera(self):
        # 摄像机参数初始化
        self.camera = {
            'position': [0.0, 0.0, -Config.INIT_CAMERA_DISTANCE],
            'rotation': [30.0, 0.0, 0.0],  # X/Y/Z轴旋转角度
            'zoom': 1.0,
            'drag_speed': 0.2,
            'zoom_speed': 0.1
        }
        self.dragging = False
        self.last_mouse_pos = (0, 0)

    def _init_debug_objects(self):
        # 初始化调试用图形
        self.objects = {
            'cube': {'size': 50, 'color': (1,0,0)},
            'axis': {
                'x': {'length': 100, 'color': (1,0,0)},
                'y': {'length': 100, 'color': (0,1,0)},
                'z': {'length': 100, 'color': (0,0,1)}
            }
        }

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                return False
            
            # 鼠标事件处理
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:  # 左键拖拽
                    self.dragging = True
                    self.last_mouse_pos = event.pos
                elif event.button == 4:  # 滚轮向上
                    self.camera['zoom'] *= (1 + self.camera['zoom_speed'])
                elif event.button == 5:  # 滚轮向下
                    self.camera['zoom'] *= (1 - self.camera['zoom_speed'])
                    
            elif event.type == MOUSEBUTTONUP:
                if event.button == 1:
                    self.dragging = False
                    
            elif event.type == MOUSEMOTION and self.dragging:
                dx = event.pos[0] - self.last_mouse_pos[0]
                dy = event.pos[1] - self.last_mouse_pos[1]
                self.camera['rotation'][1] += dx * self.camera['drag_speed']  # Y轴旋转
                self.camera['rotation'][0] = np.clip(
                    self.camera['rotation'][0] - dy * self.camera['drag_speed'],
                    -89, 89
                )
                self.last_mouse_pos = event.pos

        # 键盘事件处理
        keys = pygame.key.get_pressed()
        move_speed = 5
        if keys[K_w]: self.camera['position'][1] += move_speed
        if keys[K_s]: self.camera['position'][1] -= move_speed
        if keys[K_a]: self.camera['position'][0] -= move_speed
        if keys[K_d]: self.camera['position'][0] += move_speed
        
        return True

    def apply_camera_transform(self):
        glLoadIdentity()
        
        # 应用摄像机位置和缩放
        glTranslatef(
            self.camera['position'][0],
            self.camera['position'][1],
            -Config.INIT_CAMERA_DISTANCE * self.camera['zoom']
        )
        
        # 应用旋转（X->Y->Z顺序）
        glRotatef(self.camera['rotation'][0], 1, 0, 0)  # X轴旋转
        glRotatef(self.camera['rotation'][1], 0, 1, 0)  # Y轴旋转
        glRotatef(self.camera['rotation'][2], 0, 0, 1)  # Z轴旋转

    def draw_cube(self, size):
        """使用OpenGL基础函数绘制线框立方体"""
        size = size / 2  # 半边长
        
        # 定义立方体的8个顶点
        vertices = [
            (-size, -size, -size), (size, -size, -size),
            (size, size, -size), (-size, size, -size),
            (-size, -size, size), (size, -size, size),
            (size, size, size), (-size, size, size)
        ]
        
        # 定义12条边
        edges = [
            (0, 1), (1, 2), (2, 3), (3, 0),  # 底面
            (4, 5), (5, 6), (6, 7), (7, 4),  # 顶面
            (0, 4), (1, 5), (2, 6), (3, 7)   # 连接底面和顶面的边
        ]
        
        # 绘制线框
        glBegin(GL_LINES)
        for edge in edges:
            for vertex in edge:
                glVertex3fv(vertices[vertex])
        glEnd()

    def draw_debug_objects(self):
        # 绘制参考立方体
        glPushMatrix()
        glColor3f(*self.objects['cube']['color'])
        self.draw_cube(self.objects['cube']['size'])  # 使用自定义函数替代glutWireCube
        glPopMatrix()

        # 绘制坐标系
        glBegin(GL_LINES)
        # X轴
        glColor3f(*self.objects['axis']['x']['color'])
        glVertex3f(0,0,0)
        glVertex3f(self.objects['axis']['x']['length'],0,0)
        # Y轴
        glColor3f(*self.objects['axis']['y']['color'])
        glVertex3f(0,0,0)
        glVertex3f(0,self.objects['axis']['y']['length'],0)
        # Z轴
        glColor3f(*self.objects['axis']['z']['color'])
        glVertex3f(0,0,0)
        glVertex3f(0,0,self.objects['axis']['z']['length'])
        glEnd()

    def run(self):
        while True:
            if not self.handle_events():
                return

            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            # 应用摄像机变换
            self.apply_camera_transform()
            
            # 绘制调试对象
            self.draw_debug_objects()
            
            pygame.display.flip()
            self.clock.tick(60)

if __name__ == "__main__":
    IntegratedCameraTest().run()