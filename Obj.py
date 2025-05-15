import arcade
from settings import *
from sounds import *


class Animation:
    def __init__(self, filepath, length, speed=5, reverse=False, stagger=False, stop=False, name=None, upscale=1):
        self.index = 0
        self.speed = speed
        self.length = length
        self.stagger = stagger
        self.stop = stop
        self.filepath = filepath
        self.name = name

        texture_pairs = []
        for i in range(1, length + 1):
            texture = arcade.load_texture(filepath.format(i))
            texture.size = (texture.size[0]*upscale, texture.size[1]*upscale)

            if reverse:
                texture_pairs.append(
                    (texture.flip_left_right(), texture)
                )
            else:
                texture_pairs.append(
                    (texture, texture.flip_left_right())
                )

        self.textures = texture_pairs

    def update(self):
        self.index += 1
        if self.index >= self.length * self.speed:
            self.index = 0
            if self.stop:
                return None

        frame = self.index // self.speed

        return self.textures[frame]

    def __getitem__(self, key):
        return self.textures[self.index]

    def __call__(self):
        self.index = 0


class BaseEntity(arcade.Sprite):
    def __init__(self):
        self.init_anims()
        super().__init__(scale=0.4)
        self.now_texture = self.idle_texture
        self.alive = True
        self.character_face_direction = 0


    def change_anim(self):
        # OVERRIDE
        pass

    def init_anims(self):
        # OVERRIDE
        pass

    def kill(self):
        if self.alive:
            self.alive = False
            self.now_texture = self.die_texture
            self.change_x = 0
            self.change_y = 0

    def update(self, *args, **kwargs):
        self.update_animation()

    def update_animation(self):
        # Figure out if we need to flip face left or right

        if self.change_x < 0 and self.character_face_direction == 0:
            self.character_face_direction = 1
        elif self.change_x > 0 and self.character_face_direction == 1:
            self.character_face_direction = 0

        self.change_anim()

        direction = self.character_face_direction
        anim = self.now_texture.update()

        if anim is None:
            name = self.now_texture.name
            self.now_texture = self.idle_texture
            anim = self.now_texture.update()
        else:
            name = None

        self.texture = anim[direction]

        return name


class Attack(arcade.Sprite):
    def __init__(self,x, y, path='assets/sprites/missing.png'):
        super().__init__(path, 0.4, x, y)



class Player(BaseEntity):
    def __init__(self):
        # Default to face-right
        self.character_face_direction = 0

        # Adjust the collision box. Default includes too much empty space
        # side-to-side. Box is centered at sprite center, (0, 0)
        self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]
        self.is_jump = False
        self.is_attack = False

        self.direction = [0, 0]

        super().__init__()
        self.attack_range = 500
        self.attack_collision = None

    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/Player/{}.png', 1)
        self.walk_texture = Animation('assets/sprites/Player/{}.png', 8)
        self.jump_texture = Animation('assets/sprites/Player/Jump/jump{}.png', 6, 10, stagger=False, stop=True, name='jump')
        self.attack_texture = Animation('assets/sprites/Player/player_attack/player_attack{}.png', 4, 10, stagger=True, stop=True, name='attack')
        self.die_texture = Animation('assets/sprites/Player/player_die/player_die{}.png', 9, 5, stagger=True, stop=True, name='die')
        self.died_texture = Animation('assets/sprites/Player/player_die/player_die9.png', 1, 5, stagger=True, stop=True, name='died')

    def update(self):
        if not self.now_texture.stagger and self.alive:
            if self.direction[0] == -1:
                self.change_x = -PLAYER_MOVEMENT_SPEED
            elif 1 == self.direction[0]:
                self.change_x = PLAYER_MOVEMENT_SPEED
            elif self.direction[0] == 0:
                self.change_x = 0

        anim_name = self.update_animation()

        if anim_name == 'jump':
            self.is_jump = False
        elif anim_name == 'attack':
            self.is_attack = False
            self.attack_collision.kill()
            self.attack_collision = None
        elif anim_name == 'die':
            return True

    def jump(self):
        if not self.now_texture.stagger and self.alive:
            self.change_y = PLAYER_JUMP_SPEED
            self.is_jump = True

    def attack(self):
        if not self.now_texture.stagger and self.alive:
            self.change_x = 0
            self.now_texture = self.attack_texture
            self.is_attack = True
            if self.character_face_direction == 0:
                self.attack_collision = Attack(
                    self.position[0], self.position[1]
                )
                # self.attack_collision.right = self.center_x  * 0.9
                return self.attack_collision
            else:
                self.attack_collision = Attack(
                    self.position[0], self.position[1]
                )
                # self.attack_collision.left = self.center_x * 0.9
                return self.attack_collision

    def change_anim(self):
        # Idle animation
        if not self.alive:
            return

        if self.is_attack:
            self.now_texture = self.attack_texture
        elif self.change_y != 0 and self.is_jump:
            self.now_texture = self.jump_texture
        elif self.change_x == 0:
            if not self.now_texture.stagger:
                self.now_texture()
            self.now_texture = self.idle_texture
            # return
        else:
            self.now_texture = self.walk_texture

        return


