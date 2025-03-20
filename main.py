import os
import sys
import random
import math
import json
import re

# Imprimir información de diagnóstico
print("Directorio de trabajo actual: " + os.getcwd())
print("Archivos en el directorio actual:")
for item in os.listdir('.'):
    print(f"  - {item}")

# Verificar archivos de imagen necesarios
print("Verificando archivos de imagen necesarios:")
img_folder = "Player_ship.png"
required_files = ["Nave del jugador.jpeg", "Nave enemiga.jpeg", "Nave del jefe.jpeg", "Espacio.png"]
all_files_exist = True

if os.path.exists(img_folder) and os.path.isdir(img_folder):
    for file in required_files:
        if os.path.exists(os.path.join(img_folder, file)):
            print(f"  [OK] {file} encontrado en {img_folder}/")
        else:
            print(f"  [ERROR] {file} no encontrado en {img_folder}/")
            all_files_exist = False
else:
    print(f"  [ERROR] La carpeta {img_folder} no existe o no es un directorio")
    all_files_exist = False

# Inicializar pygame correctamente
import pygame
# Configuración específica para solucionar problemas de ventana en Windows
pygame.display.init()  # Inicializar específicamente el subsistema de visualización
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLEBUFFERS, 0)
pygame.display.gl_set_attribute(pygame.GL_MULTISAMPLESAMPLES, 0)

# Asegurarse de que pygame se inicie correctamente
try:
    pygame.init()
    
    # Verificar que se inicializó correctamente
    initialized_modules = pygame.get_init()
    if initialized_modules:
        print(f"pygame inicializado correctamente.")
        
        # Intenta configurar un modo de pantalla mínimo para probar la visualización
        try:
            test_screen = pygame.display.set_mode((100, 100), pygame.SCALED | pygame.DOUBLEBUF)
            pygame.display.set_caption("Prueba")
            if test_screen:
                print("pygame puede crear una ventana correctamente.")
                # Limpiar la pantalla de prueba y mostrar algo
                test_screen.fill((0, 0, 0))
                pygame.draw.circle(test_screen, (255, 0, 0), (50, 50), 20)
                pygame.display.flip()
                # Mantener la pantalla por un momento para que sea visible
                pygame.time.wait(100)
                # Cerrar esta ventana de prueba
                pygame.display.quit()
            else:
                print("ERROR: pygame no pudo crear una ventana.")
        except pygame.error as e:
            print(f"Error al probar la ventana: {e}")
    else:
        print("ERROR: pygame no se inicializó correctamente.")
except Exception as e:
    print(f"ERROR al inicializar pygame: {e}")
    sys.exit(1)

# Configuración para mejorar la compatibilidad
# os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

# Constantes
WIDTH, HEIGHT = 800, 600
PLAYER_SPEED = 2  # Reducido de 5 a 2 como solicitado
ENEMY_SPEED = 150
BOSS_SPEED = 100
PROJECTILE_SPEED = 500
ENEMY_SPAWN_INTERVAL = 3  # segundos
ASTEROID_SPAWN_INTERVAL = 2  # segundos
FPS = 60
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)

# Función para cargar y escalar imágenes
def load_image(path, width, height):
    # Asegurarnos de que se carguen todas las imágenes desde la carpeta correcta
    try:
        # Ruta principal: Player_ship.png/[nombre_imagen]
        full_path = os.path.join("Player_ship.png", os.path.basename(path))
        print(f"Intentando cargar imagen desde: {full_path}")
        try:
            img = pygame.image.load(full_path).convert_alpha()
            print(f"¡Imagen cargada exitosamente desde: {full_path}!")
            return pygame.transform.scale(img, (width, height))
        except pygame.error as e:
            print(f"Error al cargar imagen desde {full_path}: {e}")
            
            # Intentar con ruta alternativa (directamente en la carpeta raíz)
            alt_path = os.path.basename(path)
            print(f"Intentando ruta alternativa: {alt_path}")
            try:
                img = pygame.image.load(alt_path).convert_alpha()
                print(f"¡Imagen cargada exitosamente desde: {alt_path}!")
                return pygame.transform.scale(img, (width, height))
            except pygame.error as e2:
                print(f"Error al cargar imagen desde {alt_path}: {e2}")
                
                # Intentar desde la carpeta assets
                assets_path = os.path.join("assets", os.path.basename(path).replace(".jpeg", ".svg").replace(".png", ".svg"))
                try:
                    print(f"Intentando cargar desde assets: {assets_path}")
                    img = pygame.image.load(assets_path).convert_alpha()
                    print(f"¡Imagen cargada exitosamente desde: {assets_path}!")
                    return pygame.transform.scale(img, (width, height))
                except pygame.error as e3:
                    print(f"Error al cargar imagen desde {assets_path}: {e3}")
                    
                    # Crear una superficie de color como último recurso
                    print(f"Creando superficie de color para reemplazar imagen: {path}")
                    surface = pygame.Surface((width, height), pygame.SRCALPHA)
                    pygame.draw.rect(surface, (255, 0, 255), (0, 0, width, height))
                    return surface
    except Exception as e:
        print(f"Error general al cargar imagen {path}: {e}")
        surface = pygame.Surface((width, height), pygame.SRCALPHA)
        pygame.draw.rect(surface, (255, 0, 255), (0, 0, width, height))
        return surface

# Funciones para manejar usuarios y puntuaciones
def load_game_data():
    """Carga los datos del juego (usuarios y puntuaciones) desde el archivo JSON"""
    try:
        with open("game_data.json", "r") as f:
            data = json.load(f)
            
            # Asegurarse de que todas las estructuras necesarias existen
            if "users" not in data:
                data["users"] = []
            if "scores" not in data:
                data["scores"] = []
            
            # Eliminar registros de puntuaciones sin email
            data["scores"] = [score for score in data["scores"] if "email" in score and score["email"]]
            
            # Limpiar puntuaciones duplicadas
            clean_duplicate_scores(data)
            
            # Guardar los datos limpios
            save_game_data(data)
            
            return data
    except (FileNotFoundError, json.JSONDecodeError):
        # Si el archivo no existe o está corrupto, crear estructura inicial
        default_data = {
            "users": [],
            "scores": []
        }
        save_game_data(default_data)
        return default_data

