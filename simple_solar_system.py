import pygame
import random
import math
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *

# 初始化
pygame.init()
WIDTH, HEIGHT = 1000, 800
display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)

# OpenGL设置
gluPerspective(45, (WIDTH/HEIGHT), 0.1, 1000.0)
glTranslatef(0, 0, -400)
glEnable(GL_DEPTH_TEST)

# 改进的光照初始化
def init_lighting():
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glLightfv(GL_LIGHT0, GL_POSITION,  (0, 0, 0, 1))  # 光源固定在太阳位置
    glLightfv(GL_LIGHT0, GL_AMBIENT,  (0.2, 0.2, 0.2, 1))
    glLightfv(GL_LIGHT0, GL_DIFFUSE,  (0.8, 0.8, 0.8, 1))
    glLightfv(GL_LIGHT0, GL_SPECULAR, (0.5, 0.5, 0.5, 1))

    glMaterialfv(GL_FRONT, GL_AMBIENT, (0.2, 0.2, 0.2, 1))
    glMaterialfv(GL_FRONT, GL_DIFFUSE, (0.8, 0.8, 0.8, 1))
    glMaterialfv(GL_FRONT, GL_SPECULAR, (0.5, 0.5, 0.5, 1))
    glMaterialf(GL_FRONT, GL_SHININESS, 50)
    
    glColorMaterial(GL_FRONT, GL_AMBIENT_AND_DIFFUSE)
    glEnable(GL_COLOR_MATERIAL)
init_lighting()

# 天体类（带法线生成）
class CelestialBody:
    def __init__(self, distance, radius, color):
        self.distance = distance
        self.radius = radius
        self.color = color
        self.angle = 0
        self.trail = []
        self.max_trail = 50
        self.quad = gluNewQuadric()
        gluQuadricNormals(self.quad, GLU_SMOOTH)  # 生成法线
        
    def update(self, speed):
        self.angle += speed
        x = self.distance * math.cos(math.radians(self.angle))
        z = self.distance * math.sin(math.radians(self.angle))
        self.trail.append((x, 0, z))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)
            
    def draw(self):
        x = self.distance * math.cos(math.radians(self.angle))
        z = self.distance * math.sin(math.radians(self.angle))
        
        glPushMatrix()
        glTranslatef(x, 0, z)
        glColor3fv(self.color)  # 颜色影响材质
        gluSphere(self.quad, self.radius, 32, 32)
        glPopMatrix()
        
    def draw_trail(self):
        if len(self.trail) < 2:
            return
            
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINE_STRIP)
        glColor4f(*self.color, 0.3)
        for pos in self.trail:
            glVertex3fv(pos)
        glEnd()

# 改进的UI类
class UI:
    def __init__(self):
        self.font = pygame.font.SysFont('Microsoft YaHei', 24)
        # # 使用支持中文的字体，尝试多种可能的字体
        # try:
        #     # 尝试使用微软雅黑
        #     self.font = pygame.font.SysFont('Microsoft YaHei', 24)
        # except:
        #     try:
        #         # 尝试使用黑体
        #         self.font = pygame.font.SysFont('SimHei', 24)
        #     except:
        #         try:
        #             # 如果找不到专门的中文字体，尝试使用系统默认字体
        #             self.font = pygame.font.Font(pygame.font.get_default_font(), 24)
        #         except:
        #             # 如果都失败了，回退到Arial
        #             self.font = pygame.font.SysFont('Arial', 24)
        
    def draw_text(self, text, pos):
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, WIDTH, HEIGHT, 0)
        
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # 渲染文字
        text_surface = self.font.render(text, True, (255,255,255,255))
        text_data = pygame.image.tostring(text_surface, "RGBA", True)
        
        # 设置混合
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_LIGHTING)
        
        # 绘制
        glWindowPos2d(pos[0], HEIGHT - pos[1] - 20)
        glDrawPixels(text_surface.get_width(), text_surface.get_height(),
                    GL_RGBA, GL_UNSIGNED_BYTE, text_data)
        
        # 恢复状态
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

# 创建对象
sun = CelestialBody(0, 20, (1,1,0))
earth = CelestialBody(100, 8, (0,0.5,1))
ui = UI()

# 生成星空
stars = [(random.uniform(-500,500), 
         random.uniform(-500,500),
         random.uniform(-500,500)) for _ in range(2000)]

def draw_stars():
    glDisable(GL_LIGHTING)
    glPointSize(1.5)
    glBegin(GL_POINTS)
    for star in stars:
        glColor3f(1,1,1)
        glVertex3fv(star)
    glEnd()

# 主循环
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            quit()

    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # 更新
    earth.update(0.5)
    
    # 绘制
    sun.draw()
    earth.draw()
    earth.draw_trail()
    draw_stars()  # 最后绘制星空
    
    # UI
    ui.draw_text("太阳系模拟", (20, 20))
    ui.draw_text(f"地球轨道角度: {earth.angle:.1f}°", (20, 50))
    
    pygame.display.flip()
    pygame.time.wait(10)