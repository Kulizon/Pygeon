import pygame as pg

SCREEN_WIDTH, SCREEN_HEIGHT = 1000, 700
pg.init()
screen = pg.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))


CHARACTER_SIZE = 65
WALL_SIZE = 65

characters = pg.sprite.Group()
traps = pg.sprite.Group()
items = pg.sprite.Group()
visuals = pg.sprite.Group()
walls = pg.sprite.Group()
ground = pg.sprite.Group()
decorations = pg.sprite.Group()

font = pg.font.Font("assets/retro_font.ttf", 22)
font_s = pg.font.Font("assets/retro_font.ttf", 16)






