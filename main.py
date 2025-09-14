# -*- coding: utf-8 -*-



import pgzrun
import random
import math
from pgzero.keyboard import keys
from pygame import Rect


WIDTH = 1152
HEIGHT = 864


HERO_HEALTH = 100
HERO_SPEED = 150
ENEMY_HEALTH = 50
ENEMY_SPEED = 70
ENEMY_ATTACK_DAMAGE = 10
PLAYER_SWORD_DAMAGE = 40
PLAYER_ATTACK_RANGE_MULTIPLIER = 1.6


ENEMY_AGGRO_RADIUS = 200
ENEMY_ATTACK_RADIUS = 30
ENEMY_ATTACK_COOLDOWN = 1.5
ENEMY_PERSONAL_SPACE_RADIUS = 25
ENEMY_SEPARATION_RADIUS = 25
ENEMY_SEPARATION_STRENGTH = 0.8
ENEMY_PATROL_SPEED = ENEMY_SPEED * 0.5
ENEMY_COUNT = 8


game_state = "menu"
is_paused = False
game_over_timer = 0
DEATH_TRANSITION_DELAY = 1.5
death_transition_timer = DEATH_TRANSITION_DELAY
mouse_pos = (0, 0)


music_on = True
music_volume = 0.15
sfx_volume = 0.3
FOOTSTEP_VOLUME_MULTIPLIER = 0.4
ADAGA_VOLUME = 0.5
SLIME_JUMP = 0.5
SLIME_SOUND =  0.32


HERO_IDLE_FRAMES = [f"idle{i}" for i in range(1, 11)]; HERO_WALK_FRAMES = [f"walk{i}" for i in range(1, 11)]; HERO_ATTACK_FRAMES = [f"attack{i}" for i in range(1, 6)]
HERO_IDLE_LEFT_FRAMES = [f"idle_left_{i}" for i in range(1, 11)]; HERO_WALK_LEFT_FRAMES = [f"walk_left{i}" for i in range(1, 11)]; HERO_ATTACK_LEFT_FRAMES = [f"attack_left{i}" for i in range(1, 6)]
HERO_DIE_FRAMES = [f"hero_die{i}" for i in range(1, 11)]; HERO_DIE_LEFT_FRAMES = [f"hero_die_left{i}" for i in range(1, 11)]
ENEMY_IDLE_LEFT_FRAMES = [f"enemy_idle{i}" for i in range(1, 11)]; ENEMY_WALK_LEFT_FRAMES = [f"enemy_walk{i}" for i in range(1, 11)]; ENEMY_ATTACK_LEFT_FRAMES = [f"enemy_attack{i}" for i in range(1, 8)]
ENEMY_IDLE_RIGHT_FRAMES = [f"enemy_idle_right{i}" for i in range(1, 11)]; ENEMY_WALK_RIGHT_FRAMES = [f"enemy_walk_right{i}" for i in range(1, 11)]; ENEMY_ATTACK_RIGHT_FRAMES = [f"enemy_attack_right{i}" for i in range(1, 8)]
ENEMY_DIE_FRAMES = [f"enemy_die{i}" for i in range(1, 9)]


SCENARIOS = ["background1"]
IDLE_ANIM_RATE = 10; WALK_ANIM_RATE = 6; ATTACK_ANIM_RATE = 5; ENEMY_ANIM_RATE = 8; DIE_ANIM_RATE = 8
start_pos = (150, 450)


wall_rects = [
    Rect(0, 20, 625, 130), Rect(0, 0, 10, 390), Rect(173, 220, 140, 180), Rect(0, 530, 260, 334), Rect(360, 670, 230, 33),
    Rect(700, 740, 100, 180), Rect(1100, 0, 50, 864), Rect(1070, 640, 25, 105), Rect(955, 740, 150, 115),
    Rect(0, 250, 50, 500), Rect(430, 0, 225, 340), Rect(570,0, 80, 490), Rect(650, 380, 180, 120), Rect(640, 534, 40, 82),
    Rect(380, 630, 196, 115), Rect(420, 614, 30, 131), Rect(505, 614, 27, 131), Rect(465, 550, 17, 205),
    Rect(640, 705, 40, 82), Rect(700, 500, 100, 115), Rect(955, 500, 180, 115), Rect(930, 380, 180, 120),
    Rect(0, 850, 1100, 40), Rect(0, 20, 1100, 40), Rect(1000, 30, 100, 83), Rect(960, 34, 15, 70), Rect(695, 121, 20, 60),
    Rect(680, 215, 50, 30), Rect(695, 293, 20, 40), Rect(1013, 202, 100, 105), Rect(270, 540, 50, 30),
    Rect(270, 588, 25, 50), Rect(538, 420, 25, 25), Rect(497, 380, 40, 5)
]