def normalize_email(email):
    """Normaliza el correo electrónico para comparaciones consistentes"""
    if not email:
        return ""
    
    # Convertir a minúsculas y eliminar espacios
    normalized = email.lower().strip()
    
    # Correcciones comunes para dominios populares
    common_typos = {
        "gmal": "gmail",
        "gmial": "gmail",
        "gamil": "gmail",
        "gmali": "gmail",
        "gmaill": "gmail",
        "gmail": "gmail",  # Keep it as is
        "hotmal": "hotmail",
        "hotmial": "hotmail",
        "hotmall": "hotmail",
        "hotmail": "hotmail",  # Keep it as is
        "yaho": "yahoo",
        "yahooo": "yahoo",
        "yahoo": "yahoo"  # Keep it as is
    }
    
    # Dividir el correo en usuario y dominio
    parts = normalized.split('@')
    if len(parts) == 2:
        username, domain = parts
        
        # Dividir el dominio en nombre y extensión
        domain_parts = domain.split('.')
        if len(domain_parts) >= 2:
            domain_name = domain_parts[0]
            domain_ext = '.'.join(domain_parts[1:])
            
            # Corregir errores comunes en dominios
            if domain_name in common_typos:
                domain_name = common_typos[domain_name]
                
            return f"{username}@{domain_name}.{domain_ext}"
    
    return normalized

def email_similarity(email1, email2):
    """Determina si dos correos electrónicos son similares"""
    # Si son idénticos después de normalizar, son similares
    if normalize_email(email1) == normalize_email(email2):
        return True
        
    # Si alguno está vacío, no son similares
    if not email1 or not email2:
        return False
    
    # Dividir los correos en parte local y dominio
    parts1 = email1.lower().strip().split('@')
    parts2 = email2.lower().strip().split('@')
    
    # Si no tienen formato correcto, no son similares
    if len(parts1) != 2 or len(parts2) != 2:
        return False
    
    user1, domain1 = parts1
    user2, domain2 = parts2
    
    # Si las partes locales son idénticas, es probable que sean del mismo usuario
    if user1 == user2:
        # Verificar si los dominios son muy similares
        # Separar dominios en nombre y extensión
        domain_parts1 = domain1.split('.')
        domain_parts2 = domain2.split('.')
        
        # Si los dominios tienen extensiones diferentes, no son similares
        if len(domain_parts1) >= 2 and len(domain_parts2) >= 2:
            if domain_parts1[-1] != domain_parts2[-1]:
                return False
                
            # Comparar los nombres de dominio (gmail, hotmail, etc.)
            domain_name1 = domain_parts1[0]
            domain_name2 = domain_parts2[0]
            
            # Dominios comunes que podrían confundirse
            if domain_name1 in ["gmail", "gmal", "gmial"] and domain_name2 in ["gmail", "gmal", "gmial"]:
                return True
            if domain_name1 in ["hotmail", "hotmal"] and domain_name2 in ["hotmail", "hotmal"]:
                return True
                
    return False

def clean_duplicate_scores(data):
    """Elimina puntuaciones duplicadas, dejando solo la mejor para cada correo"""
    if "scores" not in data or not data["scores"]:
        return data
    
    # Diccionario para almacenar la mejor puntuación de cada usuario
    # Usaremos correos normalizados como claves
    best_scores = {}
    email_groups = {}  # Para agrupar correos similares
    
    # Primero, normalizar todos los correos en usuarios
    if "users" in data:
        for user in data["users"]:
            if "email" in user and user["email"]:
                original_email = user["email"]
                normalized_email = normalize_email(original_email)
                user["email"] = normalized_email
    
    # Recorrer todas las puntuaciones
    for score_entry in data["scores"][:]:  # Usar una copia para iterar
        if "email" not in score_entry or not score_entry["email"]:
            continue  # Ignorar entradas sin email
            
        original_email = score_entry["email"]
        normalized_email = normalize_email(original_email)
        
        # Actualizar el correo en la entrada actual
        score_entry["email"] = normalized_email
        
        # Verificar si este correo es similar a alguno que ya tenemos
        found_group = False
        for group_key, emails in email_groups.items():
            if any(email_similarity(normalized_email, e) for e in emails):
                emails.append(normalized_email)
                normalized_email = group_key  # Usar el correo principal del grupo
                found_group = True
                break
                
        if not found_group:
            # Crear un nuevo grupo con este correo
            email_groups[normalized_email] = [normalized_email]
        
        score = score_entry.get("score", 0)
        
        # Si no tenemos este email registrado o la puntuación es mejor
        if normalized_email not in best_scores or score > best_scores[normalized_email].get("score", 0):
            best_scores[normalized_email] = score_entry
    
    # Reemplazar la lista de puntuaciones con solo las mejores
    old_count = len(data["scores"])
    data["scores"] = list(best_scores.values())
    new_count = len(data["scores"])
    
    if old_count != new_count:
        print(f"Lista de puntuaciones limpiada. Se eliminaron {old_count - new_count} duplicados.")
    else:
        print("No se encontraron puntuaciones duplicadas.")
    
    return data

def save_game_data(data):
    """Guarda los datos del juego en el archivo JSON"""
    with open("game_data.json", "w") as f:
        json.dump(data, f, indent=2)

