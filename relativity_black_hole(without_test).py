import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

# 初始化Pygame和OpenGL
pygame.init()

# 设置显示尺寸
WIDTH, HEIGHT = 1000, 800
pygame.display.set_mode((WIDTH, HEIGHT), DOUBLEBUF | OPENGL)
pygame.display.set_caption("相对论太阳系模拟 - 黑洞效应")

# 设置视角
gluPerspective(45, (WIDTH / HEIGHT), 0.1, 2000.0)
glTranslatef(0.0, 0.0, -750)
glEnable(GL_DEPTH_TEST)
glEnable(GL_BLEND)
glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

# 颜色定义 (R, G, B, A)
YELLOW = (1.0, 1.0, 0.0, 1.0)
BLUE = (0.0, 0.2, 1.0, 1.0)
RED = (1.0, 0.0, 0.0, 1.0)
ORANGE = (1.0, 0.65, 0.0, 1.0)
GREY = (0.5, 0.5, 0.5, 1.0)
WHITE = (1.0, 1.0, 1.0, 1.0)
BLACK_HOLE = (0.0, 0.0, 0.0, 1.0)
BLACK_HOLE_ACCRETION = (0.5, 0.0, 0.5, 0.7)

# 创建球体
def create_sphere(radius, slices, stacks):
    quad = gluNewQuadric()
    gluQuadricTexture(quad, GL_TRUE)
    gluSphere(quad, radius, slices, stacks)
    return quad

# 创建时空网格
def create_spacetime_grid(size, divisions, center_mass=0):
    # 网格顶点
    vertices = []
    # 默认扁平网格
    for i in range(divisions + 1):
        for j in range(divisions + 1):
            x = size * (2.0 * i / divisions - 1.0)
            z = size * (2.0 * j / divisions - 1.0)
            y = 0
            
            # 如果有中心质量，应用广义相对论的时空弯曲效应
            if center_mass > 0:
                # 计算到中心的距离
                distance = math.sqrt(x*x + z*z)
                # 避免除以零
                if distance < 1:
                    distance = 1
                    
                # 计算引力势能 (应用Schwarzschild度规的简化形式)
                schwarzschild_radius = 2 * G * center_mass / (c * c) * 1e10  # 缩放以便可见
                if distance > schwarzschild_radius:
                    # 时空弯曲公式：y = -k * M / r
                    y = -schwarzschild_radius * 10 / distance
                else:
                    # 黑洞内部，强烈弯曲
                    y = -10  # 锁定为固定深度，表示事件视界
            
            vertices.append((x, y, z))
    
    return vertices

# 绘制时空网格
def draw_spacetime_grid(vertices, divisions):
    glColor4f(0.3, 0.3, 0.8, 0.3)  # 半透明蓝色
    glLineWidth(1.0)
    
    # 绘制经线
    for i in range(divisions + 1):
        glBegin(GL_LINE_STRIP)
        for j in range(divisions + 1):
            idx = i * (divisions + 1) + j
            glVertex3f(*vertices[idx])
        glEnd()
    
    # 绘制纬线
    for j in range(divisions + 1):
        glBegin(GL_LINE_STRIP)
        for i in range(divisions + 1):
            idx = i * (divisions + 1) + j
            glVertex3f(*vertices[idx])
        glEnd()

# 绘制黑洞吸积盘
def draw_accretion_disk(radius, inner_radius, height):
    glColor4f(*BLACK_HOLE_ACCRETION)
    
    # 绘制吸积盘（基本上是一个圆环）
    slices = 50
    loops = 20
    
    for r in range(loops):
        r_outer = inner_radius + (radius - inner_radius) * (r + 1) / loops
        r_inner = inner_radius + (radius - inner_radius) * r / loops
        
        glBegin(GL_QUAD_STRIP)
        for i in range(slices + 1):
            angle = 2.0 * math.pi * i / slices
            x_outer = r_outer * math.cos(angle)
            z_outer = r_outer * math.sin(angle)
            
            x_inner = r_inner * math.cos(angle)
            z_inner = r_inner * math.sin(angle)
            
            # 对吸积盘上色，内部偏红，外部偏蓝
            inner_color = (1.0, 0.2 * r / loops, 0.1, 0.8)
            outer_color = (0.5 - 0.5 * r / loops, 0.2, 1.0, 0.7)
            
            glColor4f(*inner_color)
            glVertex3f(x_inner, height/2.0, z_inner)
            glColor4f(*outer_color)
            glVertex3f(x_outer, height/2.0, z_outer)
        glEnd()

