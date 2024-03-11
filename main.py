import pygame as pg

from game import Map, Game
from shared import CHARACTER_SIZE, characters, items, traps, visuals, decorations, walls, \
 ground, screen

from characters import Enemy, Merchant, Player
from utility import Visual, load_images_from_folder, ActionObject, Camera
from items import Chest
from traps import SpikeTrap
from ui import display_ui


pg.init()
clock = pg.time.Clock()
gmap = Map()
game = Game(gmap)

def generate_new_level(current_player):
    game_objs_grps = [ground, walls, decorations, items, traps, visuals]
    for grp in game_objs_grps:
        grp.empty()

    print(current_player)

    if not current_player:
        characters.empty()
    else:
        characters.remove([char for char in characters.sprites() if not isinstance(char, Player)])

    global gmap
    gmap = Map()

    global game
    game = Game(gmap, current_player)

running = True
while running:
    defeat_timer_seconds = 600 - (pg.time.get_ticks() - game.defeat_timer_start) // 1000

    fps = round(clock.get_fps())

    action_objects = []
    for char in characters:
        if isinstance(char, Merchant):
            action_objects += char.items_to_sell

    for tile in decorations:
        if issubclass(tile.__class__, ActionObject):
            action_objects.append(tile)


    for event in pg.event.get():
        if event.type == pg.QUIT:
            running = False

        keys = pg.key.get_pressed()
        if event.type == pg.KEYDOWN:
            dx, dy = 0, 0

            if keys[pg.K_e]:
                for obj in action_objects:
                    performed = obj.perform_action(game.player)

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

                game.player.slash_attack(direction, 0.5)

            if keys[pg.K_SPACE]:
                game.player.dash()

    keys = pg.key.get_pressed()

    dx = 1 if keys[pg.K_d] else -1 if keys[pg.K_a] else 0
    dy = 1 if keys[pg.K_w] else -1 if keys[pg.K_s] else 0

    game.player.move_player(dx, -dy)

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

    game_objs_grps = [ground, walls, decorations, spikes, items, characters, higher_order_traps, visuals, arrows]
    for group in game_objs_grps:
        for obj in group:
            screen.blit(obj.image, (obj.rect.x + game.camera.rect.x, obj.rect.y + game.camera.rect.y))

            if isinstance(obj, Merchant):
                obj.render_items(game.camera, game.player)

    game.camera.update(game.player)

    for trap in traps:
        if game.player.rect.colliderect(trap.rect) and trap.damage > 0:
            if isinstance(trap, SpikeTrap) and game.player.rect.bottom - CHARACTER_SIZE >= trap.rect.top:
                continue

            game.player.take_damage(trap.damage)
            trap.already_hit = True

        if hasattr(trap, 'arrows'):
            for arrow in trap.arrows:
                if arrow.rect.colliderect(game.player.rect):
                    game.player.take_damage(1)
                    trap.already_hit = True
                    trap.arrows.remove(arrow)
                if any(arrow.rect.colliderect(wall) for wall in walls):
                    trap.arrows.remove(arrow)

    chests = []
    for item in items:
        if isinstance(item, Chest):
            chests.append(item)
        elif item.pickable and item.rect.colliderect(game.player.rect):
            game.player.add_item(item)
            item.remove(items)

    for char in characters:
        # display health bar
        if isinstance(char, Enemy) and char.health < char.full_health:
            health_bar_length = 60
            health_bar_height = 10
            current_health_length = (char.health / char.full_health) * health_bar_length

            pos_x = char.rect.x - (health_bar_length - CHARACTER_SIZE) // 2 + game.camera.rect.x
            pos_y = char.rect.y - 14 - health_bar_height // 2 + game.camera.rect.y

            pg.draw.rect(screen, (0, 0, 0), (pos_x, pos_y, health_bar_length, health_bar_height))
            pg.draw.rect(screen, (255, 0, 0), (pos_x, pos_y, current_health_length, health_bar_height))

        for attack in char.attacks:
            dest = attack['dest']
            effect = pg.Surface(attack['dim'])
            dmg = attack['damage']

            attackRect = effect.get_rect()
            attackRect.x = dest[0]
            attackRect.y = dest[1]

            if char == game.player:
                for chest in chests:
                    if chest.rect.colliderect(attackRect):
                        chest.open()

            for testedChar in characters:
                if attackRect.colliderect(testedChar) and testedChar != char:
                    if testedChar == game.player:
                        game.player.take_damage(1)
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


    display_ui(game.player.coins, game.player.health, gmap.discovered_mini_map, gmap.current_mini_map_cell, game.player.number_of_keys, defeat_timer_seconds, fps)

    visuals.update()
    decorations.update()
    traps.update(game.player)
    items.update(game.player)
    characters.update(game.camera, game.player.rect)
    gmap.update(game.player)

    if game.player.is_next_level:
        game.player.is_next_level = False
        generate_new_level(game.player)

    pg.display.flip()
    clock.tick(60)

pg.quit()
