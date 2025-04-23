import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import math
import numpy as np

# -------------------- 配置常量 --------------------
class Config:
    WIDTH, HEIGHT = 1000, 800
    FPS = 60
    MAX_TRAIL_LENGTH = 300
    BACKGROUND_COLOR = (0.0, 0.0, 0.05, 1.0)
    STAR_COUNT = 2000
    DEFAULT_SHOW_NAMES = True
    DEFAULT_SHOW_ORBITS = True
    
    # 颜色定义
    COLORS = {
        'YELLOW': (1.0, 1.0, 0.0),
        'BLUE': (0.1, 0.4, 0.9),
        'RED': (0.9, 0.2, 0.2),
        'ORANGE': (1.0, 0.65, 0.0),
        'GREY': (0.6, 0.6, 0.6),
        'SATURN': (0.9, 0.8, 0.5),
        'JUPITER': (0.9, 0.7, 0.4),
    }
    
    # 行星参数
    PLANET_PARAMS = [
        # (距离, 半径, 颜色, 质量, 速度, 倾角, 名称)
        (70, 3, 'GREY', 3.3e23, 0.02, 7.0, "水星"),
        (100, 6, 'ORANGE', 4.87e24, 0.015, 3.4, "金星"),
        (150, 7, 'BLUE', 5.97e24, 0.01, 0.0, "地球"),
        (200, 5, 'RED', 6.42e23, 0.008, 1.8, "火星"),
        (280, 15, 'JUPITER', 1.898e27, 0.004, 1.3, "木星"),
        (400, 12, 'SATURN', 5.683e26, 0.003, 2.5, "土星"),
    ]

# -------------------- 摄像机类 --------------------
class Camera:
    def __init__(self):
        self.reset()
        
    def reset(self):
        self.position = [0.0, 0.0, -600.0]
        self.rotation = [30.0, 0.0, 0.0]
        self.zoom_level = 1.0
        self.dragging = False
        self.last_mouse_pos = (0, 0)

    def apply(self):
        glLoadIdentity()
        glTranslatef(*self.position)
        glTranslatef(0, 0, 200 * (1 - self.zoom_level))
        glRotatef(self.rotation[0], 1, 0, 0)
        glRotatef(self.rotation[1], 0, 1, 0)
        glRotatef(self.rotation[2], 0, 0, 1)

    def handle_input(self, events):
        keys = pygame.key.get_pressed()
        
        # 键盘旋转控制
        if keys[K_LEFT]: self.rotation[1] -= 1
        if keys[K_RIGHT]: self.rotation[1] += 1
        if keys[K_UP] and (keys[K_LCTRL] or keys[K_RCTRL]): 
            self.rotation[0] -= 1
        if keys[K_DOWN] and (keys[K_LCTRL] or keys[K_RCTRL]):
            self.rotation[0] += 1
        if keys[K_q]: self.rotation[2] -= 1
        if keys[K_e]: self.rotation[2] += 1

        # 鼠标事件处理
        for event in events:
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    self.start_drag(event.pos)
                elif event.button == 4: self.zoom(0.1)
                elif event.button == 5: self.zoom(-0.1)
            elif event.type == MOUSEBUTTONUP and event.button == 1:
                self.end_drag()
            elif event.type == MOUSEMOTION:
                self.drag(event.pos)

    def rotate(self, dx, dy):
        self.rotation[1] += dx * 0.1
        self.rotation[0] += dy * 0.1

    def zoom(self, amount):
        self.zoom_level = np.clip(self.zoom_level + amount, 0.1, 3.0)

    def start_drag(self, pos):
        self.dragging = True
        self.last_mouse_pos = pos

    def end_drag(self):
        self.dragging = False

    def drag(self, pos):
        if self.dragging:
            dx = pos[0] - self.last_mouse_pos[0]
            dy = pos[1] - self.last_mouse_pos[1]
            self.rotate(dx, dy)
            self.last_mouse_pos = pos

