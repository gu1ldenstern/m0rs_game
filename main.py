from abc import ABC, abstractmethod
from enum import Enum
import random

import pyxel

WALKABLE_TILES = [(2, 10), (3, 10)]


def movement_allowed(x, y):
    left_leg_tile = pyxel.tilemap(0).pget(x // 8, y // 8 + 2)
    right_leg_tile = pyxel.tilemap(0).pget(x // 8 + 2, y // 8 + 2)
    return left_leg_tile in WALKABLE_TILES and right_leg_tile in WALKABLE_TILES


class Rotation(Enum):
    right = -1
    left = 1


class Direction(Enum):
    right = 1, 0
    left = -1, 0
    up = 0, -1
    down = 0, 1


class DogBreeds(Enum):
    ginger = 0, 96
    purple = 16, 96
    vsraty = 32, 96


def get_initial_coords():
    while True:
        x = random.randint(0, 47 * 8)
        y = random.randint(0, 15 * 8)
        if movement_allowed(x, y):
            return x, y


class Dog:
    def __init__(self):
        self.x, self.y = get_initial_coords()
        self.rotation = Rotation.right
        self.dog_breed = random.choice(list(DogBreeds))
        self.dead = -1
        self.dog_ttl = 30

    def move(self):
        if self.dead != -1:
            return

        new_x, new_y = self.x, self.y
        if self.rotation == Rotation.right:
            new_x += 1
        else:
            new_x -= 1

        if movement_allowed(new_x, new_y):
            self.x = new_x
            self.y = new_y
        else:
            self.rotation = (
                Rotation.left if self.rotation == Rotation.right else Rotation.right
            )

    def update(self):
        self.move()
        if self.dead > 0:
            self.dead -= 1

    def hit(self):
        self.dead = self.dog_ttl

    def is_alive(self):
        return self.dead == -1

    def is_dead(self):
        return self.dead == 0

    def get_burning_pic(self):
        ttl = self.dead // (self.dog_ttl / 10)
        if ttl > 4:
            if ttl % 2 == 1:
                return 0, 112
            else:
                return 16, 112
        if ttl >= 2:
            return 32, 112
        return 48, 112

    def draw(self, field_x, field_y):
        screen_x = self.x - field_x
        screen_y = self.y - field_y

        if self.dead > 0:
            u, v = self.get_burning_pic()
            pyxel.blt(
                screen_x, screen_y, 0, u, v, 16 * self.rotation.value, 16, colkey=0
            )
        else:
            pyxel.blt(
                screen_x,
                screen_y,
                0,
                self.dog_breed.value[0],
                self.dog_breed.value[1],
                16 * self.rotation.value,
                16,
                colkey=0,
            )


class IranMissiles:
    def __init__(self, m0rs_x, m0rs_y):
        self.x_current = m0rs_x + 4
        self.y_current = 0
        self.y_final = m0rs_y - 8
        self.explosion_longevity = 10
        self.countdown = self.explosion_longevity * 3 - 1
        self.counter = 0
        self.velocity = 3
        self.images = {
            0: {"x": 16, "y": 8},
            1: {"x": 48, "y": 8},
            2: {"x": 96, "y": 8},
        }

    def draw(self) -> bool:
        if self.y_current <= self.y_final:
            pyxel.blt(
                self.x_current,
                self.y_current,
                0,
                0,
                136,
                8,
                24,
                colkey=0,
            )
            self.counter += 1
            if self.counter % self.velocity == 0:
                self.y_current += 1
            return self.countdown
        if self.countdown != 0:
            image = self.images[self.countdown // self.explosion_longevity]
            pyxel.blt(
                self.x_current - 12,
                self.y_current,
                0,
                image["x"],
                image["y"],
                24,
                24,
                colkey=0,
            )
            self.countdown -= 1
        return self.countdown


class M0rs:
    def __init__(self, x=64, y=64):
        self.x = x
        self.y = y
        self.sprite_coords = (0, 16)
        self.dead = False
        self.missile = None
        self.lost = False

    def check_collision(self, dog):
        if not dog.is_alive():
            return False

        if (
            dog.x < self.x + 16
            and dog.x + 16 > self.x
            and dog.y < self.y + 16
            and dog.y + 16 > self.y
        ):
            self.dead = True
            return True

    def move(self, dx, dy):
        new_x = self.x + dx
        new_y = self.y + dy
        if movement_allowed(new_x, new_y) and not self.dead:
            self.x = new_x
            self.y = new_y
            return True
        return False

    def update(self, keys):
        if keys["up"]:
            self.move(0, -1)
        if keys["down"]:
            self.move(0, 1)
        if keys["left"]:
            self.move(-1, 0)
        if keys["right"]:
            self.move(1, 0)

    def draw(self, screen_x, screen_y):
        pyxel.blt(
            screen_x,
            screen_y,
            0,
            self.sprite_coords[0],
            self.sprite_coords[1],
            16,
            16,
            colkey=0,
        )
        if self.dead is True:
            if not self.missile:
                self.missile = IranMissiles(m0rs_x=screen_x, m0rs_y=screen_y)
            self.lost = self.missile.draw() == 0

    def check_win(self):
        return 32 <= self.y <= 64 and self.x == 479


class Shoot:
    def __init__(self, m0rs_x, m0rs_y, direction: Direction):
        self.x1 = m0rs_x + 5
        self.x2 = m0rs_x + 8
        self.y = m0rs_y + 19 - 16
        self.direction = direction
        self.hit_something = False

    def update(self):
        delta_x, delta_y = self.direction.value
        self.x1 += delta_x
        self.x2 += delta_x
        self.y += delta_y

    def is_out_of_bounds(self):
        return self.y <= 0 or self.x1 <= 0 or self.x2 <= 0

    def check_collision(self, dog, field_x, field_y):
        if not dog.is_alive():
            return False

        dog_screen_x = dog.x - field_x
        dog_screen_y = dog.y - field_y

        dog_x_min = dog_screen_x
        dog_x_max = dog_screen_x + 16
        dog_y_min = dog_screen_y
        dog_y_max = dog_screen_y + 16

        if (dog_x_min <= self.x1 <= dog_x_max and dog_y_min <= self.y <= dog_y_max) or (
            dog_x_min <= self.x2 <= dog_x_max and dog_y_min <= self.y <= dog_y_max
        ):
            dog.hit()
            self.hit_something = True
            return True
        return False

    def draw(self):
        pyxel.pset(self.x1, self.y, pyxel.COLOR_RED)
        pyxel.pset(self.x2, self.y, pyxel.COLOR_RED)


class Game(ABC):
    def __init__(self):
        self.m0rs = None

        self.game_over = False
        self.lost = False

        self.SCREEN_WIDTH = 128
        self.SCREEN_HEIGHT = 96
        self.FIELD_X = 0
        self.FIELD_Y = 0

    @abstractmethod
    def update(self):
        pass

    @abstractmethod
    def draw(self):
        pass


class Intro(Game):
    def draw(self):
        pyxel.bltm(0, 0, 0, 0, 40 * 8, self.SCREEN_WIDTH, self.SCREEN_WIDTH)

    def update(self):
        if pyxel.btnp(pyxel.KEY_SPACE):
            self.game_over = True


class Game1(Game):
    def __init__(self):
        super().__init__()
        self.m0rs = M0rs(64, 64 * 3)

        self.dogs = []
        self.DOG_COUNT = 300
        self.shots = []
        self.killed_dogs = 0

    def draw_buttom(self):
        pyxel.rect(0, 96, 128, 128, 1)
        text = f"killed dogs: {self.killed_dogs}"
        text_width = len(text) * 4
        x = (128 - text_width) // 2
        pyxel.text(x, 110, text, 7)

    def update(self):

        self.game_over = self.m0rs.check_win()

        keys = {
            "up": pyxel.btn(pyxel.KEY_W),
            "down": pyxel.btn(pyxel.KEY_S),
            "left": pyxel.btn(pyxel.KEY_A),
            "right": pyxel.btn(pyxel.KEY_D),
        }
        self.lost = self.m0rs.lost
        self.m0rs.update(keys)

        m0rs_screen_x = self.m0rs.x - self.FIELD_X
        m0rs_screen_y = self.m0rs.y - self.FIELD_Y

        shoot_keys = {
            pyxel.KEY_UP: Direction.up,
            pyxel.KEY_DOWN: Direction.down,
            pyxel.KEY_LEFT: Direction.left,
            pyxel.KEY_RIGHT: Direction.right,
        }

        for key, direction in shoot_keys.items():
            if pyxel.btn(key):
                self.shots.append(Shoot(m0rs_screen_x, m0rs_screen_y, direction))

        self.FIELD_X = self.m0rs.x - self.SCREEN_WIDTH // 2
        self.FIELD_Y = self.m0rs.y - self.SCREEN_HEIGHT // 2
        self.FIELD_X = max(0, self.FIELD_X)
        self.FIELD_Y = max(0, self.FIELD_Y)

        if not self.dogs:
            self.dogs = [Dog() for _ in range(self.DOG_COUNT)]

        for dog in self.dogs:
            dog.update()
            self.m0rs.check_collision(dog)

        self.dogs = [dog for dog in self.dogs if not dog.is_dead()]

        for shot in self.shots:
            shot.update()
            for dog in self.dogs:
                self.killed_dogs += shot.check_collision(
                    dog, self.FIELD_X, self.FIELD_Y
                )

        self.shots = [
            shot
            for shot in self.shots
            if not shot.is_out_of_bounds() and not shot.hit_something
        ]

    def draw(self):
        pyxel.cls(5)
        pyxel.bltm(
            0, 0, 0, self.FIELD_X, self.FIELD_Y, self.SCREEN_WIDTH, self.SCREEN_HEIGHT
        )

        m0rs_screen_x = self.m0rs.x - self.FIELD_X
        m0rs_screen_y = self.m0rs.y - self.FIELD_Y

        for dog in self.dogs:
            dog.draw(self.FIELD_X, self.FIELD_Y)

        for shot in self.shots:
            shot.draw()

        self.m0rs.draw(m0rs_screen_x, m0rs_screen_y)
        self.draw_buttom()


class Final(Game):
    def draw(self):
        pyxel.bltm(0, 0, 0, 0, 72 * 8, self.SCREEN_WIDTH, self.SCREEN_WIDTH)

    def update(self):
        pass


class M0rsNDA:
    def __init__(self):
        self.SCREEN_WIDTH = 128
        self.SCREEN_HEIGHT = 96

        self.current_game_index = 0
        self.current_game = None
        self.games = [Intro, Game1, Final]

        pyxel.init(128, 128)

        pyxel.load("my_resource.pyxres")

        self.start_next_game()
        pyxel.run(self.update, self.draw)

    def start_next_game(self):
        if self.current_game_index < len(self.games):
            game = self.games[self.current_game_index]
            self.current_game = game()

    def update(self):
        if pyxel.btnp(pyxel.KEY_Q) or pyxel.btnp(pyxel.KEY_ESCAPE):
            pyxel.quit()

        if self.current_game:
            self.current_game.update()

            if self.current_game.lost:
                if pyxel.btnp(pyxel.KEY_R):
                    self.current_game_index = 0
                    self.start_next_game()

            if self.current_game.game_over:
                self.current_game_index += 1
                self.start_next_game()

    def draw(self):
        if self.current_game.lost:
            pyxel.bltm(0, 0, 0, 0, 56 * 8, self.SCREEN_WIDTH, self.SCREEN_WIDTH)
        else:
            self.current_game.draw()


M0rsNDA()