def validate_email(email):
    """Valida que el correo electrónico tenga un formato válido"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return bool(re.match(pattern, email))

def user_exists(email):
    """Verifica si un usuario ya existe en el sistema"""
    normalized_email = normalize_email(email)
    data = load_game_data()
    
    # Verificar coincidencia exacta primero
    for user in data["users"]:
        if normalize_email(user["email"]) == normalized_email:
            return True
            
    # Si no hay coincidencia exacta, verificar similitud
    for user in data["users"]:
        if email_similarity(normalized_email, user["email"]):
            return True
            
    return False

def add_user(email):
    """Añade un nuevo usuario al sistema"""
    normalized_email = normalize_email(email)
    if not validate_email(email) or user_exists(normalized_email):
        return False
    
    data = load_game_data()
    data["users"].append({
        "email": normalized_email,
        "created_at": pygame.time.get_ticks()
    })
    save_game_data(data)
    return True

def save_score(email, score):
    """Guarda la puntuación de un usuario"""
    normalized_email = normalize_email(email)
    if not user_exists(normalized_email):
        return False
        
    data = load_game_data()
    
    # Buscar si el usuario ya tiene una puntuación registrada
    user_has_score = False
    highest_score = 0
    similar_emails = []
    
    # Primero, encontrar todos los correos similares
    for entry in data["scores"]:
        entry_email = entry.get("email", "")
        if email_similarity(normalized_email, entry_email):
            similar_emails.append(entry_email)
            user_has_score = True
            highest_score = max(highest_score, entry.get("score", 0))
            
    # Si el usuario ya tiene puntuación y la nueva no es mayor, no hacer nada
    if user_has_score and score <= highest_score:
        print(f"No se actualiza la puntuación, la anterior ({highest_score}) es mayor o igual que la actual ({score})")
        return True
        
    # Si el usuario ya tiene puntuación, actualizar eliminando las anteriores
    if user_has_score:
        # Eliminar todas las puntuaciones anteriores del usuario y similares
        data["scores"] = [s for s in data["scores"] if not any(email_similarity(s.get("email", ""), e) for e in similar_emails)]
        print(f"Puntuaciones anteriores eliminadas. Nueva puntuación: {score}")
    
    # Añadir la nueva puntuación
    data["scores"].append({
        "email": normalized_email,
        "score": score,
        "date": pygame.time.get_ticks()
    })
    
    # Limpiar duplicados para asegurar consistencia
    clean_duplicate_scores(data)
    
    save_game_data(data)
    return True

def get_top_scores(limit=10):
    """Obtiene las mejores puntuaciones ordenadas de mayor a menor"""
    data = load_game_data()
    scores = data["scores"]
    # Ordenar puntuaciones de mayor a menor
    scores.sort(key=lambda x: x["score"], reverse=True)
    # Convertir a lista de tuplas (email, score) para facilitar su uso
    result = [(score["email"], score["score"]) for score in scores[:limit]]
    return result

class InputBox:
    """Clase para manejar cajas de entrada de texto"""
    def __init__(self, x, y, width, height, text='', placeholder=''):
        self.rect = pygame.Rect(x, y, width, height)
        self.color_inactive = pygame.Color('lightskyblue3')
        self.color_active = pygame.Color('dodgerblue2')
        self.color = self.color_inactive
        self.text = text
        self.placeholder = placeholder
        self.font = pygame.font.SysFont("Arial", 24)
        self.txt_surface = self.font.render(text, True, self.color)
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.cursor_blink_rate = 0.5  # segundos

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Si el usuario hace clic en el input_box, activarlo
            if self.rect.collidepoint(event.pos):
                self.active = True
                self.color = self.color_active
            else:
                self.active = False
                self.color = self.color_inactive
            return False
        
        if event.type == pygame.KEYDOWN:
            if self.active:
                if event.key == pygame.K_RETURN:
                    return True  # Indicar que se ha pulsado Enter
                elif event.key == pygame.K_BACKSPACE:
                    self.text = self.text[:-1]
                else:
                    self.text += event.unicode
                # Actualizar la superficie de texto y el cursor
                self.txt_surface = self.font.render(self.text, True, WHITE)
                return False
        return False

    def update(self, dt):
        # Actualizar temporizador del cursor
        self.cursor_timer += dt
        if self.cursor_timer >= self.cursor_blink_rate:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
            
        # Asegurar que el ancho del rectángulo se ajuste al texto
        width = max(200, self.txt_surface.get_width() + 10)
        self.rect.w = width

    def draw(self, screen):
        # Dibujar rectángulo de fondo
        pygame.draw.rect(screen, BLACK, self.rect, 0)
        pygame.draw.rect(screen, self.color, self.rect, 2)
        
        # Dibujar texto o placeholder
        if self.text:
            screen.blit(self.txt_surface, (self.rect.x + 5, self.rect.y + 5))
        elif not self.active:
            placeholder_surface = self.font.render(self.placeholder, True, pygame.Color('grey'))
            screen.blit(placeholder_surface, (self.rect.x + 5, self.rect.y + 5))
        
        # Dibujar cursor cuando está activo y visible
        if self.active and self.cursor_visible:
            cursor_pos = self.rect.x + self.txt_surface.get_width() + 5
            cursor_height = self.txt_surface.get_height()
            pygame.draw.line(screen, self.color, 
                            (cursor_pos, self.rect.y + 5), 
                            (cursor_pos, self.rect.y + 5 + cursor_height), 
                            2)

class Player:
    def __init__(self):
        # Cargar la imagen del jugador
        self.image = load_image("Nave del jugador.jpeg", 50, 50)
        self.rect = self.image.get_rect(center=(WIDTH // 2, HEIGHT - 60))
        self.shoot_cooldown = 0
        self.health = 100
        self.lives = 3
        self.invulnerable = False
        self.invulnerable_timer = 0
        self.score = 0

    def move(self, dx, dy):
        # Asegurar que la nave no salga de la pantalla
        self.rect.x = max(0, min(WIDTH - self.rect.width, self.rect.x + dx))
        self.rect.y = max(0, min(HEIGHT - self.rect.height, self.rect.y + dy))

    def shoot(self, projectiles):
        if self.shoot_cooldown <= 0:
            projectiles.append(PlayerProjectile(self.rect.centerx, self.rect.top))
            self.shoot_cooldown = 0.2  # Cooldown de 200ms
            return True
        return False

    def take_damage(self, damage):
        if not self.invulnerable:
            self.health -= damage
            if self.health <= 0:
                self.lives -= 1
                if self.lives > 0:
                    self.health = 100
                    self.invulnerable = True
                    self.invulnerable_timer = 2.0  # Invulnerabilidad de 2 segundos
                return True
        return False

    def update(self, dt):
        # Actualizar cooldown de disparo
        if self.shoot_cooldown > 0:
            self.shoot_cooldown -= dt
        
        # Actualizar invulnerabilidad
        if self.invulnerable:
            self.invulnerable_timer -= dt
            if self.invulnerable_timer <= 0:
                self.invulnerable = False

    def draw(self, screen):
        # Parpadeo durante invulnerabilidad
        if self.invulnerable and int(pygame.time.get_ticks() / 100) % 2 == 0:
            return
        screen.blit(self.image, self.rect)

class PlayerProjectile:
    def __init__(self, x, y):
        # Crear proyectil del jugador (un simple rectángulo verde)
        self.image = pygame.Surface((5, 15), pygame.SRCALPHA)
        self.image.fill(GREEN)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PROJECTILE_SPEED
        self.damage = 10

    def update(self, dt):
        self.rect.y -= self.speed * dt
        return self.rect.bottom < 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class EnemyProjectile:
    def __init__(self, x, y):
        # Crear proyectil enemigo (un simple rectángulo rojo)
        self.image = pygame.Surface((5, 15), pygame.SRCALPHA)
        self.image.fill(RED)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = PROJECTILE_SPEED * 0.7
        self.damage = 10

    def update(self, dt):
        self.rect.y += self.speed * dt
        return self.rect.top > HEIGHT

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Enemy:
    def __init__(self, x, y):
        # Cargar la imagen del enemigo
        self.image = load_image("Nave enemiga.jpeg", 40, 40)
        self.rect = self.image.get_rect(center=(x, y))
        self.speed = ENEMY_SPEED
        self.shoot_timer = random.uniform(1.0, 3.0)
        self.health = 30
        self.score_value = 100

    def update(self, player_pos, dt):
        # Movimiento hacia el jugador
        dx = player_pos[0] - self.rect.centerx
        dy = player_pos[1] - self.rect.centery
        dist = math.hypot(dx, dy)
        
        if dist != 0:
            dx /= dist
            dy /= dist
            
            # Limitar movimiento vertical
            if self.rect.y < 150:
                dy = max(0, dy)
                
            self.rect.x += dx * self.speed * dt
            self.rect.y += dy * self.speed * dt
            
        # Actualizar timer de disparo
        self.shoot_timer -= dt
        
    def should_shoot(self):
        if self.shoot_timer <= 0:
            self.shoot_timer = random.uniform(1.0, 3.0)
            return True
        return False
        
    def shoot(self, projectiles):
        projectiles.append(EnemyProjectile(self.rect.centerx, self.rect.bottom))

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Boss:
    def __init__(self):
        # Cargar la imagen del jefe
        self.image = load_image("Nave del jefe.jpeg", 120, 120)
        self.rect = self.image.get_rect(center=(WIDTH // 2, 100))
        self.speed = BOSS_SPEED
        self.health = 500
        self.max_health = 500
        self.shoot_timer = 0
        self.pattern_timer = 0
        self.pattern = 0
        self.target_x = WIDTH // 2
        self.score_value = 1000
        self.active = False
        self.entrance_timer = 2.0

    def update(self, player_pos, dt, projectiles):
        # Entrada del boss
        if self.entrance_timer > 0:
            self.entrance_timer -= dt
            self.rect.y = -self.rect.height + (1 - self.entrance_timer / 2.0) * (100 + self.rect.height)
            return
        
        self.active = True
        
        # Patrones de movimiento
        self.pattern_timer -= dt
        if self.pattern_timer <= 0:
            self.pattern = (self.pattern + 1) % 3
            self.pattern_timer = random.uniform(3.0, 5.0)
            
            if self.pattern == 0:  # Movimiento lateral
                self.target_x = random.randint(100, WIDTH - 100)
            elif self.pattern == 1:  # Acercamiento al jugador
                self.target_x = player_pos[0]
        
        # Ejecutar patrón actual
        if self.pattern == 0:  # Movimiento lateral
            dx = self.target_x - self.rect.centerx
            if abs(dx) > 5:
                dx = dx / abs(dx) * min(abs(dx), self.speed * dt)
                self.rect.x += dx
                
        elif self.pattern == 1:  # Seguimiento al jugador
            dx = player_pos[0] - self.rect.centerx
            if abs(dx) > 10:
                dx = dx / abs(dx) * min(abs(dx), self.speed * 0.5 * dt)
                self.rect.x += dx
                
        elif self.pattern == 2:  # Movimiento aleatorio
            if random.random() < 0.05:
                self.target_x = random.randint(100, WIDTH - 100)
            
            dx = self.target_x - self.rect.centerx
            if abs(dx) > 5:
                dx = dx / abs(dx) * min(abs(dx), self.speed * 0.7 * dt)
                self.rect.x += dx
        
        # Disparos
        self.shoot_timer -= dt
        if self.shoot_timer <= 0:
            self.shoot(projectiles)
            # Determinar próximo disparo según el patrón
            if self.pattern == 0:
                self.shoot_timer = 0.5
            elif self.pattern == 1:
                self.shoot_timer = 0.2
            else:
                self.shoot_timer = 0.8

    def shoot(self, projectiles):
        # Patrón de disparo según el tipo de movimiento
        if self.pattern == 0:  # Disparo triple
            projectiles.append(EnemyProjectile(self.rect.centerx - 30, self.rect.bottom))
            projectiles.append(EnemyProjectile(self.rect.centerx, self.rect.bottom))
            projectiles.append(EnemyProjectile(self.rect.centerx + 30, self.rect.bottom))
            
        elif self.pattern == 1:  # Disparo dirigido
            projectiles.append(EnemyProjectile(self.rect.centerx, self.rect.bottom))
            
        elif self.pattern == 2:  # Disparo en abanico
            for i in range(-2, 3):
                proj = EnemyProjectile(self.rect.centerx + i * 20, self.rect.bottom)
                projectiles.append(proj)

    def take_damage(self, damage):
        self.health -= damage
        return self.health <= 0

    def draw(self, screen):
        screen.blit(self.image, self.rect)
        
        # Barra de vida
        if self.active:
            bar_width = 120
            bar_height = 10
            health_percentage = max(0, self.health / self.max_health)
            pygame.draw.rect(screen, RED, (self.rect.centerx - bar_width//2, self.rect.top - 20, bar_width, bar_height))
            pygame.draw.rect(screen, GREEN, (self.rect.centerx - bar_width//2, self.rect.top - 20, int(bar_width * health_percentage), bar_height))

class Explosion:
    def __init__(self, x, y, size=50):
        # Crear explosión (círculos concéntricos)
        self.image = pygame.Surface((size, size), pygame.SRCALPHA)
        pygame.draw.circle(self.image, RED, (size//2, size//2), size//2)
        pygame.draw.circle(self.image, YELLOW, (size//2, size//2), size//3)
        pygame.draw.circle(self.image, WHITE, (size//2, size//2), size//5)
        self.rect = self.image.get_rect(center=(x, y))
        self.life_timer = 0.5
        
    def update(self, dt):
        self.life_timer -= dt
        return self.life_timer <= 0
        
    def draw(self, screen):
        screen.blit(self.image, self.rect)

class Star:
    def __init__(self):
        self.x = random.randint(0, WIDTH)
        self.y = random.randint(0, HEIGHT)
        self.size = random.randint(1, 3)
        self.speed = random.randint(50, 200)
        self.color = (random.randint(200, 255), random.randint(200, 255), random.randint(200, 255))
        
    def update(self, dt):
        self.y += self.speed * dt
        if self.y > HEIGHT:
            self.y = 0
            self.x = random.randint(0, WIDTH)
            
    def draw(self, screen):
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), self.size)

class Game:
    def __init__(self):
        print("Inicializando el juego...")
        # Configurar pantalla con opciones seguras
        try:
            # Primero intentar con el modo de pantalla normal
            self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
            pygame.display.set_caption("Space Shooter")
            print("Ventana del juego creada correctamente.")
        except pygame.error as e:
            print(f"Error al crear la ventana: {e}")
            # Intentar con opciones alternativas
            try:
                self.screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.SWSURFACE)
                pygame.display.set_caption("Space Shooter (SWSURFACE)")
                print("Ventana del juego creada con opciones alternativas.")
            except pygame.error as e2:
                print(f"Error crítico al crear la ventana: {e2}")
                sys.exit(1)
        
        # Inicializar reloj
        self.clock = pygame.time.Clock()
        
        # Cargar fondo (con manejo de errores)
        try:
            self.background = load_image("Espacio.png", WIDTH, HEIGHT)
            print("Fondo cargado correctamente.")
        except Exception as e:
            print(f"Error al cargar el fondo: {e}")
            # Crear un fondo de respaldo
            self.background = pygame.Surface((WIDTH, HEIGHT))
            self.background.fill((0, 0, 0))  # Fondo negro
            
        # Inicializar fuentes
        try:
            self.font_small = pygame.font.SysFont("Arial", 24)
            self.font_medium = pygame.font.SysFont("Arial", 36)
            self.font_large = pygame.font.SysFont("Arial", 72)
            print("Fuentes cargadas correctamente.")
        except Exception as e:
            print(f"Error al cargar fuentes: {e}")
            # Usar fuente predeterminada si hay error
            self.font_small = pygame.font.Font(None, 24)
            self.font_medium = pygame.font.Font(None, 36)
            self.font_large = pygame.font.Font(None, 72)
        
        # Estado del juego
        self.running = True
        self.game_state = "login"  # "login", "title", "playing", "paused", "game_over", "win", "highscores"
        
        # Estrellas para el fondo (menos para evitar sobrecarga)
        self.stars = [Star() for _ in range(50)]
        
        # Sistema de login
        self.email_input = InputBox(WIDTH//2 - 150, HEIGHT//2 - 20, 300, 40, "", "Ingresa tu correo electrónico")
        self.current_user_email = ""
        self.login_error = ""
        
        # Tabla de puntuaciones
        self.high_scores = []
        try:
            self.load_high_scores()
            print("Puntuaciones cargadas correctamente.")
        except Exception as e:
            print(f"Error al cargar puntuaciones: {e}")
        
        # Inicializar elementos del juego - al final para evitar problemas
        try:
            self.restart_game()
            print("Elementos del juego inicializados correctamente.")
        except Exception as e:
            print(f"Error al inicializar elementos del juego: {e}")

    def restart_game(self):
        # Jugador
        self.player = Player()
        
        # Entidades
        self.enemies = []
        self.player_projectiles = []
        self.enemy_projectiles = []
        self.explosions = []
        
        # Boss
        self.boss = None
        self.boss_spawned = False
        
        # Timers
        self.enemy_spawn_timer = 0
        
        # Estado del juego
        self.score = 0
        self.level = 1
        self.enemies_killed = 0
        self.enemies_for_boss = 5  # Reducido a 5 para que aparezca más rápido el jefe
        
    def load_high_scores(self):
        """Carga las mejores puntuaciones desde el archivo JSON"""
        self.high_scores = get_top_scores(10)
    
    def save_current_score(self):
        """Guarda la puntuación actual del jugador"""
        if self.current_user_email and self.player.score > 0:
            save_score(self.current_user_email, self.player.score)
            self.load_high_scores()
    
    def run(self):
        # Loop principal del juego
        last_state = None
        
        # Imprimir mensaje de inicio
        print("Iniciando bucle principal del juego...")
        
        try:
            while self.running:
                # Cálculo de delta time para movimientos suaves
                dt = self.clock.tick(FPS) / 1000
                
                # Manejar eventos (debe hacerse antes de actualizar el estado)
                self.handle_events()
                
                # Detectar cambios de estado para realizar acciones específicas
                if self.game_state != last_state:
                    print(f"Cambio de estado: {last_state if last_state else 'Ninguno'} -> {self.game_state}")
                    # Acciones específicas al cambiar de estado
                    if self.game_state == "playing" and last_state in [None, "title"]:
                        # Reiniciar timers al empezar a jugar desde el título
                        self.enemy_spawn_timer = ENEMY_SPAWN_INTERVAL
                    
                    # Guardar el nuevo estado como el último conocido
                    last_state = self.game_state
                
                # Actualizar y dibujar según el estado actual
                if self.game_state == "login":
                    self.update_login(dt)
                    self.draw_login()
                elif self.game_state == "title":
                    self.update_title()
                    self.draw_title()
                elif self.game_state == "playing":
                    self.update(dt)
                    self.draw()
                elif self.game_state == "paused":
                    self.draw_paused()
                elif self.game_state == "game_over":
                    self.update_game_over()
                    self.draw_game_over()
                elif self.game_state == "win":
                    self.update_win()
                    self.draw_win()
                elif self.game_state == "highscores":
                    self.update_highscores()
                    self.draw_highscores()
                    
                # Para debug, imprimir FPS cada 5 segundos
                if int(pygame.time.get_ticks() / 5000) % 2 == 0 and int(pygame.time.get_ticks() / 5000) != 0:
                    current_fps = self.clock.get_fps()
                    print(f"FPS: {current_fps:.1f}")
                    
        except Exception as e:
            print(f"Error en el bucle principal: {e}")
            import traceback
            traceback.print_exc()
        finally:
            # Asegurarse de que pygame se cierre correctamente
            print("Cerrando pygame...")
            pygame.quit()
            sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            # Manejar eventos de la caja de entrada de correo
            if self.game_state == "login":
                if self.email_input.handle_event(event):  # Si presiona Enter
                    email = self.email_input.text.strip()
                    if validate_email(email):
                        # Si es un correo válido
                        if not user_exists(email):
                            # Si es nuevo usuario, registrarlo
                            add_user(email)
                            print(f"Usuario {email} registrado correctamente.")
                        self.current_user_email = normalize_email(email)
                        self.login_error = ""
                        print(f"Sesión iniciada como {self.current_user_email}. ¡Iniciando juego!")
                        self.game_state = "title"  # Ir al menú principal en lugar de directamente al juego
                    else:
                        # Mensaje de error si el correo no es válido
                        self.login_error = "Correo electrónico inválido"
                        
            # Eventos de teclado generales
            if event.type == pygame.KEYDOWN:
                # Tecla Escape - Universal
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "playing" or self.game_state == "paused":
                        self.game_state = "title"
                    elif self.game_state == "title" or self.game_state == "highscores":
                        self.game_state = "login"
                    elif self.game_state != "login":  # No salir desde login
                        self.running = False
                    
                # Tecla V para pausar/reanudar en juego
                if event.key == pygame.K_v:
                    if self.game_state == "playing":
                        self.game_state = "paused"
                    elif self.game_state == "paused":
                        self.game_state = "playing"
            
                # Tecla B para volver al menú/login
                if event.key == pygame.K_b:
                    if self.game_state == "paused" or self.game_state == "highscores":
                        self.restart_game()
                        self.game_state = "title"
            
                # Tecla N para salir del juego
                if self.game_state == "highscores" and event.key == pygame.K_n:
                    self.running = False
            
                # Tecla H para ver tabla de puntuaciones
                if self.game_state == "title" and event.key == pygame.K_h:
                    self.game_state = "highscores"
                
                # Tecla Enter/Return para diversas acciones
                if event.key == pygame.K_RETURN:
                    if self.game_state == "title":
                        self.game_state = "playing"
                
                    elif self.game_state == "highscores":
                        if self.player.lives <= 0 or (self.boss_spawned and not self.boss):
                            self.restart_game()
                            self.game_state = "playing"
                        else:
                            self.game_state = "title"
                        
                    elif self.game_state == "game_over" or self.game_state == "win":
                        self.save_current_score()
                        self.load_high_scores()
                        self.game_state = "highscores"

    def update_login(self, dt):
        # Actualizar estrellas del fondo
        for star in self.stars:
            star.update(dt)
        
        # Actualizar la caja de texto
        self.email_input.update(dt)
    
    def update_highscores(self):
        # Actualizar estrellas del fondo
        for star in self.stars:
            star.update(1/FPS)
    
    def update_title(self):
        # Actualizar estrellas del fondo
        for star in self.stars:
            star.update(1/FPS)
    
    def update_game_over(self):
        # Actualizar estrellas del fondo
        for star in self.stars:
            star.update(1/FPS)
    
    def update_win(self):
        # Actualizar estrellas del fondo
        for star in self.stars:
            star.update(1/FPS)
    
    def update(self, dt):
        # Spawn de enemigos
        self.enemy_spawn_timer -= dt
        if self.enemy_spawn_timer <= 0 and len(self.enemies) < 5 and not self.boss:
            self.enemies.append(Enemy(random.randint(50, WIDTH - 50), random.randint(50, 200)))
            self.enemy_spawn_timer = ENEMY_SPAWN_INTERVAL
        
        # Movimiento del jugador
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]: dy = -PLAYER_SPEED
        if keys[pygame.K_s] or keys[pygame.K_DOWN]: dy = PLAYER_SPEED
        if keys[pygame.K_a] or keys[pygame.K_LEFT]: dx = -PLAYER_SPEED
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]: dx = PLAYER_SPEED
        self.player.move(dx, dy)
        
        # Disparos del jugador
        if keys[pygame.K_SPACE]:
            self.player.shoot(self.player_projectiles)
        
        # Actualizar jugador
        self.player.update(dt)
        
        # Comprobar fin del juego
        if self.player.lives <= 0:
            self.game_state = "game_over"
            return
            
        # Actualizar proyectiles del jugador
        for proj in self.player_projectiles[:]:
            if proj.update(dt):
                self.player_projectiles.remove(proj)
                
        # Actualizar proyectiles de enemigos
        for proj in self.enemy_projectiles[:]:
            if proj.update(dt):
                self.enemy_projectiles.remove(proj)
                
        # Actualizar enemigos
        for enemy in self.enemies[:]:
            enemy.update(self.player.rect.center, dt)
            
            # Disparos de enemigos
            if enemy.should_shoot():
                enemy.shoot(self.enemy_projectiles)
                
        # Actualizar boss
        if self.boss:
            self.boss.update(self.player.rect.center, dt, self.enemy_projectiles)
            
        # Actualizar explosiones
        for explosion in self.explosions[:]:
            if explosion.update(dt):
                self.explosions.remove(explosion)
                
        # Actualizar estrellas del fondo
        for star in self.stars:
            star.update(dt)
            
        # Comprobar colisiones
        self.check_collisions()
        
        # Comprobar spawn del boss
        if self.enemies_killed >= self.enemies_for_boss and not self.boss_spawned:
            print(f"¡El jefe ha aparecido! Enemigos eliminados: {self.enemies_killed}")
            self.boss = Boss()
            self.boss_spawned = True
            
        # Comprobar victoria
        if self.boss_spawned and not self.boss:
            print(f"¡VICTORIA! El jugador ha derrotado al jefe.")
            self.game_state = "win"
            
    def check_collisions(self):
        # Colisión proyectiles jugador con enemigos
        for proj in self.player_projectiles[:]:
            # Colisión con enemigos
            for enemy in self.enemies[:]:
                if proj.rect.colliderect(enemy.rect):
                    if enemy.take_damage(proj.damage):
                        self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
                        self.enemies.remove(enemy)
                        self.enemies_killed += 1
                        self.player.score += enemy.score_value
                    if proj in self.player_projectiles:
                        self.player_projectiles.remove(proj)
                    break
            
            # Colisión con boss
            if self.boss and proj.rect.colliderect(self.boss.rect):
                if self.boss.take_damage(proj.damage):
                    self.explosions.append(Explosion(self.boss.rect.centerx, self.boss.rect.centery, 100))
                    self.boss = None
                    self.player.score += 1000
                if proj in self.player_projectiles:
                    self.player_projectiles.remove(proj)
        
        # Colisión proyectiles enemigos con jugador
        for proj in self.enemy_projectiles[:]:
            if proj.rect.colliderect(self.player.rect):
                if self.player.take_damage(proj.damage):
                    self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery))
                self.enemy_projectiles.remove(proj)
        
        # Colisión jugador con enemigos
        for enemy in self.enemies[:]:
            if self.player.rect.colliderect(enemy.rect):
                if self.player.take_damage(30):
                    self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery))
                self.explosions.append(Explosion(enemy.rect.centerx, enemy.rect.centery))
                self.enemies.remove(enemy)
                self.enemies_killed += 1
                
        # Colisión jugador con boss
        if self.boss and self.player.rect.colliderect(self.boss.rect):
            if self.player.take_damage(50):
                self.explosions.append(Explosion(self.player.rect.centerx, self.player.rect.centery))
            
    def draw_login(self):
        try:
            # Dibujar fondo
            self.screen.fill((0, 0, 0))  # Primero rellenar con negro por si falla el fondo
            self.screen.blit(self.background, (0, 0))
            
            # Dibujar estrellas
            for star in self.stars:
                star.draw(self.screen)
                
            # Dibujar título
            title_text = self.font_large.render("SPACE SHOOTER", True, WHITE)
            title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3))
            self.screen.blit(title_text, title_rect)
            
            # Dibujar instrucciones
            instr_text = self.font_medium.render("Inicia sesión para jugar", True, WHITE)
            instr_rect = instr_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
            self.screen.blit(instr_text, instr_rect)
            
            # Dibujar caja de entrada de email
            self.email_input.draw(self.screen)
            
            # Mostrar mensaje de error si existe
            if self.login_error:
                error_text = self.font_small.render(self.login_error, True, RED)
                error_rect = error_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 30))
                self.screen.blit(error_text, error_rect)
            
            # Dibujar instrucciones adicionales
            help_text = self.font_small.render("Presiona ESC para salir", True, WHITE)
            help_rect = help_text.get_rect(center=(WIDTH//2, HEIGHT - 40))
            self.screen.blit(help_text, help_rect)
            
            # Actualizar la pantalla
            pygame.display.flip()
        except Exception as e:
            print(f"Error al dibujar pantalla de login: {e}")
    
    def draw_highscores(self):
        # Dibujar fondo
        self.screen.blit(self.background, (0, 0))
        
        # Dibujar estrellas
        for star in self.stars:
            star.draw(self.screen)
            
        # Dibujar título
        title_text = self.font_large.render("MEJORES PUNTUACIONES", True, WHITE)
        title_rect = title_text.get_rect(center=(WIDTH//2, 100))
        self.screen.blit(title_text, title_rect)
        
        # Dibujar puntuaciones
        y_pos = 180
        for i, (email, score) in enumerate(self.high_scores):
            # Acortar el email si es muy largo
            display_email = email
            if len(email) > 20:
                display_email = email[:17] + "..."
                
            score_text = self.font_medium.render(f"{i+1}. {display_email}: {score}", True, WHITE)
            score_rect = score_text.get_rect(center=(WIDTH//2, y_pos))
            self.screen.blit(score_text, score_rect)
            y_pos += 40
            
        # Destacar puntuación del jugador actual si está en la lista
        if self.current_user_email:
            for i, (email, score) in enumerate(self.high_scores):
                if email == self.current_user_email:
                    highlight_y = 180 + i * 40
                    pygame.draw.rect(self.screen, (255, 255, 0, 50), 
                                    pygame.Rect(WIDTH//2 - 200, highlight_y - 20, 400, 40), 2)
            
        # Dibujar instrucciones
        if self.game_state == "highscores" and (self.player.lives <= 0 or (self.boss_spawned and not self.boss)):
            instr_text = self.font_medium.render("Presiona ENTER para jugar de nuevo", True, WHITE)
        else:
            instr_text = self.font_medium.render("Presiona ENTER para volver", True, WHITE)
        instr_rect = instr_text.get_rect(center=(WIDTH//2, HEIGHT - 120))
        self.screen.blit(instr_text, instr_rect)
        
        # Nuevas opciones
        option_text1 = self.font_medium.render("B para volver a la pantalla de inicio", True, WHITE)
        option_rect1 = option_text1.get_rect(center=(WIDTH//2, HEIGHT - 80))
        self.screen.blit(option_text1, option_rect1)
        
        option_text2 = self.font_medium.render("N para salir del juego", True, WHITE)
        option_rect2 = option_text2.get_rect(center=(WIDTH//2, HEIGHT - 40))
        self.screen.blit(option_text2, option_rect2)
        
        pygame.display.flip()
    
    def draw_title(self):
        try:
            # Dibujar fondo
            self.screen.fill((0, 0, 0))  # Rellenar con negro primero
            self.screen.blit(self.background, (0, 0))
            
            # Dibujar estrellas
            for star in self.stars:
                star.draw(self.screen)
                
            # Dibujar título
            title_text = self.font_large.render("SPACE SHOOTER", True, WHITE)
            title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3))
            self.screen.blit(title_text, title_rect)
            
            # Dibujar mensaje de bienvenida con el email
            if self.current_user_email:
                welcome_text = self.font_medium.render(f"Bienvenido, {self.current_user_email}", True, WHITE)
                welcome_rect = welcome_text.get_rect(center=(WIDTH//2, HEIGHT//2 - 60))
                self.screen.blit(welcome_text, welcome_rect)
            
            # Dibujar opciones
            instr1_text = self.font_medium.render("Presiona ENTER para jugar", True, WHITE)
            instr1_rect = instr1_text.get_rect(center=(WIDTH//2, HEIGHT//2))
            self.screen.blit(instr1_text, instr1_rect)
            
            instr2_text = self.font_medium.render("Presiona H para ver puntuaciones", True, WHITE)
            instr2_rect = instr2_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 50))
            self.screen.blit(instr2_text, instr2_rect)
            
            instr3_text = self.font_medium.render("Presiona ESC para salir", True, WHITE)
            instr3_rect = instr3_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
            self.screen.blit(instr3_text, instr3_rect)
            
            # Actualizar pantalla
            pygame.display.flip()
        except Exception as e:
            print(f"Error al dibujar pantalla de título: {e}")
    
    def draw_paused(self):
        # Dibujar juego actual como fondo
        self.draw()
        
        # Dibujar overlay semitransparente
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 128))  # Negro semitransparente
        self.screen.blit(overlay, (0, 0))
        
        # Dibujar mensaje de pausa
        pause_text = self.font_large.render("PAUSA", True, WHITE)
        pause_rect = pause_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        self.screen.blit(pause_text, pause_rect)
        
        # Dibujar instrucciones
        instr_text = self.font_medium.render("Presiona V para continuar", True, WHITE)
        instr_rect = instr_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(instr_text, instr_rect)
        
        # Mostrar controles
        controls_text1 = self.font_small.render("ESC para volver al menú principal", True, WHITE)
        controls_rect1 = controls_text1.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
        self.screen.blit(controls_text1, controls_rect1)
        
        # Nueva opción - Volver a pantalla de inicio
        controls_text2 = self.font_small.render("B para volver a la pantalla de inicio", True, WHITE)
        controls_rect2 = controls_text2.get_rect(center=(WIDTH//2, HEIGHT//2 + 100))
        self.screen.blit(controls_text2, controls_rect2)
        
        pygame.display.flip()
    
    def draw_game_over(self):
        # Dibujar fondo
        self.screen.blit(self.background, (0, 0))
        
        # Dibujar estrellas
        for star in self.stars:
            star.draw(self.screen)
            
        # Dibujar título
        title_text = self.font_large.render("GAME OVER", True, RED)
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        self.screen.blit(title_text, title_rect)
        
        # Dibujar puntuación
        score_text = self.font_medium.render(f"Puntuación: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(score_text, score_rect)
        
        # Dibujar instrucciones
        instr_text = self.font_medium.render("Presiona ENTER para ver puntuaciones", True, WHITE)
        instr_rect = instr_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
        self.screen.blit(instr_text, instr_rect)
        
        pygame.display.flip()
        
    def draw_win(self):
        # Dibujar fondo
        self.screen.blit(self.background, (0, 0))
        
        # Dibujar estrellas
        for star in self.stars:
            star.draw(self.screen)
            
        # Dibujar título
        title_text = self.font_large.render("¡VICTORIA!", True, GREEN)
        title_rect = title_text.get_rect(center=(WIDTH//2, HEIGHT//3))
        self.screen.blit(title_text, title_rect)
        
        # Dibujar puntuación
        score_text = self.font_medium.render(f"Puntuación final: {self.player.score}", True, WHITE)
        score_rect = score_text.get_rect(center=(WIDTH//2, HEIGHT//2))
        self.screen.blit(score_text, score_rect)
        
        # Dibujar instrucciones
        instr_text = self.font_medium.render("Presiona ENTER para ver puntuaciones", True, WHITE)
        instr_rect = instr_text.get_rect(center=(WIDTH//2, HEIGHT//2 + 60))
        self.screen.blit(instr_text, instr_rect)
        
        pygame.display.flip()
        
    def draw(self):
        # Dibujar fondo
        self.screen.blit(self.background, (0, 0))
        
        # Dibujar estrellas
        for star in self.stars:
            star.draw(self.screen)
        
        # Dibujar proyectiles del jugador
        for proj in self.player_projectiles:
            proj.draw(self.screen)
            
        # Dibujar proyectiles enemigos
        for proj in self.enemy_projectiles:
            proj.draw(self.screen)
            
        # Dibujar jugador
        self.player.draw(self.screen)
        
        # Dibujar enemigos
        for enemy in self.enemies:
            enemy.draw(self.screen)
            
        # Dibujar boss
        if self.boss:
            self.boss.draw(self.screen)
            
        # Dibujar explosiones
        for explosion in self.explosions:
            explosion.draw(self.screen)
            
        # Dibujar información del jugador
        health_text = self.font_small.render(f"Salud: {self.player.health}", True, WHITE)
        self.screen.blit(health_text, (10, 10))
        
        lives_text = self.font_small.render(f"Vidas: {self.player.lives}", True, WHITE)
        self.screen.blit(lives_text, (10, 40))
        
        score_text = self.font_small.render(f"Puntuación: {self.player.score}", True, WHITE)
        self.screen.blit(score_text, (10, 70))
        
        pygame.display.flip()

if __name__ == "__main__":
    game = Game()
    game.run()