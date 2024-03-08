import pygame as pg
from copy import deepcopy

from shared import WALL_SIZE, CHARACTER_SIZE, characters, items, traps, visuals, decorations, walls, SCREEN_WIDTH, \
    SCREEN_HEIGHT, ground

pg.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


from characters import Player, Enemy, Merchant
from map_generation import connect_rooms, generate_level
from utility import Animated, Visual, load_images_from_folder, load_tileset, convert_csv_to_2d_list
from items import Chest, Key, Item
from traps import Trap, ArrowTrap, FlamethrowerTrap, SpikeTrap
from ui import display_ui, trim_matrix

clock = pg.time.Clock()

rooms = [i+1 for i in range(10)]
room_map = connect_rooms(rooms)
mini_map = trim_matrix(room_map)
discovered_mini_map = deepcopy(mini_map)
for y, row in enumerate(discovered_mini_map):
    for x, el in enumerate(row):
        if el != 1:
            discovered_mini_map[y][x] = 0

map_width_px, map_height_px = generate_level(room_map)



class Camera:
    def __init__(self, width, height):
        self.rect = pg.Rect(0, 0, width, height)

        self.width = width
        self.height = height
        self.initial_width = width
        self.initial_height = height

    def update(self, target):
        x = -target.rect.x + (SCREEN_WIDTH // 2)
        y = -target.rect.y + (SCREEN_HEIGHT // 2)

        x = min(0, x)
        y = min(0, y)
        x = max(-(self.width - SCREEN_WIDTH), x)
        y = max(-(self.height - SCREEN_HEIGHT), y)

        self.rect = pg.Rect(x, y, self.width, self.height)




player = Player(map_width_px//2 - CHARACTER_SIZE, map_height_px//2 - CHARACTER_SIZE)
merchant = Merchant(map_width_px//2 - CHARACTER_SIZE, map_height_px//2 - 220 - CHARACTER_SIZE)
ch1 = Enemy(map_width_px//2, map_height_px//2 + 250)

characters.add(player, ch1, merchant)

camera = Camera(map_width_px, map_height_px)

current_cell = room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
defeat_timer_start = pg.time.get_ticks()

running = True
while running:
    defeat_timer_seconds = 600 - (pg.time.get_ticks() - defeat_timer_start) // 1000

    fps = round(clock.get_fps())
    print(fps)

    action_objects = []
    for char in characters:
        if isinstance(char, Merchant):
            action_objects += char.items_to_sell


    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        keys = pg.key.get_pressed()
        if event.type == pg.KEYDOWN:
            dx, dy = 0, 0

            if keys[pg.K_e]:
                for obj in action_objects:
                    performed = obj.perform_action(player)

                    if performed:
                        break

            if keys[pg.K_UP] or keys[pg.K_DOWN] or keys[pg.K_RIGHT] or keys[pg.K_LEFT]:
                direction = [0, 0]

                if event.key == pg.K_UP:
                    direction = [0, 1]
                elif event.key == pg.K_DOWN:
                    direction = [0, -1]
                elif event.key == pg.K_RIGHT:
                    direction = [1, 0]
                elif event.key == pg.K_LEFT:
                    direction = [-1, 0]

                player.slash_attack(direction)

            if keys[pg.K_SPACE]:
                player.dash()

    keys = pg.key.get_pressed()

    dx = 1 if keys[pg.K_d] else -1 if keys[pg.K_a] else 0
    dy = 1 if keys[pg.K_w] else -1 if keys[pg.K_s] else 0

    if dx != 0 or dy != 0:
        player.move_player(dx, -dy, walls)

    screen.fill("#25141A")

    arrows = []
    [arrows.extend(trap.arrows) for trap in traps if hasattr(trap, 'arrows')]

    higher_order_traps = []
    spikes = []
    for trap in traps:
        if isinstance(trap, SpikeTrap):
            spikes.append(trap)
        else:
            higher_order_traps.append(trap)


    game_objs_groups = [ground, walls, decorations, spikes, items, characters, higher_order_traps, visuals, arrows]
    for group in game_objs_groups:
        for obj in group:
            screen.blit(obj.image, (obj.rect.x + camera.rect.x, obj.rect.y + camera.rect.y))

            if isinstance(obj, Merchant):
                obj.render_items(camera, player, screen)

    camera.update(player)

    for trap in traps:
        if player.rect.colliderect(trap.rect) and trap.damage > 0:
            if isinstance(trap, SpikeTrap) and player.rect.bottom - CHARACTER_SIZE >= trap.rect.top:
                continue

            player.take_damage(trap.damage)
            trap.already_hit = True

        if hasattr(trap, 'arrows'):
            for arrow in trap.arrows:
                if arrow.rect.colliderect(player.rect):
                    player.take_damage(1)
                    trap.already_hit = True
                    trap.arrows.remove(arrow)
                if any(arrow.rect.colliderect(wall) for wall in walls):
                    trap.arrows.remove(arrow)

    chests = []
    for item in items:
        if isinstance(item, Chest):
            chests.append(item)
        else:
            if item.rect.colliderect(player.rect):
                player.add_item(item)
                item.remove(items)

    for char in characters:
        # display health bar
        if isinstance(char, Enemy) and char.health < char.full_health:
            health_bar_length = 60
            health_bar_height = 10
            current_health_length = (char.health / char.full_health) * health_bar_length

            pos_x = char.rect.x - (health_bar_length - CHARACTER_SIZE) // 2 + camera.rect.x
            pos_y = char.rect.y - 14 - health_bar_height // 2 + camera.rect.y

            pg.draw.rect(screen, (0, 0, 0), (pos_x, pos_y, health_bar_length, health_bar_height))
            pg.draw.rect(screen, (255, 0, 0), (pos_x, pos_y, current_health_length, health_bar_height))

        for attack in char.attacks:
            dest = attack['dest']
            effect = pg.Surface(attack['dim'])
            dmg = attack['damage']

            attackRect = effect.get_rect()
            attackRect.x = dest[0]
            attackRect.y = dest[1]

            if char == player:
                for chest in chests:
                    if chest.rect.colliderect(attackRect):
                        chest.open()

            for testedChar in characters:
                if attackRect.colliderect(testedChar) and testedChar != char:
                    if testedChar == player:
                        player.take_damage(1)
                    else:
                        testedChar.health -= dmg
                        if isinstance(testedChar, Enemy) and testedChar.health <= 0:
                            characters.remove(testedChar)
                            images = load_images_from_folder("assets/effects/explosion")
                            visuals.add(Visual(images, testedChar.rect.inflate(20, 20), pg.time.get_ticks(), 400))
                    print('hit')

            char.attacks.remove(attack)

            images = load_images_from_folder("assets/effects/slash_attack")
            attackVisual = Visual(images, attackRect, attack['start_time'], attack['duration'], attack['flipped_x'], attack['flipped_y'])

            visuals.add(attackVisual)


    wx = len(room_map[0]) * 16
    wy = len(room_map) * 16

    new_cell = room_map[int(player.rect.y // WALL_SIZE // 16)][int(player.rect.x // WALL_SIZE // 16)]
    if current_cell != new_cell:
        for y, row in enumerate(mini_map):
            for x, el in enumerate(row):
                if el == new_cell:
                    discovered_mini_map[y][x] = new_cell

    current_cell = new_cell
    display_ui(screen, player.coins, player.health, discovered_mini_map, current_cell, player.number_of_keys, defeat_timer_seconds)

    visuals.update()
    decorations.update()
    traps.update(player)
    items.update(player)
    characters.update(walls, player.rect)

    pg.display.flip()
    clock.tick(60)

pg.quit()
