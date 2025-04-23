import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np
import os
import sys

# 常量定义
WIDTH, HEIGHT = 1000, 800
FPS = 60
MAX_TRAIL_LENGTH = 300  # 减少轨迹点数量提高性能

# 颜色定义 (R, G, B) - 增强颜色对比度
YELLOW = (1.0, 1.0, 0.0)       # 太阳
BLUE = (0.1, 0.4, 0.9)         # 地球
RED = (0.9, 0.2, 0.2)          # 火星
ORANGE = (1.0, 0.65, 0.0)      # 金星
GREY = (0.6, 0.6, 0.6)         # 水星
WHITE = (1.0, 1.0, 1.0)
GREEN = (0.0, 0.8, 0.2)
PURPLE = (0.5, 0.0, 0.5)
BLACK = (0.0, 0.0, 0.0)
SATURN_COLOR = (0.9, 0.8, 0.5) # 土星
JUPITER_COLOR = (0.9, 0.7, 0.4) # 木星

# 引力常数 G
G = 6.67e-11

class Camera:
    """摄像机类，管理视角和移动"""
    def __init__(self):
        self.position = [0.0, 0.0, -600.0]  # 调整到更远的位置，原来是-200.0
        self.rotation = [30.0, 0.0, 0.0]    # 默认倾斜30度，能看到更多行星
        self.zoom_level = 1.0
        self.dragging = False
        self.last_mouse_pos = (0, 0)
        
    def apply(self):
        """应用摄像机视角"""
        glLoadIdentity()
        glTranslatef(*self.position)
        glTranslatef(0, 0, 200 * (1 - self.zoom_level))  # 缩放效果
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)
    
    def rotate(self, x=0, y=0, z=0):
        """旋转摄像机"""
        self.rotation[0] += x
        self.rotation[1] += y
        self.rotation[2] += z
    
    def zoom(self, amount):
        """缩放视图"""
        self.zoom_level = max(0.1, min(3.0, self.zoom_level + amount))
    
    def start_drag(self, mouse_pos):
        """开始拖拽视角"""
        self.dragging = True
        self.last_mouse_pos = mouse_pos
    
    def end_drag(self):
        """结束拖拽视角"""
        self.dragging = False
    
    def drag(self, mouse_pos):
        """拖拽视角"""
        if self.dragging:
            dx = mouse_pos[0] - self.last_mouse_pos[0]
            dy = mouse_pos[1] - self.last_mouse_pos[1]
            self.rotate(x=dy * 0.1, y=dx * 0.1)
            self.last_mouse_pos = mouse_pos