spawn_zones = [
    Rect(100, 150, 300, 100), Rect(500, 150, 350, 250), Rect(920, 400, 150, 200),
    Rect(400, 450, 500, 100), Rect(280, 400, 100, 150)
]


class Hero:
    """ Controla o jogador, incluindo movimento, ataques e animações. """
    def __init__(self, idle_frames, walk_frames, attack_frames, idle_left_frames, walk_left_frames, attack_left_frames, die_frames, die_left_frames, pos):
        
        self.idle_frames, self.walk_frames, self.attack_frames = idle_frames, walk_frames, attack_frames
        self.idle_left_frames, self.walk_left_frames, self.attack_left_frames = idle_left_frames, walk_left_frames, attack_left_frames
        self.die_frames, self.die_left_frames = die_frames, die_left_frames
        
        
        self.actor = Actor(idle_frames[0], pos)
        self.health, self.max_health, self.display_health = HERO_HEALTH, HERO_HEALTH, HERO_HEALTH
        self.is_attacking, self.is_walking, self.dealt_damage_this_swing, self.facing_left = False, False, False, False
        self.frame_index, self.anim_timer, self.is_dead, self.footsteps_playing = 0, 0, False, False

    @property
    def death_anim_finished(self):
        return self.is_dead and self.frame_index >= len(self.die_frames) - 1

    def update(self, dt):
        
        if self.display_health > self.health:
            self.display_health = max(self.health, self.display_health - 50 * dt)
        
        if self.is_dead:
            self.update_animation()
            return

        if self.health <= 0 and not self.is_dead:
            self.die()
        
        self.handle_input(dt)
        self.update_animation()
        
        
        if self.is_attacking and self.frame_index == 2 and not self.dealt_damage_this_swing:
            self.deal_damage()
            self.dealt_damage_this_swing = True

    def handle_input(self, dt):
        if self.is_attacking or self.is_dead:
            self.is_walking = False
            self.manage_footsteps()
            return

        old_x, old_y = self.actor.x, self.actor.y
        dx, dy = 0, 0
        
        if keyboard.left or keyboard.a: dx = -1; self.facing_left = True
        if keyboard.right or keyboard.d: dx = 1; self.facing_left = False
        if keyboard.up or keyboard.w: dy = -1
        if keyboard.down or keyboard.s: dy = 1

        if dx != 0 or dy != 0:
            self.is_walking = True
            factor = 0.707 if dx != 0 and dy != 0 else 1
            
            
            self.actor.x += dx * HERO_SPEED * dt * factor
            if self.actor.collidelist(wall_rects) != -1: self.actor.x = old_x
            
            self.actor.y += dy * HERO_SPEED * dt * factor
            if self.actor.collidelist(wall_rects) != -1: self.actor.y = old_y
        else:
            self.is_walking = False
        
        self.manage_footsteps()

    def manage_footsteps(self):
        try:
            if self.is_walking and not self.footsteps_playing:
                sounds.passos.play(-1)
                self.footsteps_playing = True
            elif not self.is_walking and self.footsteps_playing:
                sounds.passos.fadeout(300)
                self.footsteps_playing = False
        except Exception as e:
            print(f"Erro com som 'passos': {e}")

    def update_animation(self):
        if self.is_dead:
            death_frames = self.die_left_frames if self.facing_left else self.die_frames
            self.anim_timer += 1
            if self.anim_timer >= DIE_ANIM_RATE and self.frame_index < len(death_frames) - 1:
                self.anim_timer, self.frame_index = 0, self.frame_index + 1
            self.actor.image = death_frames[self.frame_index]
            return

        idle_frames, walk_frames, attack_frames = (self.idle_left_frames, self.walk_left_frames, self.attack_left_frames) if self.facing_left else (self.idle_frames, self.walk_frames, self.attack_frames)

        if self.is_attacking:
            self.anim_timer += 1
            if self.anim_timer >= ATTACK_ANIM_RATE:
                self.anim_timer, self.frame_index = 0, self.frame_index + 1
            if self.frame_index >= len(attack_frames):
                self.is_attacking, self.frame_index = False, 0
            self.actor.image = attack_frames[self.frame_index % len(attack_frames)]
        elif self.is_walking:
            self.anim_timer += 1
            if self.anim_timer >= WALK_ANIM_RATE:
                self.anim_timer, self.frame_index = 0, (self.frame_index + 1) % len(walk_frames)
            self.actor.image = walk_frames[self.frame_index]
        else:
            self.anim_timer += 1
            if self.anim_timer >= IDLE_ANIM_RATE:
                self.anim_timer, self.frame_index = 0, (self.frame_index + 1) % len(idle_frames)
            self.actor.image = idle_frames[self.frame_index]

    def die(self):
        self.is_dead, self.frame_index, self.anim_timer = True, 0, 0
        if self.footsteps_playing:
            try:
                sounds.passos.fadeout(300)
                self.footsteps_playing = False
            except Exception as e:
                print(f"Erro ao parar som 'passos': {e}")

    def attack(self):
        if not self.is_attacking and not self.is_walking and not self.is_dead:
            self.is_attacking, self.frame_index, self.anim_timer, self.dealt_damage_this_swing = True, 0, 0, False

    def deal_damage(self):
        global enemies
        hitbox_size = 60
        direction_x = -1 if self.facing_left else 1
        offset_x = self.actor.width / 2 * direction_x * PLAYER_ATTACK_RANGE_MULTIPLIER
        hitbox_x = self.actor.centerx + offset_x
        hitbox_y = self.actor.y
        attack_hitbox = Rect((0, 0), (hitbox_size, hitbox_size))
        attack_hitbox.center = (hitbox_x, hitbox_y)
        
        hit_occured = False
        for enemy in enemies:
            if enemy.health > 0 and attack_hitbox.colliderect(enemy.actor._rect):
                enemy.health -= PLAYER_SWORD_DAMAGE
                hit_occured = True
        
        if hit_occured:
            try:
                sounds.adagahit.play()
            except Exception as e:
                print(f"Erro com som 'adagahit': {e}")

    def draw(self):
        self.actor.draw()