# 天体类
class CelestialBody:
    def __init__(self, distance_from_center, radius, color, mass=1.0, 
                 initial_velocity=(0,0,0), name=""):
        self.distance = distance_from_center
        self.radius = radius
        self.color = color
        self.mass = mass
        self.name = name
        self.angle = 0
        
        # 位置和速度变量
        self.x = distance_from_center
        self.y = 0.0
        self.z = 0.0
        self.vx, self.vy, self.vz = initial_velocity
        
        # 轨迹
        self.trail = []
        self.max_trail_length = 1000
        self.quadratic = create_sphere(radius, 32, 32)
        
        # 相对论效应 - 水星近日点进动效应
        self.perihelion_shift = 0
        
    def calculate_gravity(self, other_body, dt):
        dx = other_body.x - self.x
        dy = other_body.y - self.y
        dz = other_body.z - self.z
        
        # 距离
        distance = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # 避免零距离
        if distance < 0.1:
            return 0, 0, 0
            
        # 牛顿引力
        force = G * self.mass * other_body.mass / (distance * distance)
        
        # 如果是黑洞，添加相对论修正
        if other_body.name == "黑洞":
            # 广义相对论修正：在强引力场下引力增强
            schwarzschild_radius = 2 * G * other_body.mass / (c * c)
            relativistic_factor = 1 + 3 * schwarzschild_radius / distance
            force *= relativistic_factor
            
            # 记录水星的近日点进动（仅适用于接近黑洞的天体）
            if distance < 1.5 * other_body.radius and self.name != "光子":
                # 近日点进动效应，随着距离黑洞更近而增加
                self.perihelion_shift += 0.01 * dt / distance
        
        # 计算力的方向
        fx = force * dx / distance
        fy = force * dy / distance
        fz = force * dz / distance
        
        return fx, fy, fz
    
    def update_velocity(self, fx, fy, fz, dt):
        # 牛顿第二定律：F = ma，所以 a = F/m
        ax = fx / self.mass
        ay = fy / self.mass
        az = fz / self.mass
        
        # 更新速度
        self.vx += ax * dt
        self.vy += ay * dt
        self.vz += az * dt
    
    def update_position(self, dt):
        # 更新位置
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.z += self.vz * dt
        
        # 记录轨迹
        if len(self.trail) >= self.max_trail_length:
            self.trail.pop(0)
        self.trail.append((self.x, self.y, self.z))
    
    def draw(self):
        glPushMatrix()
        
        # 移动到天体位置
        glTranslatef(self.x, self.y, self.z)
        
        # 设置颜色并绘制天体
        glColor4f(*self.color)
        
        # 如果是黑洞，绘制特殊效果
        if self.name == "黑洞":
            # 黑洞事件视界
            gluSphere(self.quadratic, self.radius, 32, 32)
            
            # 吸积盘（仅在黑洞周围）
            glPopMatrix()  # 退出当前矩阵
            draw_accretion_disk(self.radius * 4, self.radius, 5)
        else:
            # 普通天体
            gluSphere(self.quadratic, self.radius, 32, 32)
            glPopMatrix()
        
        # 绘制轨道轨迹
        if len(self.trail) > 2:
            glColor4f(*self.color)
            glBegin(GL_LINE_STRIP)
            for pos in self.trail:
                glVertex3f(*pos)
            glEnd()

# 物理常量
G = 6.67e-11 * 1e8  # 引力常数（缩放）
c = 3e8 / 1e6  # 光速（缩放）

# 创建中心黑洞和行星
black_hole = CelestialBody(0, 30, BLACK_HOLE, mass=1e31, name="黑洞")

