import pygame as pg
pg.init()

CHARACTER_SIZE = 55
WALL_SIZE = 55

characters = pg.sprite.Group()
traps = pg.sprite.Group()
items = pg.sprite.Group()
visuals = pg.sprite.Group()

font = pg.font.Font("assets/retro_font.ttf", 22)
