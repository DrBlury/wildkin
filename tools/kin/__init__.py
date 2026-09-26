"""The kin roster: one KinSpec per species, in id order (docs/EXPANSION.md 4).

Each batch module (base.py, normal_a.py, ...) owns a fixed id range and
defines SPECIES = [KinSpec(...), ...]. tools/gen_species.py writes the C
tables (src/species_data.h) and tools/gen_monsters.py draws the sprites from
the same specs, so data and art can never drift apart.

KinSpec fields
  id, name        fixed by the roster (name <= 10 characters, UPPERCASE)
  types           ('BLAZE',) or ('BLAZE', 'DUSK')
  rarity          'C' common, 'U' uncommon, 'R' rare, 'L' legend, 'F' fusion
  base            (HP, ATTACK, DEFENSE, FOCUS, WILL, SPEED)
  catch, xp       catch rate 3..255 (higher = easier), XP yield
  evo             None | ('LEVEL', 16, 'PYREFOX') | ('ITEM', 'BLOOM_SHARD', 'X')
                  | ('BOND', 0, 'X')   (bond >= 220 on a level-up)
  category        'LANTERN KIT' (the Almanac's "the ... kin")
  height, weight  decimetres, hectograms
  learnset        [(level, 'M_SWIPE'), ...] level 1 = known at the start
  traits          ('SURGE', 'EMBERSKIN') two TRAITS names
  desc            Almanac text (2-3 short sentences)
  field           field abilities: any of 'SURF', 'FLY', 'TELEPORT', 'LIGHT', 'STRENGTH'
  fusion          signature types for fusion kin: ('BLAZE', 'TIDE'), else None
  model           function -> gen_monsters.Model (the art); None = placeholder
"""

import importlib
import os
import re

TYPES = ['BEAST', 'BLAZE', 'TIDE', 'BLOOM', 'SPARK', 'FROST', 'BRAWL', 'VENOM', 'STONE', 'GALE',
         'DREAM', 'SWARM', 'DUSK', 'WYRM', 'HOLLOW', 'RELIC', 'METAL', 'ASTRAL']
RARITY = {'C': 'R_COMMON', 'U': 'R_UNCOMMON', 'R': 'R_RARE', 'L': 'R_LEGEND', 'F': 'R_FUSION'}
FIELD = ['SURF', 'FLY', 'TELEPORT', 'LIGHT', 'STRENGTH']
TRAIT_NAMES = ['SURGE', 'BRUISER', 'FOCUSED', 'KEEN EYE', 'THICK FUR', 'BEDROCK', 'DRIFTER',
               'SOAKER', 'CONDUCTOR', 'STATIC FUR', 'EMBERSKIN', 'SPORESKIN', 'WAKEFUL', 'SELFMEND',
               'BASKER', 'GLOWER', 'STUBBORN', 'MOMENTUM', 'HOARDER', 'QUICK STUDY', 'SLIPPERY']

# Base stat total ranges by tier (docs/EXPANSION.md 4).
BST = {'first': (280, 345), 'middle': (380, 435), 'final': (470, 535), 'single': (400, 485),
       'rare': (440, 545), 'fusion': (490, 565), 'legend': (570, 625)}

BATCHES = ['base', 'normal_a', 'normal_b', 'rare', 'legend', 'fusion_a', 'fusion_b']


class KinSpec:
    def __init__(self, id, name, types, rarity, base=None, catch=120, xp=100, evo=None,
                 category='', height=10, weight=100, learnset=None, traits=('KEEN EYE', 'THICK FUR'),
                 desc='', field=(), fusion=None, model=None, placeholder=False, concept=''):
        self.id, self.name, self.types, self.rarity = id, name, tuple(types), rarity
        self.base = tuple(base) if base else None
        self.catch, self.xp, self.evo = catch, xp, evo
        self.category, self.height, self.weight = category, height, weight
        self.learnset = list(learnset or [])
        self.traits, self.desc, self.field = tuple(traits), desc, tuple(field)
        self.fusion = tuple(fusion) if fusion else None
        self.model, self.placeholder, self.concept = model, placeholder, concept


def load():
    """All specs in id order (validated)."""
    specs = []
    for b in BATCHES:
        mod = importlib.import_module('kin.' + b)
        specs.extend(mod.SPECIES)
    specs.sort(key=lambda s: s.id)
    validate(specs)
    return specs