planets = [
    # 水星: 距离、半径、颜色、质量、初始速度、名称
    CelestialBody(120, 4, GREY, mass=3.3e23, initial_velocity=(0, 0, 2.0), name="水星"),
    # 金星
    CelestialBody(180, 8, ORANGE, mass=4.87e24, initial_velocity=(0, 0, 1.6), name="金星"),
    # 地球
    CelestialBody(250, 9, BLUE, mass=5.97e24, initial_velocity=(0, 0, 1.3), name="地球"),
    # 火星
    CelestialBody(320, 6, RED, mass=6.42e23, initial_velocity=(0, 0, 1.1), name="火星"),
]

# 添加一些光子以展示光线弯曲
photons = []
for i in range(15):
    angle = i * math.pi / 7
    dist = 400
    px = dist * math.cos(angle)
    pz = dist * math.sin(angle)
    
    # 光子的初始速度指向黑洞（接近但不是完全指向，以展示弯曲效果）
    vx = -px / 100
    vz = -pz / 100
    
    # 添加一点随机性
    vx += np.random.uniform(-0.1, 0.1)
    vz += np.random.uniform(-0.1, 0.1)
    
    photon = CelestialBody(0, 1, WHITE, mass=1e-10, 
                        initial_velocity=(vx, 0, vz), name="光子")
    photon.x = px
    photon.z = pz
    photons.append(photon)

# 旋转变量
rotation_x = 0
rotation_y = 0
rotation_z = 0

# 游戏主循环
clock = pygame.time.Clock()
dt = 0.5
paused = False
show_info = True
font = pygame.font.SysFont(None, 24)

# 生成时空网格（初始扁平）
grid_size = 400
grid_divisions = 20
spacetime_grid = create_spacetime_grid(grid_size, grid_divisions)

# 绘制文本的函数
def draw_text(surface, text, x, y, color=(255, 255, 255)):
    text_surface = font.render(text, True, color)
    surface.blit(text_surface, (x, y))