# 天体类
class CelestialBody:
    def __init__(self, distance_from_sun, radius, color, mass=1.0, 
                 orbital_speed=1.0, inclination=0.0, name=""):
        self.distance = distance_from_sun
        self.radius = radius
        self.color = color
        self.mass = mass
        self.orbital_speed = orbital_speed
        self.inclination = inclination * math.pi / 180  # 转换为弧度
        self.angle = 0
        self.name = name
        self.x = distance_from_sun
        self.y = 0.0
        self.z = 0.0
        # 使用NumPy数组存储轨迹点以提高性能
        self.trail = np.zeros((MAX_TRAIL_LENGTH, 3), dtype=np.float32)
        self.trail_index = 0
        self.trail_count = 0
        self.max_trail_length = MAX_TRAIL_LENGTH
        self.quadratic = gluNewQuadric()
        gluQuadricNormals(self.quadratic, GLU_SMOOTH)
        # 添加自转属性
        self.rotation_angle = 0

    def update_position(self, dt):
        """更新天体位置"""
        # 更新轨道角度
        self.angle += self.orbital_speed * dt
        
        # 计算新的位置（考虑轨道倾角）
        self.x = self.distance * math.cos(self.angle)
        self.y = self.distance * math.sin(self.angle) * math.cos(self.inclination)
        self.z = self.distance * math.sin(self.angle) * math.sin(self.inclination)
        
        # 更新自转角度
        self.rotation_angle += dt * 10  # 自转速度
        
        # 更新轨迹点
        idx = self.trail_index % self.max_trail_length
        self.trail[idx] = [self.x, self.y, self.z]
        self.trail_index += 1
        self.trail_count = min(self.trail_count + 1, self.max_trail_length)

    def draw(self, show_names=True, font=None, surface=None):
        """绘制天体"""
        glPushMatrix()
        
        # 移动到天体位置
        glTranslatef(self.x, self.y, self.z)
        
        # 添加自转
        glRotatef(self.rotation_angle, 0, 1, 0)  # 添加绕Y轴自转
        
        # 设置颜色 - 增加颜色强度
        r, g, b = self.color
        glColor3f(min(1.0, r*1.5), min(1.0, g*1.5), min(1.0, b*1.5))  # 提高亮度
        
        # 绘制天体 - 增加细分数
        gluSphere(self.quadratic, self.radius, 24, 24)
        
        glPopMatrix()
        
        # 绘制轨道轨迹 - 使用更亮的颜色
        if len(self.trail) > 2:
            glDisable(GL_LIGHTING)  # 轨迹不需要光照效果
            glLineWidth(2.0)  # 增加线宽
            glBegin(GL_LINE_STRIP)
            for i, pos in enumerate(self.trail):
                alpha = i / len(self.trail)
                # 更亮的轨迹颜色
                glColor4f(min(1.0, self.color[0]*1.5), 
                         min(1.0, self.color[1]*1.5), 
                         min(1.0, self.color[2]*1.5), 
                         alpha)
                glVertex3f(*pos)
            glEnd()
            glLineWidth(1.0)
            glEnable(GL_LIGHTING)  # 恢复光照

class SolarSystem:
    """太阳系类，管理所有天体"""
    def __init__(self):
        # 创建太阳和行星（不使用纹理）
        self.sun = CelestialBody(0, 20, YELLOW, mass=1.989e30, name="太阳")
        
        self.planets = [
            # 水星: 距离、半径、颜色、质量、公转速度、轨道倾角、名称
            CelestialBody(70, 3, GREY, mass=3.3e23, orbital_speed=0.02, 
                         inclination=7.0, name="水星"),
            # 金星
            CelestialBody(100, 6, ORANGE, mass=4.87e24, orbital_speed=0.015, 
                         inclination=3.4, name="金星"),
            # 地球
            CelestialBody(150, 7, BLUE, mass=5.97e24, orbital_speed=0.01, 
                         inclination=0.0, name="地球"),
            # 火星
            CelestialBody(200, 5, RED, mass=6.42e23, orbital_speed=0.008, 
                         inclination=1.8, name="火星"),
            # 木星
            CelestialBody(280, 15, JUPITER_COLOR, mass=1.898e27, orbital_speed=0.004, 
                         inclination=1.3, name="木星"),
            # 土星
            CelestialBody(400, 12, SATURN_COLOR, mass=5.683e26, orbital_speed=0.003, 
                         inclination=2.5, name="土星"),
        ]
        
        # 是否显示行星名称
        self.show_names = True
        
        # 是否显示轨道线
        self.show_orbits = True
        
        # 动态调整摄像机位置适应最远行星
        max_distance = max(p.distance for p in self.planets)
        self.recommended_camera_distance = -max_distance * 1.5
    
    def update(self, dt, paused=False):
        """更新所有天体位置"""
        if not paused:
            for planet in self.planets:
                planet.update_position(dt)
    
    def draw(self, font=None, surface=None):
        """绘制太阳系"""
        # 设置光源位置（在太阳位置）
        light_position = [0.0, 0.0, 0.0, 1.0]
        glLightfv(GL_LIGHT0, GL_POSITION, light_position)
        
        # 绘制太阳
        self.sun.draw(self.show_names, font, surface)
        
        # 绘制轨道线
        if self.show_orbits:
            self.draw_orbit_lines()
        
        # 绘制行星
        for planet in self.planets:
            planet.draw(self.show_names, font, surface)
    
    def draw_orbit_lines(self):
        """绘制轨道线"""
        glDisable(GL_LIGHTING)  # 轨道线不需要光照
        glEnable(GL_LINE_SMOOTH)
        glLineWidth(1.0)
        
        for planet in self.planets:
            glBegin(GL_LINE_LOOP)
            for i in range(100):
                angle = 2.0 * math.pi * i / 100
                # 使用与天体实际位置相同的计算逻辑，考虑轨道倾角
                x = planet.distance * math.cos(angle)
                y = planet.distance * math.sin(angle) * math.cos(planet.inclination)
                z = planet.distance * math.sin(angle) * math.sin(planet.inclination)
                glVertex3f(x, y, z)
            glEnd()
        
        glDisable(GL_LINE_SMOOTH)
        glEnable(GL_LIGHTING)  # 恢复光照设置