# -------------------- 天体类 --------------------
class CelestialBody:
    def __init__(self, distance, radius, color_name, mass, speed, inclination, name):
        self.distance = distance
        self.radius = radius
        self.color = Config.COLORS[color_name]
        self.mass = mass
        self.orbital_speed = speed
        self.inclination = math.radians(inclination)
        self.name = name
        
        self.angle = 0
        self.rotation_angle = 0
        self._init_position()
        self._init_trail()
        self.quadratic = gluNewQuadric()

    def _init_position(self):
        self.x = self.distance
        self.y = self.z = 0.0

    def _init_trail(self):
        self.trail = np.zeros((Config.MAX_TRAIL_LENGTH, 3), dtype=np.float32)
        self.trail_index = 0
        self.trail_count = 0

    def update_position(self, dt):
        self.angle += self.orbital_speed * dt
        self._calculate_position()
        self._update_trail()
        self.rotation_angle += dt * 10

    def _calculate_position(self):
        self.x = self.distance * math.cos(self.angle)
        self.y = self.distance * math.sin(self.angle) * math.cos(self.inclination)
        self.z = self.distance * math.sin(self.angle) * math.sin(self.inclination)

    def _update_trail(self):
        idx = self.trail_index % Config.MAX_TRAIL_LENGTH
        self.trail[idx] = (self.x, self.y, self.z)
        self.trail_index += 1
        self.trail_count = min(self.trail_count + 1, Config.MAX_TRAIL_LENGTH)

    def draw(self):
        self._draw_body()
        self._draw_trail()

    def _draw_body(self):
        glPushMatrix()
        glTranslatef(self.x, self.y, self.z)
        glRotatef(self.rotation_angle, 0, 1, 0)
        glColor3f(*self._enhanced_color())
        gluSphere(self.quadratic, self.radius, 24, 24)
        glPopMatrix()

    def _enhanced_color(self):
        return tuple(min(1.0, c*1.5) for c in self.color)

    def _draw_trail(self):
        if self.trail_count < 2: return
        
        glDisable(GL_LIGHTING)
        glLineWidth(2.0)
        glBegin(GL_LINE_STRIP)
        for i in range(self.trail_count):
            alpha = i / self.trail_count
            glColor4f(*self._enhanced_color(), alpha)
            glVertex3fv(self.trail[(self.trail_index - i) % Config.MAX_TRAIL_LENGTH])
        glEnd()
        glEnable(GL_LIGHTING)

# -------------------- 太阳系类 --------------------
class SolarSystem:
    def __init__(self):
        self.sun = CelestialBody(0, 20, 'YELLOW', 1.989e30, 0, 0, "太阳")
        self.planets = [self._create_planet(*params) for params in Config.PLANET_PARAMS]
        self.show_orbits = Config.DEFAULT_SHOW_ORBITS
        self.show_names = Config.DEFAULT_SHOW_NAMES

    def _create_planet(self, *args):
        return CelestialBody(*args)

    def update(self, dt, paused):
        if not paused:
            for planet in self.planets:
                planet.update_position(dt)

    def draw(self):
        self._draw_orbits()
        self.sun.draw()
        for planet in self.planets:
            planet.draw()

    def _draw_orbits(self):
        if not self.show_orbits: return
        
        glDisable(GL_LIGHTING)
        glLineWidth(1.0)
        for planet in self.planets:
            glBegin(GL_LINE_LOOP)
            for angle in np.linspace(0, 2*np.pi, 100):
                x = planet.distance * math.cos(angle)
                y = planet.distance * math.sin(angle) * math.cos(planet.inclination)
                z = planet.distance * math.sin(angle) * math.sin(planet.inclination)
                glVertex3f(x, y, z)
            glEnd()
        glEnable(GL_LIGHTING)