def move_names():
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
                        'src', 'game', 'moves.h')
    src = open(path).read()
    enum = src[src.index('M_BONK,'):]
    enum = enum[:enum.index('MOVE_COUNT')]
    return set(re.findall(r'\b(M_[A-Z0-9_]+)\b', enum))


def prevo_map(specs):
    pre = {}
    for s in specs:
        if s.evo:
            pre[s.evo[2]] = s.name
    return pre


def tier(s, specs):
    pre = prevo_map(specs)
    if s.rarity == 'L':
        return 'legend'
    if s.rarity == 'F':
        return 'fusion'
    has_pre, has_next = s.name in pre, bool(s.evo)
    if not has_pre and not has_next:
        return 'rare' if s.rarity == 'R' else 'single'
    if not has_pre:
        return 'first'
    return 'middle' if has_next else 'final'


def validate(specs):
    errs = []
    names = set()
    moves = move_names()
    sigs = set()
    for i, s in enumerate(specs):
        if s.id != i:
            errs.append('ids must run 0..N-1 without gaps: expected %d, got %d (%s)' % (i, s.id, s.name))
        if not re.fullmatch(r'[A-Z][A-Z0-9]{1,9}', s.name):
            errs.append('%s: name must be 2-10 UPPERCASE letters/digits' % s.name)
        if s.name in names:
            errs.append('%s: name used twice' % s.name)
        names.add(s.name)
        if not 1 <= len(s.types) <= 2 or any(t not in TYPES for t in s.types):
            errs.append('%s: bad types %r' % (s.name, s.types))
        if s.rarity not in RARITY:
            errs.append('%s: bad rarity %r' % (s.name, s.rarity))
        if not s.base or len(s.base) != 6 or not all(1 <= v <= 255 for v in s.base):
            errs.append('%s: base stats must be 6 values 1..255' % s.name)
        if not 3 <= s.catch <= 255:
            errs.append('%s: catch rate %d out of 3..255' % (s.name, s.catch))
        for t in s.traits:
            if t not in TRAIT_NAMES:
                errs.append('%s: unknown trait %s' % (s.name, t))
        if len(s.traits) != 2:
            errs.append('%s: needs exactly 2 traits' % s.name)
        for f in s.field:
            if f not in FIELD:
                errs.append('%s: unknown field ability %s' % (s.name, f))
        if not s.learnset or s.learnset[0][0] != 1:
            errs.append('%s: learnset must start with level-1 moves' % s.name)
        prev = 0
        for (lv, mv) in s.learnset:
            if mv not in moves:
                errs.append('%s: unknown move %s' % (s.name, mv))
            if lv < prev or not 1 <= lv <= 100:
                errs.append('%s: learnset levels must be ascending 1..100' % s.name)
            prev = lv
        if s.rarity == 'F':
            if not s.fusion or len(s.fusion) != 2 or any(t not in TYPES for t in s.fusion):
                errs.append('%s: fusion kin need a 2-type signature' % s.name)
            else:
                key = tuple(sorted(s.fusion))
                if key in sigs:
                    errs.append('%s: fusion signature %r used twice' % (s.name, s.fusion))
                sigs.add(key)
        elif s.fusion:
            errs.append('%s: only fusion kin have a signature' % s.name)
        if len(s.desc) > 180:
            errs.append('%s: description longer than 180 characters' % s.name)
    for s in specs:
        if s.evo:
            kind, param, into = s.evo
            if kind not in ('LEVEL', 'ITEM', 'BOND'):
                errs.append('%s: bad evo kind %s' % (s.name, kind))
            if into not in names:
                errs.append('%s: grows into unknown %s' % (s.name, into))
    for s in specs:
        if s.base and not s.placeholder and s.id >= 32:   # the original 32 are balanced by the sim
            lo, hi = BST[tier(s, specs)]
            t = sum(s.base)
            if not lo <= t <= hi:
                errs.append('%s: base stat total %d outside %d..%d for its tier (%s)' %
                            (s.name, t, lo, hi, tier(s, specs)))
    if errs:
        raise ValueError('kin roster:\n  ' + '\n  '.join(errs))