class UserInterface:
    """用户界面类，处理UI渲染"""
    def __init__(self, width, height):
        self.width = width
        self.height = height
        self.font = pygame.font.SysFont(None, 24)
        self.large_font = pygame.font.SysFont(None, 36)
        
    def draw_text(self, surface, text, x, y, color=(255, 255, 255)):
        """绘制文本"""
        text_surface = self.font.render(text, True, color)
        surface.blit(text_surface, (x, y))
        
    def draw_large_text(self, surface, text, x, y, color=(255, 255, 255)):
        """绘制大字体文本"""
        text_surface = self.large_font.render(text, True, color)
        surface.blit(text_surface, (x, y))
    
    def render_info(self, surface, dt, paused, camera):
        """渲染信息面板"""
        # 切换回2D模式
        self.setup_2d_mode()
        
        # 创建半透明背景面板
        panel_surface = pygame.Surface((300, 230), pygame.SRCALPHA)
        panel_surface.fill((0, 0, 0, 150))
        surface.blit(panel_surface, (10, 10))
        
        # 绘制信息文本
        info_text = [
            f"时间步长: {dt:.2f}",
            f"缩放: {camera.zoom_level:.1f}x",
            f"状态: {'暂停' if paused else '运行'}",
            "",
            "--- 控制 ---",
            "空格: 暂停/继续",
            "I: 显示/隐藏信息",
            "O: 显示/隐藏轨道",
            "N: 显示/隐藏名称",
            "方向键: 旋转视图",
            "Ctrl+上下: 上下旋转",
            "Q/E: Z轴旋转",
            "鼠标滚轮: 缩放",
            "+/-: 调整时间步长",
            "鼠标拖拽: 旋转视角"
        ]
        
        for i, text in enumerate(info_text):
            self.draw_text(surface, text, 20, 20 + i * 25)
            
        # 恢复3D模式
        self.restore_3d_mode()
    
    def render_planet_names(self, surface, solar_system, camera):
        """渲染行星名称"""
        # 需要切换回2D模式
        self.setup_2d_mode()
        
        # 获取当前视图和投影矩阵
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        # 绘制太阳名称
        self.draw_planet_name(surface, solar_system.sun, modelview, projection, viewport)
        
        # 绘制行星名称
        for planet in solar_system.planets:
            self.draw_planet_name(surface, planet, modelview, projection, viewport)
        
        # 恢复3D模式
        self.restore_3d_mode()
    
    def draw_planet_name(self, surface, planet, modelview, projection, viewport):
        """在行星上方绘制名称"""
        # 将3D坐标转换为屏幕坐标
        win_coords = gluProject(planet.x, planet.y, planet.z, modelview, projection, viewport)
        
        if win_coords:
            x, y, z = win_coords
            # 只有当z值在0-1范围内（在视野内）时才绘制
            if 0.0 <= z <= 1.0 and 0 <= x <= self.width and 0 <= y <= self.height:
                # 计算适当的偏移量，使文本出现在行星上方
                offset = planet.radius * 15 / max(1, z)
                self.draw_text(surface, planet.name, int(x) - 20, int(self.height - y) - offset)
    
    def setup_2d_mode(self):
        """切换到2D模式"""
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, self.width, self.height, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glDisable(GL_DEPTH_TEST)
    
    def restore_3d_mode(self):
        """恢复3D模式"""
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()
    
    def render_help_screen(self, surface):
        """渲染帮助屏幕"""
        self.setup_2d_mode()
        
        # 创建半透明背景
        help_surface = pygame.Surface((self.width - 100, self.height - 100), pygame.SRCALPHA)
        help_surface.fill((0, 0, 0, 200))
        surface.blit(help_surface, (50, 50))
        
        # 绘制标题
        self.draw_large_text(surface, "太阳系模拟 - 帮助", 60, 60)
        
        # 绘制帮助内容
        help_text = [
            "基本控制:",
            "  方向键: 旋转视图",
            "  Ctrl+方向键上下: 上下旋转视图",
            "  Q/E: Z轴旋转",
            "  鼠标滚轮: 缩放视图",
            "  空格: 暂停/继续模拟",
            "",
            "显示选项:",
            "  I: 显示/隐藏信息面板",
            "  O: 显示/隐藏轨道线",
            "  N: 显示/隐藏行星名称",
            "  H: 显示/隐藏此帮助页面",
            "",
            "模拟控制:",
            "  +: 增加时间步长",
            "  -: 减少时间步长",
            "  R: 重置视图",
            "",
            "按任意键关闭此帮助页面"
        ]
        
        for i, text in enumerate(help_text):
            self.draw_text(surface, text, 60, 100 + i * 25)
        
        self.restore_3d_mode()