class Enemy:
    """ Controla os inimigos, incluindo IA de patrulha, perseguição e separação. """
    def __init__(self, idle_left_frames, walk_left_frames, attack_left_frames, idle_right_frames, walk_right_frames, attack_right_frames, pos):
        
        self.idle_left_frames, self.walk_left_frames, self.attack_left_frames = idle_left_frames, walk_left_frames, attack_left_frames
        self.idle_right_frames, self.walk_right_frames, self.attack_right_frames = idle_right_frames, walk_right_frames, attack_right_frames
        
        
        self.actor = Actor(self.idle_left_frames[0], pos)
        self.health, self.max_health = ENEMY_HEALTH, ENEMY_HEALTH
        self.is_attacking, self.is_walking, self.facing_left = False, False, True
        self.attack_cooldown, self.frame_index, self.anim_timer = 0, 0, 0
        self.patrol_state, self.patrol_timer, self.patrol_dx, self.patrol_dy, self.death_anim_started = "idle", random.uniform(2, 5), 0, 0, False
        self.ambient_sound_timer = random.uniform(1, 3)

    @property
    def is_dying(self):
        return self.health <= 0

    def update(self, dt, player, all_enemies):
        if self.is_dying or hero.is_dead:
            self.is_walking = False
            self.update_animation()
            return

        old_x, old_y = self.actor.x, self.actor.y
        dx = player.actor.x - self.actor.x
        dy = player.actor.y - self.actor.y
        distance = math.sqrt(dx**2 + dy**2) if (dx != 0 or dy != 0) else 0
        self.attack_cooldown = max(0, self.attack_cooldown - dt)

        
        if distance < ENEMY_ATTACK_RADIUS and self.attack_cooldown == 0:
            self.is_walking = False
            self.attack(player)
        elif distance < ENEMY_AGGRO_RADIUS:
            
            player_dx, player_dy = 0, 0
            if distance > ENEMY_PERSONAL_SPACE_RADIUS:
                player_dx = dx / distance
                player_dy = dy / distance

            separation_dx, separation_dy = 0, 0
            for other_enemy in all_enemies:
                if other_enemy is not self and not other_enemy.is_dying:
                    dist_to_other = self.actor.distance_to(other_enemy.actor)
                    if dist_to_other < ENEMY_SEPARATION_RADIUS and dist_to_other > 0:
                        away_dx = self.actor.x - other_enemy.actor.x
                        away_dy = self.actor.y - other_enemy.actor.y
                        separation_dx += away_dx / dist_to_other
                        separation_dy += away_dy / dist_to_other

            final_dx = player_dx + (separation_dx * ENEMY_SEPARATION_STRENGTH)
            final_dy = player_dy + (separation_dy * ENEMY_SEPARATION_STRENGTH)
            final_magnitude = math.sqrt(final_dx**2 + final_dy**2)

            if final_magnitude > 0:
                self.is_walking = True
                norm_dx, norm_dy = final_dx / final_magnitude, final_dy / final_magnitude
                self.actor.x += norm_dx * ENEMY_SPEED * dt
                if self.actor.collidelist(wall_rects) != -1: self.actor.x = old_x
                self.actor.y += norm_dy * ENEMY_SPEED * dt
                if self.actor.collidelist(wall_rects) != -1: self.actor.y = old_y
            else:
                self.is_walking = False

            self.facing_left = (player.actor.x - self.actor.x) < 0
            
            
            self.ambient_sound_timer -= dt
            if self.ambient_sound_timer <= 0:
                self.play_random_ambient_sound()
                self.ambient_sound_timer = random.uniform(1, 3)
        else:
            
            self.patrol_timer -= dt
            if self.patrol_timer <= 0:
                if self.patrol_state == "idle":
                    self.patrol_state = "walking"; self.patrol_timer = random.uniform(2, 4)
                    angle = random.uniform(0, 2 * math.pi)
                    self.patrol_dx, self.patrol_dy = math.cos(angle), math.sin(angle)
                else:
                    self.patrol_state = "idle"; self.patrol_timer = random.uniform(3, 6)
                    self.patrol_dx, self.patrol_dy = 0, 0
            
            if self.patrol_state == "walking":
                self.is_walking = True
                self.actor.x += self.patrol_dx * ENEMY_PATROL_SPEED * dt
                if self.actor.collidelist(wall_rects) != -1: self.actor.x, self.patrol_timer = old_x, 0
                self.actor.y += self.patrol_dy * ENEMY_PATROL_SPEED * dt
                if self.actor.collidelist(wall_rects) != -1: self.actor.y, self.patrol_timer = old_y, 0
                self.facing_left = self.patrol_dx < 0
            else:
                self.is_walking = False
        
        self.update_animation()

    def update_animation(self):
        if self.is_dying:
            if not self.death_anim_started:
                self.frame_index, self.anim_timer, self.death_anim_started = 0, 0, True
            self.anim_timer += 1
            if self.anim_timer >= DIE_ANIM_RATE and self.frame_index < len(ENEMY_DIE_FRAMES) - 1:
                self.anim_timer, self.frame_index = 0, self.frame_index + 1
            self.actor.image = ENEMY_DIE_FRAMES[self.frame_index]
            return

        idle_frames, walk_frames, attack_frames = (self.idle_left_frames, self.walk_left_frames, self.attack_left_frames) if self.facing_left else (self.idle_right_frames, self.walk_right_frames, self.attack_right_frames)
        
        if self.is_attacking:
            self.anim_timer += 1
            if self.anim_timer >= ATTACK_ANIM_RATE:
                self.anim_timer = 0
                self.frame_index += 1
            if self.frame_index >= len(attack_frames):
                self.is_attacking, self.frame_index = False, 0
            self.actor.image = attack_frames[self.frame_index]
        elif self.is_walking:
            self.anim_timer += 1
            if self.anim_timer >= WALK_ANIM_RATE:
                self.anim_timer, self.frame_index = 0, (self.frame_index + 1) % len(walk_frames)
            self.actor.image = walk_frames[self.frame_index]
        else:
            self.anim_timer += 1
            if self.anim_timer >= IDLE_ANIM_RATE:
                self.anim_timer, self.frame_index = 0, (self.frame_index + 1) % len(idle_frames)
            self.actor.image = idle_frames[self.frame_index]

    def attack(self, player):
        if self.is_dying or hero.is_dead: return
        self.is_attacking, self.frame_index, self.anim_timer, self.attack_cooldown = True, 0, 0, ENEMY_ATTACK_COOLDOWN
        if self.actor.distance_to(player.actor) <= ENEMY_ATTACK_RADIUS + 20:
            player.health -= ENEMY_ATTACK_DAMAGE
        try:
            sounds.slimejump.play()
        except Exception as e:
            print(f"Erro com som 'slimejump': {e}")

    def play_random_ambient_sound(self):
        try:
            sound = getattr(sounds, random.choice(['slimesound1', 'slimesound2', 'slimesound3', 'slimesound4']))
            sound.play()
        except Exception as e:
            print(f"Erro com som de ambiente do slime: {e}")

    def draw(self):
        self.actor.draw()