class MovingObject:
    def __init__(self, sprite, speed, direction, range_):
        self.sprite = sprite
        self.speed = speed
        self.direction = direction
        self.range = range_
        self.start_coords = [sprite.center_x, sprite.center_y]
        self.physics = True

    def update(self):
        if self.direction[1]:
            # Меняем направление, если вышли за пределы движения по Y
            if abs(self.sprite.center_y - self.start_coords[1]) >= self.range:
                self.direction[1] *= -1

            self.sprite.change_y = self.speed * self.direction[1]

        if self.direction[0]:
            if abs(self.sprite.center_x - self.start_coords[0]) >= self.range:
                self.direction[0] *= -1

            self.sprite.change_x = self.speed * self.direction[0]


class Mob2(BaseEntity):
    def __init__(self, x, y, speed, direction, range_):
        # Default to face-right
        self.speed = speed
        self.direction = direction
        self.range = range_
        self.start_coords = [x, y]
        self.is_attack = False
        self.is_aggro = False
        self.can_attack = False

        # Adjust the collision box. Default includes too much empty space
        # side-to-side. Box is centered at sprite center, (0, 0)
        self.points = [[-22, -64], [22, -64], [22, 28], [-22, 28]]

        self.direction = direction
        self.view_collision = None
        # Set up parent class
        super().__init__()

    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/mob2/idle/mob2_s{}.png', 4, 10)
        self.attack_texture = Animation('assets/sprites/mob2/attack/mob2_a{}.png', 5, stop=True, stagger=True)

    def create_view_collision(self, direction):
        self.view_collision = None

    def update(self):
        if not self.now_texture.stagger and self.alive:
            if self.direction[0]:
                if abs(self.center_x  - self.start_coords[0]) >= self.range:
                    self.direction[0] *= -1

                self.change_x = self.speed * self.direction[0]

            self.center_x += self.change_x

        self.create_view_collision(self.direction[0])
        anim_name = self.update_animation()
        if anim_name == 'attack':
            self.is_attack = False
        elif anim_name == 'die':
            arcade.Sprite.kill(self)
        elif anim_name == 'exposure':
            self.can_attack = True
            start_sound('mob1_run', loop=True)

    def play_attack_sound(self):
        start_sound('mob2_attack')

    def attack(self):
        if not self.now_texture.stagger and self.alive and self.can_attack:
            self.play_attack_sound()
            self.change_x = 0
            self.now_texture = self.attack_texture
            self.is_attack = True

    def change_anim(self):
        if not self.alive:
            return
        if self.is_attack:
            self.now_texture = self.attack_texture
        elif self.is_aggro:
            if self.now_texture.stagger:
                self.now_texture = self.exposure_texture
            else:
                self.now_texture = self.run_texture
        elif self.change_x == 0:
            self.now_texture = self.idle_texture

    def aggro(self):
        self.speed *= 3
        self.is_aggro = True
        self.now_texture = self.exposure_texture


class Mob1(Mob2):
    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/mob1/idle/mob2_walk{}.png', 2, 10, reverse=True)
        self.attack_texture = Animation('assets/sprites/mob1/attack/mob2_a{}.png', 5, reverse=True, stagger=True, stop=True, name='attack')
        self.die_texture = Animation('assets/sprites/mob1/mob1_die/mob1_die{}.png', 9, 10, reverse=True, stagger=True, stop=True, name='die')
        self.exposure_texture = Animation('assets/sprites/mob1/exposure/mob2_e{}.png', 10, 7, reverse=True, stagger=True, stop=True, name='exposure')
        self.run_texture = Animation('assets/sprites/mob1/run/mob2_run{}.png', 2, 5, reverse=True)

    def create_view_collision(self, direction):
        if self.view_collision:
            self.view_collision.remove_from_sprite_lists()
        x = self.position[0]
        if direction == -1:
            x -= (1080 * 0.1)
        else:
            x += (1080 * 0.1)
        self.view_collision = Attack(x, self.position[1], "assets/sprites/view_collision.png")

    def update(self):
        self.hit_box = arcade.hitbox.RotatableHitBox(self.texture.hit_box_points)
        self.hit_box.scale = (0.4, 0.4)
        super().update()


class Artifact(BaseEntity):
    def __init__(self, x, y):
        self.is_active = False
        super().__init__()

    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/artifact/idle/artifact1_{}.png', 6, speed=10)
        self.active_texture = Animation('assets/sprites/artifact/active/artifact2_{}.png', 16, speed=7, stop=True, name='active')
        self.missing_texture = Animation('assets/sprites/block.png', 1)

    def active(self):
        self.is_active = True
        self.now_texture = self.active_texture

    def update(self):
        anim_name = self.update_animation()
        if anim_name == 'active':
            self.now_texture = self.missing_texture

    def play_attack_sound(self):
        start_sound('mob1_attack')


class Portal(BaseEntity):
    def __init__(self, x, y):
        self.is_active = False
        super().__init__()

    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/block.png', 1, speed=100)
        self.active_texture = Animation('assets/sprites/portal/p_{}.png', 9, speed=7)

    def active(self):
        self.is_active = True
        self.now_texture = self.active_texture


class Video(BaseEntity):
    def __init__(self):
        self.is_active = False
        super().__init__()

    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/video/video ({}).jpg', 30, speed=3, stop=True, upscale=2.5, name='idle')
        self.final_texture = Animation('assets/sprites/video/video (30).jpg', 1, speed=3, upscale=2.5)

    def update(self):
        self.is_active = True
        anim_name = self.update_animation()
        if anim_name == 'idle':
            self.now_texture = self.final_texture


class Noise(BaseEntity):
    def init_anims(self):
        self.idle_texture = Animation('assets/sprites/noise/n_{}.png', 3, upscale=2.5)

