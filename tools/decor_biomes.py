"""Transparent biome objects; all shapes use their target tileset's native palette.

All dimensions are in 16px map cells. Hut roofs and canopies are upper-layer
silhouettes, not rectangular terrain stamps, so the floor shows around them.
"""
import math
from pixelart import Decor, Img, hash2


def ellipse(im, cx, cy, rx, ry, fill, edge=None):
    for y in range(max(0, cy-ry), min(im.h, cy+ry+1)):
        for x in range(max(0, cx-rx), min(im.w, cx+rx+1)):
            d = ((x-cx)/rx)**2 + ((y-cy)/ry)**2
            if d <= 1:
                im.set(x, y, edge if edge and d > .75 else fill)


def branch(im, x0, y0, x1, y1, width, fill, rim):
    n = max(abs(x1-x0), abs(y1-y0), 1)
    for i in range(n+1):
        x = x0 + (x1-x0)*i//n
        y = y0 + (y1-y0)*i//n
        im.rect(x-width//2, y-width//2, x+width//2, y+width//2, fill)
        im.set(x-width//2, y, rim)


def cactus(bloom=False):
    im = Img(16, 32)
    branch(im, 8, 27, 8, 7, 5, 'bio_jungle_mid', 'bio_jungle_dk')
    branch(im, 7, 18, 3, 18, 3, 'bio_jungle_lt', 'bio_jungle_dk')
    branch(im, 3, 19, 3, 12, 3, 'bio_jungle_mid', 'bio_jungle_dk')
    branch(im, 10, 15, 13, 15, 3, 'bio_jungle_lt', 'bio_jungle_dk')
    branch(im, 13, 16, 13, 10, 3, 'bio_jungle_mid', 'bio_jungle_dk')
    for y in range(9, 27, 4):
        im.set(9, y, 'bio_jungle_hi')
    ellipse(im, 8, 28, 5, 2, 'bio_desert_out')
    if bloom:
        ellipse(im, 8, 6, 3, 2, 'bio_desert_rust', 'bio_desert_hi')
    return im


def tuft():
    im = Img(16, 16)
    for x in (3, 6, 9, 12):
        branch(im, 8, 13, x, 7 + x%3, 1, 'bio_desert_rust', 'bio_desert_dk')
    return im


def hut(desert):
    im = Img(48, 48)
    outline = 'bio_desert_out' if desert else 'bio_jungle_out'
    roof = 'bio_desert_roof' if desert else 'bio_jungle_roof'
    roof_light = 'bio_desert_adobe_lt' if desert else 'bio_jungle_thatch_lt'
    wall = 'bio_desert_adobe' if desert else 'bio_jungle_wicker'
    dark = 'bio_desert_adobe_dk' if desert else 'bio_jungle_bark_dk'
    # Stepped unequal eaves and sloped sides make the roof a distinct silhouette.
    for y in range(4, 27):
        left = max(2, 23-(y-4)*2) if y < 15 else 2 + (y-15)//6
        right = min(45, 24+(y-4)*2) if y < 15 else 45-(y-15)//7
        im.rect(left, y, right, y, outline)
        if right-left > 3:
            im.rect(left+1, y, right-1, y, roof_light if y < 12 or y%6 == 2 else roof)
        if y > 17:
            for x in range(left+4, right-3, 6):
                im.set(x, y, dark)
    im.rect(8, 27, 39, 42, outline)
    im.rect(9, 28, 38, 40, wall)
    for x in range(12, 38, 8):
        im.rect(x, 29, x, 39, dark if desert else roof_light)
    im.rect(19, 33, 29, 43, outline)
    im.rect(20, 34, 28, 43, dark)
    im.set(27, 39, roof_light)
    im.rect(8, 43, 18, 44, dark)
    im.rect(30, 43, 39, 44, dark)
    return im


def cliff_hut():
    im = hut(True)
    colors = {
        'bio_desert_out': 'b_out', 'bio_desert_roof': 'p_red',
        'bio_desert_adobe_lt': 'white', 'bio_desert_adobe': 'wd_lt',
        'bio_desert_adobe_dk': 'wd_dk',
    }
    for y in range(im.h):
        for x in range(im.w):
            if im.get(x, y) is not None:
                im.set(x, y, colors[im.get(x, y)])
    return im


def well():
    im = Img(32, 32)
    ellipse(im, 16, 20, 12, 8, 'bio_desert_adobe', 'bio_desert_out')
    ellipse(im, 16, 18, 8, 4, 'bio_desert_water', 'bio_desert_adobe_dk')
    branch(im, 6, 19, 6, 5, 2, 'bio_desert_roof', 'bio_desert_out')
    branch(im, 26, 19, 26, 5, 2, 'bio_desert_roof', 'bio_desert_out')
    branch(im, 6, 5, 26, 5, 2, 'bio_desert_roof', 'bio_desert_out')
    return im


def jar():
    im = Img(16, 16)
    ellipse(im, 8, 9, 5, 5, 'bio_desert_adobe', 'bio_desert_out')
    im.rect(5, 3, 11, 4, 'bio_desert_roof')
    im.rect(6, 6, 7, 11, 'bio_desert_adobe_lt')
    return im


def canopy_caravan():
    im = Img(32, 32)
    for x in (4, 27):
        branch(im, x, 27, x, 12, 2, 'bio_desert_adobe_dk', 'bio_desert_out')
    for y in range(6, 17):
        half = 3 + (y-6)*11//10
        im.rect(16-half, y, 16+half, y, 'bio_desert_roof' if (y//3)%2 else 'bio_desert_hi')
        im.set(16-half, y, 'bio_desert_out')
        im.set(16+half, y, 'bio_desert_out')
    return im


def buttress():
    im = Img(32, 48)
    ellipse(im, 16, 14, 13, 12, 'bio_jungle_lt', 'bio_jungle_out')
    ellipse(im, 11, 8, 7, 5, 'bio_jungle_moss', 'bio_jungle_lt')
    branch(im, 16, 14, 17, 39, 6, 'bio_jungle_bark', 'bio_jungle_bark_dk')
    for end in ((3, 44), (29, 45), (9, 43)):
        branch(im, 17, 35, *end, 3, 'bio_jungle_bark', 'bio_jungle_bark_dk')
    return im


def vines():
    im = Img(16, 32)
    for x in (3, 9, 13):
        for y in range(0, 28):
            xx = x + round(math.sin(y*.3+x)*2)
            im.set(xx, y, 'bio_jungle_dk')
            if y % 6 == 2:
                ellipse(im, xx+2, y, 2, 1, 'bio_jungle_lt', 'bio_jungle_out')
    return im


def canopy():
    im = Img(48, 32)
    for x, y, rx, ry in ((12, 17, 11, 12), (25, 11, 14, 10), (37, 19, 10, 10)):
        ellipse(im, x, y, rx, ry, 'bio_jungle_mid', 'bio_jungle_out')
        ellipse(im, x-3, y-3, max(2, rx-5), max(2, ry-6), 'bio_jungle_hi', 'bio_jungle_lt')
    for x in range(3, 45):
        for y in range(3, 29):
            if im.get(x, y) and hash2(x, y, 12)%31==0:
                im.set(x, y, 'bio_jungle_moss')
    return im


def orchid():
    im = Img(16, 16)
    branch(im, 8, 14, 8, 6, 1, 'bio_jungle_lt', 'bio_jungle_dk')
    for x, y in ((5, 5), (11, 5), (8, 3), (6, 8), (10, 8)):
        ellipse(im, x, y, 2, 2, 'bio_jungle_pink', 'bio_jungle_bloom')
    im.set(8, 6, 'bio_jungle_moss')
    return im


def root_bridge():
    im = Img(32, 16)
    for y in (5, 8, 11):
        branch(im, 1, y+1, 30, y-1, 2, 'bio_jungle_bark', 'bio_jungle_bark_dk')
    for x in (5, 13, 22, 28):
        im.set(x, 6, 'bio_jungle_moss')
    return im


def cascade(frame=0):
    im = Img(32, 32)
    for y in range(2, 29):
        for x in range(5, 27):
            edge = x in (5, 26)
            im.set(x, y, 'w_hi' if edge or y > 24 and (x+frame)%4 < 3 else
                   'w_lt' if (x+y*2+frame*4)%7 < 2 else
                   'w_dk' if x%5==0 else 'w_base')
    for x in range(2, 30):
        im.set(x, 30-(x%3), 'w_hi')
    return im


def river_foam():
    im = Img(32, 16)
    for x in range(32):
        for y in range(16):
            d = y-7-2*math.sin(x*.31)
            if abs(d)<1.5 and hash2(x,y,4)%4:
                im.set(x,y,'w_hi')
            elif 1.5<abs(d)<3 and hash2(x,y,7)%5==0:
                im.set(x,y,'w_lt')
    return im


def coral():
    im = Img(32, 32)
    ellipse(im, 16, 27, 12, 3, 's_base', 's_dk')
    for a,b,c,d in ((15,27,11,6),(17,25,23,4),(13,20,4,13),(20,17,27,13)):
        branch(im,a,b,c,d,3,'f_red','f_redd')
        ellipse(im,c,d,3,2,'f_red','f_redd')
    for x,y in ((11,7),(22,6),(5,13),(26,14)):
        im.set(x,y,'white')
    return im


def cairn():
    im=Img(16,32)
    for cy,rx,ry in ((26,7,4),(19,6,4),(12,4,3),(6,3,2)):
        ellipse(im,8,cy,rx,ry,'rk_lt','rk_dk')
        im.set(6,cy-1,'rk_hi')
        im.set(9,cy-2,'sn_hi')
    return im


def fungus():
    im=Img(32,32)
    for cx, cy, rx in ((9,15,7),(23,19,6),(16,10,5)):
        branch(im,cx,cy,cx,29,2,'mo_base','mo_dk')
        ellipse(im,cx,cy,rx,4,'cr_base','cr_dk')
        ellipse(im,cx-2,cy-2,max(2,rx-3),1,'cr_hi')
        for x in range(cx-rx+2,cx+rx-1,3):
            im.set(x,cy,'cr_lt')
    return im


def signal_bell():
    im = Img(16, 32)
    branch(im, 2, 29, 2, 4, 2, 'wd_base', 'wd_dk')
    branch(im, 13, 29, 13, 4, 2, 'wd_base', 'wd_dk')
    im.rect(1, 3, 14, 5, 'wd_dk')
    im.rect(2, 3, 13, 3, 'wd_lt')
    im.rect(7, 5, 8, 8, 'b_out')
    for y in range(8, 20):
        half = 2 + (y - 8) // 4
        im.rect(8 - half, y, 8 + half, y, 'b_out')
        im.rect(9 - half, y, 7 + half, y, 'p_yel')
        im.set(9 - half, y, 'white')
    im.rect(3, 20, 13, 21, 'p_yel')
    im.rect(4, 22, 12, 22, 'b_out')
    im.rect(7, 22, 8, 25, 'st_mid')
    return im


def biome_waypost(desert):
    prefix = 'bio_desert_' if desert else 'bio_jungle_'
    outline = prefix + 'out'
    wood = prefix + ('adobe_dk' if desert else 'bark_dk')
    face = prefix + ('adobe' if desert else 'roof')
    light = prefix + ('adobe_lt' if desert else 'thatch_lt')
    im = Img(16, 16)
    im.rect(7, 8, 9, 15, wood)
    im.rect(1, 2, 14, 10, outline)
    im.rect(2, 3, 13, 9, face)
    im.rect(3, 3, 12, 3, light)
    im.rect(4, 5, 10, 5, wood)
    im.rect(4, 7, 8, 7, wood)
    return im


DECOR = [
    Decor('DESERT_WAYPOST', ['desert'], biome_waypost(True), doc='carved oasis directions; 1x1 solid'),
    Decor('JUNGLE_WAYPOST', ['jungle'], biome_waypost(False), doc='woven leaf waymarker; 1x1 solid'),
    Decor('TOWN_CLIFF_HUT', ['town'], cliff_hut(), top='XXX/XXX/...', solid='.../.../XXX',
          doc='closed cliffside timber storehouse; 3x3 with irregular red roof'),
    Decor('TOWN_SIGNAL_BELL', ['town'], signal_bell(), top='X/.', solid='./X',
          doc='Mistbell signal bell on a timber frame; 1x2, lower cell solid'),
    Decor('DESERT_CACTUS', ['desert'], cactus(), top='X/.', doc='two-arm saguaro; 1x2, lower cell solid'),
    Decor('DESERT_CACTUS_BLOOM', ['desert'], cactus(True), top='X/.', doc='flowering saguaro; 1x2, lower cell solid'),
    Decor('DESERT_DUNE_TUFT', ['desert'], tuft(), solid='.', doc='dry dune sedge; 1x1 walkable'),
    Decor('DESERT_ADOBE_HUT', ['desert'], hut(True), top='XXX/XXX/...', solid='.../.../X.X',
          doc='irregular adobe shelter; 3x3, open central doorway'),
    Decor('DESERT_WELL', ['desert'], well(), top='XX/..', doc='oasis well with arched rim; 2x2'),
    Decor('DESERT_JAR', ['desert'], jar(), doc='water jar; 1x1'),
    Decor('DESERT_CARAVAN_CANOPY', ['desert'], canopy_caravan(), top='XX/..', solid='../XX',
          doc='striped asymmetrical shade canopy; 2x2'),
    Decor('JUNGLE_BUTTRESS', ['jungle'], buttress(), top='XX/XX/..', doc='exposed buttress roots and crown; 2x3'),
    Decor('JUNGLE_VINES', ['jungle'], vines(), top='X/.', solid='./.', doc='hanging vines; 1x2, walkable'),
    Decor('JUNGLE_CANOPY', ['jungle'], canopy(), top='XXX/XXX', solid='.../...',
          doc='three overlapping crowns; 3x2, overhead'),
    Decor('JUNGLE_WOVEN_HUT', ['jungle'], hut(False), top='XXX/XXX/...', solid='.../.../X.X',
          doc='uneven woven shelter; 3x3, open central doorway'),
    Decor('JUNGLE_ORCHID', ['jungle'], orchid(), solid='.', doc='pink orchid; 1x1 walkable'),
    Decor('JUNGLE_ROOT_BRIDGE', ['jungle'], root_bridge(), floor='XX', solid='..',
          doc='root lattice over water; 2x1 walkable bridge'),
    Decor('WILD_WATERFALL', ['wild'], frames=[cascade(f) for f in range(3)], period=16,
          solid='../..', doc='falling white cascade; 2x2, animated water overlay'),
    Decor('WILD_RIVER_FOAM', ['wild'], river_foam(), solid='..',
          doc='broken white river-foam line; 2x1 walkable overlay'),
    Decor('COAST_CORAL_CLUSTER', ['coast'], coral(), top='XX/..',
          doc='branching coral reef on a stone foot; 2x2'),
    Decor('SNOW_CAIRN', ['snow'], cairn(), top='X/.', doc='frosted trail cairn; 1x2'),
    Decor('CAVE_FUNGAL_SHELF', ['cave'], fungus(), top='XX/..',
          doc='luminous tiered fungal shelf; 2x2'),
]