def draw_health_bar(screen_obj, x, y, width, height, current_val, max_val, display_val=None):
    if current_val < 0: current_val = 0
    border_rect = Rect(x-2, y-2, width+4, height+4)
    background_rect = Rect(x, y, width, height)
    
    if display_val is not None:
        damage_fill_ratio = display_val / max_val
        damage_rect = Rect(x, y, width * damage_fill_ratio, height)
        screen_obj.draw.filled_rect(damage_rect, (255, 100, 100))

    current_fill_ratio = current_val / max_val
    foreground_rect = Rect(x, y, width * current_fill_ratio, height)
    
    health_color = "darkgreen"
    if current_fill_ratio < 0.5: health_color = "gold"
    if current_fill_ratio < 0.25: health_color = "firebrick"
    
    screen_obj.draw.filled_rect(background_rect, "black")
    screen_obj.draw.filled_rect(foreground_rect, health_color)
    screen_obj.draw.rect(border_rect, "darkgrey")

def reset_game():
    global enemies, death_transition_timer
    hero.health, hero.display_health, hero.actor.pos = HERO_HEALTH, HERO_HEALTH, start_pos
    enemies.clear()
    hero.is_dead, death_transition_timer = False, DEATH_TRANSITION_DELAY
    
    for _ in range(ENEMY_COUNT):
        while True:
            zone = random.choice(spawn_zones)
            pos = (random.randint(zone.left, zone.right), random.randint(zone.top, zone.bottom))
            spawn_check_rect = Rect(0, 0, 50, 50)
            spawn_check_rect.center = pos
            if spawn_check_rect.collidelist(wall_rects) == -1 and hero.actor.distance_to(pos) > 200:
                enemies.append(Enemy(ENEMY_IDLE_LEFT_FRAMES, ENEMY_WALK_LEFT_FRAMES, ENEMY_ATTACK_LEFT_FRAMES, ENEMY_IDLE_RIGHT_FRAMES, ENEMY_WALK_RIGHT_FRAMES, ENEMY_ATTACK_RIGHT_FRAMES, pos))
                break