def draw_starfield(stars, frame_count):
    """绘制星空背景，并随时间缓慢旋转"""
    glDisable(GL_LIGHTING)
    glPushMatrix()
    
    # 使星空随时间缓慢旋转
    glRotatef(frame_count * 0.01, 0, 1, 0)  # 绕Y轴缓慢旋转
    
    glColor3f(1.0, 1.0, 1.0)  # 纯白色
    glPointSize(2.0)  # 增加点大小
    
    glBegin(GL_POINTS)
    for x, y, z in stars:
        glVertex3f(x, y, z)
    glEnd()
    
    glPopMatrix()
    glEnable(GL_LIGHTING)

def main():
    """主函数"""
    # 初始化Pygame和OpenGL
    pygame.init()
    
    # 设置OpenGL属性
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 1)
    pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 4)
    pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
    
    display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
    pygame.display.set_caption("太阳系模拟 - 3D增强版")
    
    # 设置视角 - 增加远裁剪面和近裁剪面
    gluPerspective(45, (WIDTH / HEIGHT), 1.0, 5000.0)  # 远裁剪面从2000.0改为5000.0
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    
    # 关闭纹理（确保不会尝试使用不存在的纹理）
    glDisable(GL_TEXTURE_2D)
    
    # 增强光照设置
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    light_ambient = [0.6, 0.6, 0.6, 1.0]  # 进一步增强环境光
    light_diffuse = [1.0, 1.0, 1.0, 1.0]  # 最亮的漫反射光
    light_specular = [1.0, 1.0, 1.0, 1.0]
    light_position = [0.0, 0.0, 0.0, 1.0]  # 光源位置在太阳处
    
    glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
    glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
    glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
    glLightfv(GL_LIGHT0, GL_POSITION, light_position)
    
    print("初始化OpenGL完成")
    
    print("初始化太阳系...")
    # 创建对象
    solar_system = SolarSystem()
    ui = UserInterface(WIDTH, HEIGHT)
    camera = Camera()
    
    # 游戏变量
    clock = pygame.time.Clock()
    dt = 1.0
    paused = False
    show_info = True
    show_help = False
    
    # 生成星星数据（只生成一次）
    stars = []
    for _ in range(2000):  # 增加星星数量
        distance = 900
        theta = 2 * math.pi * np.random.random()
        phi = math.acos(2 * np.random.random() - 1)
        x = distance * math.sin(phi) * math.cos(theta)
        y = distance * math.sin(phi) * math.sin(theta)
        z = distance * math.cos(phi)
        stars.append((x, y, z))
    
    print("初始化完成，开始渲染循环")
    running = True
    frame_count = 0
    while running:
        frame_count += 1
        if frame_count % 100 == 0:  # 每100帧输出一次
            print(f"已渲染 {frame_count} 帧")
            
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    paused = not paused
                elif event.key == pygame.K_i:
                    show_info = not show_info
                elif event.key == pygame.K_o:
                    solar_system.show_orbits = not solar_system.show_orbits
                elif event.key == pygame.K_n:
                    solar_system.show_names = not solar_system.show_names
                elif event.key == pygame.K_h:
                    show_help = not show_help
                elif event.key == pygame.K_r:
                    camera = Camera()  # 重置视图
                elif event.key == pygame.K_PLUS or event.key == pygame.K_KP_PLUS:
                    dt *= 1.2
                elif event.key == pygame.K_MINUS or event.key == pygame.K_KP_MINUS:
                    dt /= 1.2
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:  # 滚轮向上
                    camera.zoom(0.1)
                elif event.button == 5:  # 滚轮向下
                    camera.zoom(-0.1)
                elif event.button == 1:  # 左键按下
                    camera.start_drag(event.pos)
            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:  # 左键松开
                    camera.end_drag()
            elif event.type == pygame.MOUSEMOTION:
                camera.drag(event.pos)

        # 处理连续按键
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            camera.rotate(y=-1)
        if keys[pygame.K_RIGHT]:
            camera.rotate(y=1)
        if keys[pygame.K_UP] and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
            camera.rotate(x=-1)
        elif keys[pygame.K_UP]:  # 如果没有按Ctrl，则向前移动
            camera.position[2] += 5
        if keys[pygame.K_DOWN] and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
            camera.rotate(x=1)
        elif keys[pygame.K_DOWN]:  # 如果没有按Ctrl，则向后移动
            camera.position[2] -= 5
        if keys[pygame.K_q]:
            camera.rotate(z=1)
        if keys[pygame.K_e]:
            camera.rotate(z=-1)

        # 清空缓冲区
        glClearColor(0.0, 0.0, 0.05, 1.0)  # 深蓝色背景
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        
        # 应用摄像机
        camera.apply()
        if frame_count == 1:  # 只在第一帧输出
            print(f"摄像机位置: {camera.position}")
            print(f"摄像机旋转: {camera.rotation}")
            print(f"太阳位置: 0,0,0")
            print(f"地球位置: {solar_system.planets[2].x}, {solar_system.planets[2].y}, {solar_system.planets[2].z}")

        # 绘制星空背景
        draw_starfield(stars, frame_count)

        # 更新并绘制太阳系
        solar_system.update(dt, paused)
        solar_system.draw(ui.font, pygame.display.get_surface())
        
        # 绘制UI
        if solar_system.show_names:
            ui.render_planet_names(pygame.display.get_surface(), solar_system, camera)
            
        if show_info:
            ui.render_info(pygame.display.get_surface(), dt, paused, camera)
            
        if show_help:
            ui.render_help_screen(pygame.display.get_surface())

        # 更新显示
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


try:
    display = pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
except pygame.error as e:
    print("OpenGL初始化失败:", e)
    pygame.quit()
    sys.exit(1)



if __name__ == "__main__":
    main()