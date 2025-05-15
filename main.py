import arcade
from arcade.types import Color

from Obj import (
    Player, MovingObject, Mob2, Mob1, Artifact, Portal, Video,
    Noise
)
from settings import *
from sounds import *


DEBUG = False


class GameView(arcade.View):
    """
    Main application class.
    """

    def __init__(self): #отвечает за инициализацию основного игрового уровня или сцены
        super().__init__()

        # self.camera_sprites - основная камера для отображения игрового мира (спрайтов).
        # self.camera_bounds - границы камеры, ограничивают перемещение камеры размерами окна.
        # self.camera_gui - отдельная камера для элементов интерфейса (GUI), чтобы они оставались на месте при прокрутке игрового мира.
        self.camera_sprites = arcade.Camera2D()
        self.camera_bounds = self.window.rect
        self.camera_gui = arcade.Camera2D()
        #self.camera_shake - эффект "тряски" камеры
        self.camera_shake = arcade.camera.grips.ScreenShake2D(
            self.camera_sprites.view_data,
            max_amplitude=20.0,
            acceleration_duration=0.2,
            falloff_time=1,
            shake_frequency=10.0,
        )
        # The scene which helps draw multiple spritelists in order. self.scene - объект сцены, который управляет отображением различных списков спрайтов в нужном порядке.
        # self.a_list - отдельный список спрайтов (например, для определённой группы объектов).
        self.scene = self.create_scene()
        self.a_list = arcade.SpriteList()
        # Our physics engine.
        self.physics_engine = arcade.PhysicsEnginePlatformer(
            self.player, gravity_constant=GRAVITY, walls=self.scene["objects"], platforms=self.p_lst
        )
        #self.blood - спрайт с изображением крови.
        #self.blood_list - список, содержащий спрайты крови (для отображения эффекта при ранении).
        self.blood = arcade.Sprite('assets/sprites/Blood.png')
        self.blood_list = arcade.SpriteList()
        self.blood_list.append(self.blood)

        self.hint = arcade.Sprite('assets/sprites/hint.png') #- спрайт с подсказкой для игрока.
        self.hint.scale = (0.3, 0.3) # (0.3, 0.3) - уменьшение размера спрайта.
        self.hint_list = arcade.SpriteList() # список спрайтов для подсказок.
        self.hint_list.append(self.hint) # флаг, показывающий, активна ли подсказка.
        self.hint_active = True

        self.video = Video()
        self.video_list = arcade.SpriteList()
        self.video_list.append(self.video)

        self.noise = Noise()
        self.noise_list = arcade.SpriteList()
        self.noise_list.append(self.noise)
        self.end = False

    def create_scene(self) -> arcade.Scene:
        """Load the tilemap and create the scene object."""
        #Загружается карта уровней из файла map.json с масштабированием TILE_SCALING.
        #Для слоя "objects2" включается пространственный хешинг (use_spatial_hash=True), что ускоряет проверку столкновений.
        layer_options = {
            "objects2": {
                "use_spatial_hash": True,
            },
        }
        tile_map = arcade.load_tilemap(
            "map.json",
            scaling=TILE_SCALING,
            layer_options=layer_options,
        )

        start_sound('background_sound', loop=True)


        # Если в тайлмапе задан цвет фона, он устанавливается как цвет окна.
        if tile_map.background_color:
            self.window.background_color = Color.from_iterable(tile_map.background_color)

        # Use the tilemap's size to correctly set the camera's bounds.
        # Устанавливаются границы движения камеры по размерам карты и окна, чтобы камера не выходила за пределы игрового мира.
        self.camera_bounds = arcade.LRBT(
            self.window.width/2.0,
            tile_map.width * GRID_PIXEL_SIZE - self.window.width/2.0,
            self.window.height/2.0,
            tile_map.height * GRID_PIXEL_SIZE - self.window.height/2,
        )

        # Our Scene Object
        # Initialize Scene with our TileMap, this will automatically add all layers
        # Извлекается слой платформ "objects2" для дополнительной обработки.
        # Создаётся объект сцены из тайлмапа, автоматически добавляющий все слои как списки спрайтов.
        platforms = tile_map.object_lists["objects2"]
        del tile_map.object_lists["objects2"]
        scene = arcade.Scene.from_tilemap(tile_map)
        #Создание движущихся платформ. Для каждого объекта платформы создаётся спрайт. Устанавливаются физические свойства (масса, трение, упругость).
        #Позиция спрайта рассчитывается по координатам объекта. Создаётся объект MovingObject, который отвечает за движение платформы (например, вверх-вниз).
        #Платформы добавляются в список движущихся объектов, в сцену и в отдельный список платформ.
        self.moving_objects = []
        self.p_lst = arcade.SpriteList()
        for obj in platforms:
            sprite = arcade.Sprite(
                "assets/sprites/platform.png",
                scale=TILE_SCALING
                )

            # Координаты — можно использовать obj.x и obj.y, или obj.shape
            x1, y1 = obj.shape[0]
            x2, y2 = obj.shape[2]  # по диагонали

            sprite.mass = 1.0
            sprite.friction = 0.5
            sprite.elasticity = 0.3
            sprite.center_x = (x1 + x2) / 2 #Центр прямоугольной области
            sprite.center_y = (y1 + y2) / 2

            # Создаем объект движения (например, вверх-вниз на 100 пикселей, скорость 1)
            moving_object = MovingObject(
                sprite=sprite,
                speed=obj.properties['speed'],
                direction=[0, obj.properties['direction']],
                range_=obj.properties['range']  # Дальность движения по Y
            )

            self.moving_objects.append(moving_object) #Добавляет объект moving_object (обычно это игровой объект с логикой движения, например, движущаяся платформа) в список moving_objects.
            scene.add_sprite("moving_objects", sprite) #Добавляет спрайт sprite в сцену (scene) в слой с именем "moving_objects".
            self.p_lst.append(sprite) #Добавляет тот же спрайт sprite в отдельный список спрайтов p_lst, который используется для управления платформами

        #Аналогично платформам, создаются объекты врагов с разным классом в зависимости от направления движения.
        mobs = tile_map.object_lists['mobs']
        del tile_map.object_lists['mobs'] #После извлечения этот слой удаляется из объекта тайлмапа, чтобы избежать повторной обработки.
        self.mobs_spritelist = arcade.SpriteList() #Создаётся пустой список спрайтов self.mobs_spritelist, в который будут добавляться объекты врагов для удобного управления и отрисовки.
        for mob in mobs:
            x1, y1 = mob.shape[0]
            x2, y2 = mob.shape[2]
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            # Создаем объект движения
            direction = mob.properties['direction']
            if direction == 0:
                mob = Mob2(
                    x, y,
                    speed=mob.properties['speed'],
                    direction=[direction, 0],
                    range_=mob.properties['range']  # Дальность движения по Y
                )
                self.mob2 = mob
                self.mob2.can_attack = True

            else:
                mob = Mob1(
                    x, y,
                    speed=mob.properties['speed'],
                    direction=[direction, 0],
                    range_=mob.properties['range']  # Дальность движения по Y
                )
                self.mob1 = mob

            mob.position = (x, y)

            self.moving_objects.append(mob) #Враг добавляется в общий список движущихся объектов self.moving_objects для обновления логики движения.
            scene.add_sprite("mobs", mob) #Спрайт врага добавляется в сцену в слой "mobs" для отрисовки.
            self.mobs_spritelist.append(mob) #Враг добавляется в список спрайтов врагов self.mobs_spritelist для удобства управления и обработки столкновений.

        artifact = tile_map.object_lists['artifact']
        del tile_map.object_lists['artifact']
        for artifact in artifact:
            x1, y1 = artifact.shape[0]
            x2, y2 = artifact.shape[2]
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            artifact = Artifact(x, y)
            artifact.position = (x, y)

            self.moving_objects.append(artifact)
            scene.add_sprite("artifact", artifact)
            self.artifact = artifact


        portal = tile_map.object_lists['portal']
        del tile_map.object_lists['portal']
        for portal in portal:
            x1, y1 = portal.shape[0]
            x2, y2 = portal.shape[2]
            x = (x1 + x2) / 2
            y = (y1 + y2) / 2
            portal = Portal(x, y)
            portal.position = (x, y)

            self.moving_objects.append(portal)
            scene.add_sprite("portal", portal)
            self.portal = portal

        wall = tile_map.object_lists['wall']
        del tile_map.object_lists['wall']
        for wall in wall:
            if len(wall.shape) > 2:
                x1, y1 = wall.shape[0]
                x2, y2 = wall.shape[2]
                x = (x1 + x2) / 2
                y = (y1 + y2) / 2
                wall = arcade.Sprite('assets/sprites/stone.png', center_x=x, center_y=y)
                scene.add_sprite("wall", wall)

        #Создаётся объект игрока, устанавливается стартовая позиция и добавляется в сцену.
        self.player_list = arcade.SpriteList()
        self.player = Player()
        self.player.position = (180, 180)
        self.player_list.append(self.player)
        scene.add_sprite("player", self.player)

        return scene

    def reset(self):
        """предназначен для сброса игры к её исходному состоянию."""
        stop_all_sounds()
        self.__init__()


    def on_draw(self):
        """Render the screen."""

        # Clear the screen to the background color
        self.clear()
        self.camera_shake.update_camera()
        # Draw the map with the sprite camera
        with self.camera_sprites.activate():
            # Draw our Scene
            # Note, if you a want pixelated look, add pixelated=True to the parameters

            self.scene.draw()
            self.scene["moving_objects"].draw()
            self.scene["mobs"].draw()

            self.scene["player"].draw()
            self.scene["wall"].draw()
            if DEBUG:
                self.scene.draw_hit_boxes(
                    (255, 0, 0),
                    2,
                    names=[
                        'moving_objects',
                        'player',
                        'collisions',
                        'mobs',
                        'portal',
                        'artifact',
                    ]
                )


        # Draw the score with the gui camera
        with self.camera_gui.activate():
            # Draw our score on the screen. The camera keeps it in place.
            if not self.player.alive:
                self.blood_list.draw()
            elif self.hint_active:
                self.hint_list.draw()
            if self.end:
                self.video_list.draw()
            self.noise_list.draw()
        self.camera_shake.readjust_camera()

    def on_key_press(self, key, modifiers):
        """Called whenever a key is pressed."""

        if key == arcade.key.UP or key == arcade.key.W:
            if self.physics_engine.can_jump():
                start_sound('player_jump')
                self.player.jump()
        elif key == arcade.key.SPACE:
            attack_collision = self.player.attack()
            if attack_collision:
                start_sound('player_attack')
                self.a_list.append(attack_collision)
        elif key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.direction[0] = 1
            start_sound('player_walk', loop=True)
        elif key == arcade.key.LEFT or key == arcade.key.A:
            self.player.direction[0] = -1
            start_sound('player_walk', loop=True)
        elif key == arcade.key.R:
            self.reset()
        elif key == arcade.key.E and arcade.check_for_collision(self.player, self.artifact) and not self.mob1.alive:
            self.artifact.active()
            self.portal.active()
            start_sound('artifact_activate')
            self.camera_shake.start()
        elif key == arcade.key.TAB:
            self.hint_active = not self.hint_active

    def on_key_release(self, key, modifiers):
        """Called when the user releases a key."""
        if key == arcade.key.RIGHT or key == arcade.key.D:
            self.player.direction[0] = 0
            stop_sound('player_walk')
        if key == arcade.key.LEFT or key == arcade.key.A:
            self.player.direction[0] = 0
            stop_sound('player_walk')

    def center_camera_to_player(self):
        # Move the camera to center on the player
        self.camera_sprites.position = arcade.math.smerp_2d(
            self.camera_sprites.position,
            self.player.position,
            self.window.delta_time,
            FOLLOW_DECAY_CONST,
        )

        # Constrain the camera's position to the camera bounds.
        self.camera_sprites.view_data.position = arcade.camera.grips.constrain_xy(
            self.camera_sprites.view_data, self.camera_bounds
        )
        self.camera_gui.position = self.blood.position = self.noise.position = self.video.position = self.player.position
        self.hint.position = [
            self.player.position[0] + WINDOW_WIDTH // 2 - self.hint.width * 0.55,
            self.player.position[1] + WINDOW_HEIGHT // 2 - self.hint.height * 0.6
        ]

    def on_update(self, delta_time: float):
        """Movement and game logic"""

        # Move the player with the physics engine
        self.physics_engine.update()
        #Вызывает метод update() для всех движущихся объектов (платформы, враги, артефакты и т.д.), чтобы они изменяли своё состояние и позицию.
        for moving_object in self.moving_objects:
            moving_object.update()


        self.artifact.update()

        #Обновляет состояние игрока. Если метод update() возвращает True (например, игрок погиб или проиграл), вызывается метод reset() для перезапуска игры.
        if self.player.update():
            self.reset()

        #Если игрок попадает в зону видимости моба (view_collision), а моб ещё не агрессивен и жив, моб становится агрессивным (aggro()), меняет направление, если нужно, и проигрывает звук.
        #Если игрок сталкивается с мобом, который может атаковать, моб атакует, игрок погибает (kill()), и запускается эффект тряски камеры.
        for mob in self.mobs_spritelist:
            if mob.view_collision and arcade.check_for_collision(self.player, mob.view_collision) and not mob.is_aggro and mob.alive:
                mob.aggro()
                if mob.direction[0] == -1 and mob.position[0] < self.player.position[0] \
                        or mob.direction[0] == 1 and mob.position[0] > self.player.position[0]:
                    mob.direction[0] *= -1
                start_sound('mob1_exposure')

            elif arcade.check_for_collision(self.player, mob) and mob.alive and mob.can_attack:
                mob.attack()
                self.player.kill()
                self.camera_shake.start()

        #Если моб mob1 сталкивается с объектами из списка a_list, он погибает и проигрывается звук смерти.
        if arcade.check_for_collision_with_list(self.mob1, self.a_list) and not self.mob1.is_aggro and self.mob1.alive:
            self.mob1.kill()
            start_sound('mob1_die')

        #Если игрок касается активного портала, игра отмечается как завершённая (self.end = True), и проигрывается звук победы.
        if arcade.check_for_collision(self.player, self.portal) and self.portal.is_active:
            self.end = True
            if not self.video.is_active:
                start_sound('win')

        if self.end:
            self.video.update()

        self.noise.update()
        # Position the camera
        self.center_camera_to_player()
        self.camera_shake.update(delta_time)

        #Если включён режим отладки, в сцену добавляются спрайты для визуализации зон столкновений моба и (закомментировано) игрока.
        if DEBUG:
            self.scene.add_sprite("collisions", self.mob1.view_collision)
            # if self.player.attack_collision:
                # self.scene.add_sprite("collisions", self.player.attack_collision)

    #Метод on_resize(self, width: int, height: int) в библиотеке Arcade вызывается автоматически при изменении размера окна игры и служит для корректной обработки этого события.
    def on_resize(self, width: int, height: int):
        """ Resize window """
        #super().on_resize(width, height) - это важно, так как базовый метод обновляет внутренние параметры окна и системы координат. Без этого вызова координаты и отображение могут сбиться
        super().on_resize(width, height)

        # Update the cameras to match the new window size
        self.camera_sprites.match_window()
        # The position argument keeps `0, 0` in the bottom left corner.
        self.camera_gui.match_window(position=True)


def main():
    """Main function"""
    window = arcade.Window(WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE)
    game = GameView()

    window.show_view(game)
    arcade.run()


if __name__ == "__main__":
    main()