# -------------------- 用户界面类 --------------------
class UserInterface:
    def __init__(self):
        self.font = pygame.font.SysFont('Arial', 24)
        self.show_info = True
        self.show_help = False

    def toggle_display(self, key):
        if key == K_i: self.show_info = not self.show_info
        elif key == K_h: self.show_help = not self.show_help

    def render(self, surface, solar_system, camera, dt, paused):
        if self.show_help:
            self._render_help(surface)
        else:
            if self.show_info: 
                self._render_info(surface, dt, paused, camera)
            if solar_system.show_names: 
                self._render_names(surface, solar_system)

    def _render_info(self, surface, dt, paused, camera):
        self._draw_panel(surface, [
            f"时间步长: {dt:.2f}",
            f"缩放: {camera.zoom_level:.1f}x",
            f"状态: {'暂停' if paused else '运行'}",
            "控制: 空格-暂停 I-信息 O-轨道 N-名称",
            "方向键: 旋转 Q/E-Z轴旋转",
            "鼠标拖拽/滚轮: 视角控制"
        ])

    def _render_help(self, surface):
        self._draw_panel(surface, [
            "=== 帮助 ===",
            "空格: 暂停/继续",
            "I: 显示/隐藏信息",
            "O: 显示/隐藏轨道",
            "N: 显示/隐藏名称",
            "H: 显示帮助",
            "R: 重置视角",
            "+/-: 调整时间步长",
            "ESC: 退出"
        ], width=400)

    def _draw_panel(self, surface, lines, x=20, y=20, width=300, alpha=150):
        panel = pygame.Surface((width, len(lines)*25 + 20), pygame.SRCALPHA)
        panel.fill((0, 0, 0, alpha))
        for i, text in enumerate(lines):
            self._draw_text(panel, text, 10, 10 + i*25)
        surface.blit(panel, (x, y))

    def _render_names(self, surface, solar_system):
        if not solar_system.show_names:
            return
            
        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_LIGHTING)
        for body in [solar_system.sun] + solar_system.planets:
            self._draw_name(surface, body)
        glPopAttrib()

    def _draw_name(self, surface, body):
        viewport = glGetIntegerv(GL_VIEWPORT)
        proj = glGetDoublev(GL_PROJECTION_MATRIX)
        model = glGetDoublev(GL_MODELVIEW_MATRIX)
        
        pos = gluProject(body.x, body.y, body.z, model, proj, viewport)
        if pos and 0 <= pos[0] <= Config.WIDTH and 0 <= pos[1] <= Config.HEIGHT:
            self._draw_text(surface, body.name, pos[0], Config.HEIGHT - pos[1] - 30)

    def _draw_text(self, surface, text, x, y, color=(255,255,255)):
        text_surf = self.font.render(text, True, color)
        surface.blit(text_surf, (x, y))

# -------------------- 主程序类 --------------------
class SolarSystemSimulator:
    def __init__(self):
        pygame.init()
        self._init_opengl()
        self.camera = Camera()
        self.solar_system = SolarSystem()
        self.ui = UserInterface()
        self.clock = pygame.time.Clock()
        self.dt = 1.0
        self.paused = False
        self.stars = self._generate_stars()

    def _init_opengl(self):
        pygame.display.set_mode((Config.WIDTH, Config.HEIGHT), DOUBLEBUF|OPENGL)
        gluPerspective(45, Config.WIDTH/Config.HEIGHT, 1.0, 5000.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        self._setup_lighting()

    def _setup_lighting(self):
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.6, 0.6, 0.6, 1))
        glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1))
        glLightfv(GL_LIGHT0, GL_POSITION, (0,0,0,1))

    def _generate_stars(self):
        return [self._random_star() for _ in range(Config.STAR_COUNT)]

    def _random_star(self):
        theta = np.random.uniform(0, 2*np.pi)
        phi = np.arccos(np.random.uniform(-1, 1))
        r = 900
        return (r*math.sin(phi)*math.cos(theta),
                r*math.sin(phi)*math.sin(theta),
                r*math.cos(phi))

    def run(self):
        while True:
            if not self._handle_events():
                break
            self._update()
            self._render()
            pygame.display.flip()
            self.clock.tick(Config.FPS)
        pygame.quit()

    def _handle_events(self):
        events = pygame.event.get()
        for event in events:
            if event.type == QUIT:
                return False
            if event.type == KEYDOWN:
                self._handle_keydown(event)
        self.camera.handle_input(events)
        return True

    def _handle_keydown(self, event):
        key = event.key
        if key == K_ESCAPE: 
            pygame.event.post(pygame.event.Event(QUIT))
        elif key == K_SPACE: 
            self.paused = not self.paused
        elif key in (K_PLUS, K_KP_PLUS): 
            self.dt *= 1.2
        elif key in (K_MINUS, K_KP_MINUS): 
            self.dt /= 1.2
        elif key == K_o: 
            self.solar_system.show_orbits = not self.solar_system.show_orbits
        elif key == K_n: 
            self.solar_system.show_names = not self.solar_system.show_names
        elif key == K_r: 
            self.camera.reset()
        else: 
            self.ui.toggle_display(key)

    def _update(self):
        self.solar_system.update(self.dt, self.paused)

    def _render(self):
        glClearColor(*Config.BACKGROUND_COLOR)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        self.camera.apply()
        self._draw_stars()
        self.solar_system.draw()
        self.ui.render(pygame.display.get_surface(), self.solar_system, 
                      self.camera, self.dt, self.paused)

    def _draw_stars(self):
        glDisable(GL_LIGHTING)
        glPointSize(2.0)
        glBegin(GL_POINTS)
        for star in self.stars:
            glVertex3fv(star)
        glEnd()
        glEnable(GL_LIGHTING)

if __name__ == "__main__":
    simulator = SolarSystemSimulator()
    simulator.run()