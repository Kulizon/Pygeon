import math

from shared import SCREEN_WIDTH, SCREEN_HEIGHT, screen
import pygame as pg
from shared import font
from utility import Animated, load_images_from_folder, load_tileset


heart_image = pg.transform.scale(pg.image.load('assets/heart.png'), (30, 28))
coin_images = load_tileset("assets/coin.png", 13, 13)
coin_animated = Animated(coin_images, (30, 30), 200)
key_images = load_images_from_folder("assets/items_and_traps_animations/keys/silver_resized")
key_animated = Animated(key_images, (30, 22), 200)

def trim_matrix(matrix):
    min_row = len(matrix)
    max_row = 0
    min_col = len(matrix[0])
    max_col = 0

    for i in range(len(matrix)):
        for j in range(len(matrix[0])):
            if matrix[i][j] != 0:
                min_row = min(min_row, i)
                max_row = max(max_row, i)
                min_col = min(min_col, j)
                max_col = max(max_col, j)

    # Extract the trimmed matrix
    trimmed_matrix = []
    for i in range(min_row, max_row + 1):
        row = matrix[i][min_col:max_col + 1]
        trimmed_matrix.append(row)

    return trimmed_matrix


def display_health(health):
    for i in range(health):
        screen.blit(heart_image, (10 + i * 40, 10))


def display_coins(coins):
    screen.blit(coin_animated.image, (10, 50))
    text = font.render("0" * (3 - int(math.log10(coins+1))) + str(coins), True, (255, 255, 255))
    screen.blit(text, (50, 52))
    coin_animated.animate_new_frame()


def display_full_map(map, current_cell):
    gap = 5
    cell_size = 40
    map = trim_matrix(map)

    map_width = len(map[0]) * cell_size + (len(map[0]) - 1) * gap
    map_height = len(map) * cell_size + (len(map) - 1) * gap

    offset_x = (SCREEN_WIDTH - map_width) // 2
    offset_y = (SCREEN_HEIGHT - map_height) // 2

    bg_width = max(400, map_width + 100)
    bg_height = max(400, map_height + 100)

    pg.draw.rect(screen,(0, 0, 0), ((SCREEN_WIDTH - bg_width) // 2, (SCREEN_HEIGHT - bg_height) // 2, bg_width, bg_width))

    for y, row in enumerate(map):
        for x, cell in enumerate(row):
            display_x = offset_x + x * (cell_size + gap)
            display_y = offset_y + y * (cell_size + gap)

            color = (0, 0, 120) if cell == 0 else (255, 0, 0) if cell == current_cell else (0, 255, 0)
            pg.draw.rect(screen, color, (display_x, display_y, cell_size, cell_size))


def display_mini_map(map, current_cell):
    gap = 5
    screen_gap = 15
    mini_map_size = 140

    cell_position = [-1, -1]

    for y, row in enumerate(map):
        for x, cell in enumerate(row):
            if cell == current_cell:
                cell_position = [x, y]
                break

    mini_map = [[0 for _ in range(5)] for _ in range(5)]

    start_x = max(0, cell_position[0] - 2)
    end_x = min(len(map[0]), cell_position[0] + 3)
    start_y = max(0, cell_position[1] - 2)
    end_y = min(len(map), cell_position[1] + 3)

    center_x = 2
    center_y = 2

    for y in range(start_y, end_y):
        for x in range(start_x, end_x):
            mini_map[center_y - (cell_position[1] - y)][center_x - (cell_position[0] - x)] = map[y][x]

    cell_width = (mini_map_size - 2 * screen_gap) // (2 * 2 + 1)
    cell_height = (mini_map_size - 2 * screen_gap) // (2 * 2 + 1)

    map_size_px = (cell_width + gap) * 6
    cells_gap = screen_gap - (mini_map_size - map_size_px) // 2

    pg.draw.rect(screen, (0, 0, 0), (SCREEN_WIDTH - screen_gap - map_size_px, screen_gap, map_size_px, map_size_px))

    for y in range(5):
        for x in range(5):
            display_x = SCREEN_WIDTH - cells_gap - map_size_px + (x + 1) * (cell_width + gap)
            display_y = cells_gap + 2 + y * cell_height + gap * y
            cell_value = mini_map[y][x]
            color = (255, 0, 0) if cell_value == current_cell else (0, 255, 0) if cell_value != 0 else (0, 0, 0)
            pg.draw.rect(screen, color, (display_x, display_y, cell_width, cell_height))


def display_keys(number_of_keys):
    screen.blit(key_animated.image, (10, 92))

    text = font.render(str(number_of_keys), True, (255, 255, 255))
    screen.blit(text, (50, 90))

    key_animated.animate_new_frame()


def display_timer(timer_seconds):
    mini_map_size = 140
    screen_gap = 15

    seconds = timer_seconds % 60
    minutes = timer_seconds // 60

    text_color = (255, 0, 0) if minutes == 1 else (255, 255, 255)

    text = str(minutes) + ":"
    if seconds < 10:
        text += "0"
    text += str(seconds)

    text = font.render(text, True, text_color)
    screen.blit(text, (SCREEN_WIDTH - text.get_width() - screen_gap, mini_map_size + screen_gap + text.get_height()))


def display_fps(fps):
    screen_gap = 15

    text = font.render(str(fps), True, (0, 255, 0))
    screen.blit(text, (screen_gap, SCREEN_HEIGHT - text.get_height() - screen_gap))


def display_ui(coins, health, mini_map, current_cell, number_of_keys, timer_seconds, fps):
    display_health(health)
    display_coins(coins)
    display_keys(number_of_keys)
    display_timer(timer_seconds)
    display_mini_map(mini_map, current_cell)
    #display_full_map(mini_map, current_cell)
    display_fps(fps)