def update_all_volumes():
    try:
        music.set_volume(music_volume if music_on else 0)
        sounds.adagahit.set_volume(sfx_volume * ADAGA_VOLUME)
        sounds.passos.set_volume(sfx_volume * FOOTSTEP_VOLUME_MULTIPLIER)
        sounds.slimejump.set_volume(sfx_volume *SLIME_JUMP)
        for i in range(1, 5):
            getattr(sounds, f"slimesound{i}").set_volume(sfx_volume * SLIME_SOUND)
    except Exception as e:
        print(f"Erro ao definir volumes: {e}")


hero = Hero(HERO_IDLE_FRAMES, HERO_WALK_FRAMES, HERO_ATTACK_FRAMES, HERO_IDLE_LEFT_FRAMES, HERO_WALK_LEFT_FRAMES, HERO_ATTACK_LEFT_FRAMES, HERO_DIE_FRAMES, HERO_DIE_LEFT_FRAMES, start_pos)
enemies = []

start_button = Rect(0, 0, 220, 60); start_button.center = (WIDTH//2, HEIGHT//2 - 40)
music_button = Rect(0, 0, 220, 60); music_button.center = (WIDTH//2, HEIGHT//2 + 40)
exit_button = Rect(0, 0, 220, 60); exit_button.center = (WIDTH//2, HEIGHT//2 + 220)
music_vol_down = Rect(0, 0, 60, 60); music_vol_down.center = (WIDTH//2 - 100, HEIGHT//2 + 110)
music_vol_up = Rect(0, 0, 60, 60); music_vol_up.center = (WIDTH//2 + 100, HEIGHT//2 + 110)
sfx_vol_down = Rect(0, 0, 60, 60); sfx_vol_down.center = (WIDTH//2 - 100, HEIGHT//2 + 170)
sfx_vol_up = Rect(0, 0, 60, 60); sfx_vol_up.center = (WIDTH//2 + 100, HEIGHT//2 + 170)



def draw():
    screen.clear()
    if game_state == "menu": draw_menu()
    elif game_state == "game": draw_game()
    elif game_state == "game_over": draw_game_over()
    elif game_state == "victory": draw_victory()

def update(dt):
    global game_state, death_transition_timer, game_over_timer, enemies, is_paused
    if game_state == "game" and not is_paused:
        hero.update(dt)
        for e in enemies: e.update(dt, hero, enemies)
        enemies = [e for e in enemies if not e.is_dying or e.frame_index < len(ENEMY_DIE_FRAMES) - 1]
        
        if hero.death_anim_finished:
            death_transition_timer -= dt
        if death_transition_timer <= 0:
            set_game_state("game_over")
        
        if not enemies and not hero.is_dead:
            set_game_state("victory")
            
    elif game_state == "game_over":
        game_over_timer += dt * 3

def on_key_down(key):
    global is_paused
    if key == keys.ESCAPE: exit()
    if game_state == "game":
        if key == keys.P:
            is_paused = not is_paused
            hero.manage_footsteps()
        if not is_paused:
            if key == keys.SPACE: hero.attack()

def on_mouse_down(pos):
    global music_on, music_volume, sfx_volume
    if game_state == "menu" or (game_state == "game" and is_paused):
        if game_state == "menu":
            if start_button.collidepoint(pos):
                try: sounds.start_game.play()
                except: pass
                set_game_state("game")
            elif music_button.collidepoint(pos):
                music_on = not music_on
                update_all_volumes()
            elif exit_button.collidepoint(pos):
                exit()
        
        if music_vol_down.collidepoint(pos): music_volume = max(0.0, round(music_volume - 0.1, 1)); update_all_volumes()
        elif music_vol_up.collidepoint(pos): music_volume = min(1.0, round(music_volume + 0.1, 1)); update_all_volumes()
        elif sfx_vol_down.collidepoint(pos): sfx_volume = max(0.0, round(sfx_volume - 0.1, 1)); update_all_volumes()
        elif sfx_vol_up.collidepoint(pos): sfx_volume = min(1.0, round(sfx_volume + 0.1, 1)); update_all_volumes()

    elif game_state in ("game_over", "victory"):
        set_game_state("menu")

def on_mouse_move(pos):
    global mouse_pos
    mouse_pos = pos



def draw_volume_controls(y_start):
    vol_controls = [
        (music_vol_down, music_vol_up, f"Música: {int(music_volume*100)}%", y_start),
        (sfx_vol_down, sfx_vol_up, f"Efeitos: {int(sfx_volume*100)}%", y_start + 60)
    ]
    for down_btn, up_btn, text, y_pos in vol_controls:
        down_btn.centery = y_pos
        up_btn.centery = y_pos
        for btn, label in [(down_btn, "-"), (up_btn, "+")]:
            color = "darkblue" if btn.collidepoint(mouse_pos) else (80,80,80)
            screen.draw.filled_rect(btn, color)
            screen.draw.rect(btn, "white")
            screen.draw.text(label, center=(btn.centerx, btn.centery-4), fontsize=40)
        screen.draw.text(text, center=(WIDTH//2, y_pos), fontsize=32)

def draw_menu():
    screen.blit(SCENARIOS[0], (0,0))
    screen.draw.filled_rect(Rect(0,0,WIDTH,HEIGHT), (0,0,0,180))
    screen.draw.text("Roguelike Adventure", center=(WIDTH//2, HEIGHT*0.2), fontsize=80, color="orange", shadow=(1,1), scolor="black")
    
    buttons = [(start_button, "Começar"), (music_button, f"Música: {'ON' if music_on else 'OFF'}"), (exit_button, "Sair")]
    for btn, text in buttons:
        color = "darkgreen" if btn.collidepoint(mouse_pos) else (80,80,80)
        screen.draw.filled_rect(btn, color)
        screen.draw.rect(btn, "white")
        screen.draw.text(text, center=btn.center, fontsize=32)
        
    draw_volume_controls(HEIGHT//2 + 110)
    
    screen.draw.text("Use WASD/Setas para mover, ESPAÇO para atacar.", center=(WIDTH//2, HEIGHT-60), fontsize=22, color="gray")
    screen.draw.text("Pressione 'P' para Pausar durante o jogo.", center=(WIDTH//2, HEIGHT-30), fontsize=22, color="gray")

def draw_game():
    screen.blit(SCENARIOS[0], (0,0))
    hero.draw()
    for e in enemies:
        e.draw()
        if not e.is_dying:
            draw_health_bar(screen, e.actor.x - 16, e.actor.y - 22, 32, 5, e.health, e.max_health)
            
    screen.draw.text("VIDA:", (20, 20), fontsize=30, color="white", owidth=1, ocolor="black")
    if not hero.is_dead:
        draw_health_bar(screen, 90, 25, 200, 20, hero.health, hero.max_health, hero.display_health)
        
    if is_paused:
        screen.draw.filled_rect(Rect(0,0,WIDTH,HEIGHT), (0,0,0,150))
        screen.draw.text("PAUSADO", center=(WIDTH//2, HEIGHT//2 - 80), fontsize=80, color="white", owidth=1.5, ocolor="black")
        draw_volume_controls(HEIGHT//2)

def draw_game_over():
    draw_game()
    screen.draw.filled_rect(Rect(0,0,WIDTH,HEIGHT), (0,0,0,150))
    hover_offset = math.sin(game_over_timer) * 5
    screen.draw.text("GAME OVER", center=(WIDTH//2, HEIGHT//2 - 40), fontsize=80, color="white", owidth=1.5, ocolor="black")
    screen.draw.text("Clique para voltar ao Menu", center=(WIDTH//2, HEIGHT//2 + 40 + hover_offset), fontsize=30, color="white", owidth=1.5, ocolor="black")

def draw_victory():
    screen.fill("darkgreen")
    screen.draw.text("VOCÊ VENCEU!", center=(WIDTH//2, HEIGHT//2 - 40), fontsize=80, color="white")
    screen.draw.text("Clique para voltar ao Menu", center=(WIDTH//2, HEIGHT//2 + 40), fontsize=30, color="white")

def set_game_state(state):
    global game_state, game_over_timer, is_paused
    
    if hero.footsteps_playing:
        try:
            sounds.passos.stop()
            hero.footsteps_playing = False
        except: pass
    
    if state == "game":
        reset_game()
        if music_on:
            try:
                music.play("dungeon_theme")
            except Exception as e:
                print(f"Erro ao tocar música de fundo: {e}")
    elif state in ("game_over", "victory", "menu"):
        try:
            music.stop()
        except: pass
        if state != "menu":
            game_over_timer = 0
    
    is_paused = False
    game_state = state
    update_all_volumes()


update_all_volumes()
pgzrun.go()