running = True
show_grid = True
warp_spacetime = False
simulation_time = 0

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                paused = not paused
            elif event.key == pygame.K_i:
                show_info = not show_info
            elif event.key == pygame.K_g:
                show_grid = not show_grid
            elif event.key == pygame.K_w:
                warp_spacetime = not warp_spacetime
                if warp_spacetime:
                    # 扭曲时空网格
                    spacetime_grid = create_spacetime_grid(grid_size, grid_divisions, black_hole.mass)
                else:
                    # 平坦时空网格
                    spacetime_grid = create_spacetime_grid(grid_size, grid_divisions)
            elif event.key == pygame.K_UP:
                dt *= 1.2
            elif event.key == pygame.K_DOWN:
                dt /= 1.2
            elif event.key == pygame.K_r:
                # 重置光子
                photons.clear()
                for i in range(15):
                    angle = i * math.pi / 7
                    dist = 400
                    px = dist * math.cos(angle)
                    pz = dist * math.sin(angle)
                    
                    vx = -px / 100
                    vz = -pz / 100
                    
                    vx += np.random.uniform(-0.1, 0.1)
                    vz += np.random.uniform(-0.1, 0.1)
                    
                    photon = CelestialBody(0, 1, WHITE, mass=1e-10, 
                                       initial_velocity=(vx, 0, vz), name="光子")
                    photon.x = px
                    photon.z = pz
                    photons.append(photon)

    # 处理连续按键
    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]:
        rotation_y -= 1
    if keys[pygame.K_RIGHT]:
        rotation_y += 1
    if keys[pygame.K_UP] and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
        rotation_x -= 1
    if keys[pygame.K_DOWN] and (keys[pygame.K_LCTRL] or keys[pygame.K_RCTRL]):
        rotation_x += 1
    if keys[pygame.K_q]:
        rotation_z += 1
    if keys[pygame.K_e]:
        rotation_z -= 1

    # 清空缓冲区
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    
    # 重置模型视图矩阵
    glLoadIdentity()
    glTranslatef(0.0, 0.0, -750)
    
    # 应用旋转
    glRotatef(rotation_x, 1, 0, 0)
    glRotatef(rotation_y, 0, 1, 0)
    glRotatef(rotation_z, 0, 0, 1)

    # 更新天体位置
    if not paused:
        simulation_time += dt
        
        # 更新行星
        for planet in planets:
            # 计算黑洞对行星的引力
            fx, fy, fz = planet.calculate_gravity(black_hole, dt)
            
            # 更新行星速度
            planet.update_velocity(fx, fy, fz, dt)
            
            # 更新行星位置
            planet.update_position(dt)
            
            # 检查是否被黑洞捕获
            distance_to_black_hole = math.sqrt(
                (planet.x - black_hole.x)**2 + 
                (planet.y - black_hole.y)**2 + 
                (planet.z - black_hole.z)**2)
            
            # 如果距离小于黑洞半径，行星被吞噬
            if distance_to_black_hole < black_hole.radius:
                # 增加黑洞质量
                black_hole.mass += planet.mass
                planets.remove(planet)
        
        # 更新光子（光线弯曲效应）
        for photon in photons[:]:  # 使用副本迭代，以便安全删除
            # 计算黑洞对光子的引力（光也受引力影响）
            fx, fy, fz = photon.calculate_gravity(black_hole, dt)
            
            # 更新光子速度
            photon.update_velocity(fx, fy, fz, dt)
            
            # 更新光子位置
            photon.update_position(dt)
            
            # 检查是否被黑洞捕获
            distance_to_black_hole = math.sqrt(
                (photon.x - black_hole.x)**2 + 
                (photon.y - black_hole.y)**2 + 
                (photon.z - black_hole.z)**2)
            
            # 如果距离小于黑洞半径，光子被吞噬
            if distance_to_black_hole < black_hole.radius:
                photons.remove(photon)
            
            # 如果光子飞得太远，移除它
            elif abs(photon.x) > 1000 or abs(photon.z) > 1000:
                photons.remove(photon)

    # 绘制时空网格
    if show_grid:
        draw_spacetime_grid(spacetime_grid, grid_divisions)
        
    # 绘制黑洞
    black_hole.draw()
    
    # 绘制行星
    for planet in planets:
        planet.draw()
    
    # 绘制光子
    for photon in photons:
        photon.draw()

    # 渲染UI层
    if show_info:
        # 切换回2D模式绘制文本
        modelview = glGetDoublev(GL_MODELVIEW_MATRIX)
        projection = glGetDoublev(GL_PROJECTION_MATRIX)
        viewport = glGetIntegerv(GL_VIEWPORT)
        
        # 2D绘制文本前保存状态
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        glOrtho(0, WIDTH, HEIGHT, 0, -1, 1)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        
        # 禁用深度测试
        glDisable(GL_DEPTH_TEST)
        
        # 绘制2D覆盖层
        screen_surface = pygame.display.get_surface()
        info_text = [
            f"相对论太阳系模拟 - 黑洞效应",
            f"时间步长: {dt:.2f}",
            f"模拟时间: {simulation_time:.1f} 单位",
            f"黑洞质量: {black_hole.mass:.1e}",
            f"行星数量: {len(planets)}",
            "空格: 暂停/继续",
            "i: 显示/隐藏信息",
            "g: 显示/隐藏时空网格",
            "w: 切换时空弯曲",
            "r: 重置光子",
            "方向键: 旋转视图",
            "Ctrl+上下: 上下旋转",
            "Q/E: Z轴旋转",
            f"状态: {'暂停' if paused else '运行'}"
        ]
        
        for i, text in enumerate(info_text):
            draw_text(screen_surface, text, 10, 10 + i * 25)
        
        # 对每个行星显示近日点进动
        y_offset = 380
        draw_text(screen_surface, "近日点进动:", 10, y_offset)
        y_offset += 25
        for planet in planets:
            draw_text(screen_surface, f"{planet.name}: {planet.perihelion_shift:.5f} 弧度", 
                    10, y_offset)
            y_offset += 25
            
        # 恢复状态
        glEnable(GL_DEPTH_TEST)
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopMatrix()

    # 更新显示
    pygame.display.flip()
    clock.tick(60)

pygame.quit()