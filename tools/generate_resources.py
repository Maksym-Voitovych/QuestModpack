#!/usr/bin/env python3
"""Reproduce the AIA2 32px RGBA pixel-art set. Requires Pillow; no source art needed.

The 48 keys use individually composed silhouettes and native-resolution pixel
facets. Chapter badges embed a nearest-neighbor miniature of their own key.
"""
from pathlib import Path
import hashlib
import json
import math

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'kubejs/assets/kubejs'
NAMES = [
    'Кореневий кремінь', 'Мідний водоворот', 'Ковальська обітниця', 'Серце андезиту',
    'Паросток мани', 'Бронзовий регулятор', 'Тотем сутінків', 'Сталева відьомська печать',
    'Руна живої землі', 'Латунний гримуар', 'Іскра першої мережі', 'Нафтовий компас',
    'Алхімічний вольт', 'Пневматичний виклик', 'Печатка пекельного знання', 'Осмієвий резонатор',
    'Цифровий архів', 'Полімерна спіраль', 'Душа сплаву', 'Арканний автоматон',
    'Ельфійська корона', 'Грозовий трансформатор', 'Призма збагачення', 'Розумна плата',
    'Роботизований тигель', 'Зерно відтворення', 'Життєва матриця', 'Вузол світових ліній',
    'Реакторний акорд', 'Око кінцевої межі', 'Воля Ґаї', 'Вінець високої напруги',
    'Радіохімічна капсула', 'Сплав далеких світів', 'Надпровідна решітка', 'Термоядерний тороїд',
    'Місячний астролябій', 'Планетарний атлас', 'Антиматеріальний розлом', 'Крило виверни',
    'Пробуджене драконяче серце', 'Фрактал Хаосу', 'Еволюційний механізм', 'Планетарна кузня',
    'Терези трансмутації', 'Нейтронна сингулярність', 'Космічна конвергенція', 'Вінець нескінченності',
]
KINDS = ('tech_matrix', 'arcane_catalyst', 'convergence_core', 'epoch_seal')
KIND_UK = {'tech_matrix': 'Матриця ремесла', 'arcane_catalyst': 'Арканний каталізатор',
           'convergence_core': 'Осередок узгодження', 'epoch_seal': 'Печатка випробування'}
SECTIONS = {'epochs': 'Епохи', 'technology': 'Технології', 'magic': 'Магія',
            'adventure': 'Пригоди', 'collection': 'Колекції'}


def color(hexval):
    return tuple(bytes.fromhex(hexval)) + (255,)


PALETTES = [
    ('755038', 'bc8550', 'edca89', '587c38', 'a5d65a'),
    ('71452d', 'c77e43', 'ffd794', '357e80', '73e4d1'),
    ('485162', '8997a6', 'e3e8ec', '4e8078', 'a7e5b4'),
    ('5c556c', 'a79bac', 'ede1ca', '7651ad', 'cf9dff'),
    ('75602a', 'c2a34d', 'fff0a6', '25687c', '70d6f2'),
    ('3c5a68', '779ca8', 'd5eced', '844c92', 'f1a4db'),
    ('4e496d', '9d8bb6', 'e8dbff', '256d75', '89f3dc'),
    ('574354', 'af8388', 'ffe6bc', '9b3569', 'ff8fcf'),
    ('4c4e73', '969ccb', 'f1ecff', '3e74a1', '9fe9ff'),
    ('603948', 'c17a57', 'fff3b6', 'ad3f27', 'ffd472'),
    ('41446e', '9d94d0', 'f0e9ff', '74309c', 'e48dff'),
    ('4f4b68', 'afadc8', 'fff7d5', '387d95', 'a3ffed'),
]


class Pixel:
    def __init__(self, n):
        self.im = Image.new('RGBA', (32, 32))
        self.d = ImageDraw.Draw(self.im)
        self.dark = color('171c2b')
        self.shadow, self.metal, self.light, self.deep, self.glow = [color(x) for x in PALETTES[(n-1)//4]]
        self.white = color('ffffe8')

    def box(self, xy, fill, outline=None, width=1):
        self.d.rectangle(xy, fill=fill, outline=outline, width=width)

    def line(self, points, fill=None, width=1):
        self.d.line(points, fill=fill or self.light, width=width)

    def poly(self, pts, fill=None, outline=True):
        self.d.polygon(pts, fill=fill or self.metal)
        if outline:
            self.d.line(pts+[pts[0]], fill=self.dark, width=1)

    def ring(self, x, y, radius, width=3, octagonal=False):
        if octagonal:
            def pts(r):
                return [(round(x+math.cos(math.pi/8+i*math.pi/4)*r),
                         round(y+math.sin(math.pi/8+i*math.pi/4)*r)) for i in range(8)]
            self.poly(pts(radius), self.metal)
            self.poly(pts(radius-width), (0,0,0,0))
            self.line([(x-radius+2,y-2),(x-radius+2,y-4),(x-3,y-radius+2)], self.light)
        else:
            self.d.ellipse((x-radius,y-radius,x+radius,y+radius),fill=self.dark)
            self.d.ellipse((x-radius+1,y-radius+1,x+radius-1,y+radius-1),fill=self.metal)
            self.d.ellipse((x-radius+width,y-radius+width,x+radius-width,y+radius-width),fill=(0,0,0,0))
            self.d.arc((x-radius+1,y-radius+1,x+radius-1,y+radius-1),190,275,fill=self.light,width=1)
            self.d.arc((x-radius+1,y-radius+1,x+radius-1,y+radius-1),10,90,fill=self.shadow,width=1)

    def gem(self, x, y, rx=4, ry=6):
        self.poly([(x,y-ry),(x+rx,y-2),(x+rx,y+ry-2),(x,y+ry),(x-rx,y+2),(x-rx,y-ry+2)],self.deep)
        self.poly([(x,y-ry+1),(x+rx-1,y-2),(x,y+ry-1),(x-1,y)],self.glow,False)
        self.line([(x-1,y-ry+3),(x-1,y),(x-rx+1,y+1)],self.white)
        self.line([(x+rx-1,y),(x+1,y+ry-2)],self.deep)

    def spark(self,x,y):
        self.line([(x-1,y),(x+1,y)],self.glow)
        self.line([(x,y-1),(x,y+1)],self.glow)
        self.box((x,y,x,y),self.white)

    def bolt(self,x,y):
        self.box((x-1,y-1,x+1,y+1),self.dark)
        self.box((x,y-1,x+1,y),self.light)
        self.box((x,y,x,y),self.metal)

    def shaft(self,x,y,length=15,teeth=2):
        self.box((x-2,y,x+2,y+length),self.dark)
        self.box((x-1,y,x+1,y+length-1),self.metal)
        self.line([(x-1,y+1),(x-1,y+length-1)],self.light)
        for k in range(teeth):
            sy=y+length-3-k*4
            self.box((x+2,sy,x+5,sy+2),self.dark)
            self.box((x+2,sy,x+4,sy+1),self.metal)
            self.box((x+2,sy,x+4,sy),self.light)

    def gear(self,x,y,r=8,teeth=8):
        points=[]
        for j in range(teeth*4):
            a=j*math.tau/(teeth*4)-math.pi/2
            rad=r if j%4 in (1,2) else r-2
            points.append((round(x+math.cos(a)*rad),round(y+math.sin(a)*rad)))
        self.poly(points)
        self.ring(x,y,r-3,2)
        for a in range(0,360,90):
            rad=math.radians(a)
            xx=round(x+math.cos(rad)*(r-1)); yy=round(y+math.sin(rad)*(r-1))
            self.box((xx,yy,xx,yy),self.light)

    def circuit(self,x,y,w=10,h=8):
        self.box((x,y,x+w,y+h),self.dark)
        self.box((x+1,y+1,x+w-1,y+h-1),self.deep)
        self.line([(x+2,y+2),(x+w-3,y+2),(x+w-3,y+h-2)],self.glow)
        self.line([(x+2,y+h-2),(x+4,y+h-2),(x+4,y+4),(x+w-2,y+4)],self.metal)
        for a in range(2,w-1,3):
            self.line([(x+a,y-1),(x+a,y)],self.light)
            self.line([(x+a,y+h),(x+a,y+h+1)],self.light)

    def leaf(self,x,y,direction=1):
        self.poly([(x,y),(x+direction*1,y-4),(x+direction*6,y-6),
                   (x+direction*5,y-2)],self.deep)
        self.line([(x,y-1),(x+direction*4,y-4)],self.glow)

    def rune(self,x,y,seed):
        # Each compact rune has a stem and two independently placed angular arms.
        self.line([(x,y),(x,y+4)],self.glow)
        self.line([(x,y+(seed%3)),(x+2,y+(seed%3)-1)],self.glow)
        self.line([(x,y+3),(x-2,y+2+seed%2)],self.glow)

    def feather(self,pts):
        self.poly(pts,self.metal)
        self.line([pts[0],pts[-2]],self.light)

    def finish(self):
        """One-pixel metal bevels, placed at native resolution without blur."""
        original=self.im.copy()
        for y in range(1,31):
            for x in range(1,31):
                value=original.getpixel((x,y))
                if value!=self.metal:continue
                top=original.getpixel((x,y-1));left=original.getpixel((x-1,y))
                below=original.getpixel((x,y+1));right=original.getpixel((x+1,y))
                if top==self.dark or left==self.dark:
                    self.im.putpixel((x,y),self.light)
                elif below==self.dark or right==self.dark:
                    self.im.putpixel((x,y),self.shadow)
                elif (x*7+y*11)%43==0:
                    self.im.putpixel((x,y),self.light)
        return self.im


def key_art(n):
    p=Pixel(n)
    # Forty-eight intentionally different compositions: key, vessel, tablet,
    # instrument, ring, creature, engine, and celestial artifact forms.
    if n==1:
        p.poly([(8,5),(15,2),(20,6),(17,13),(12,16),(6,12)],p.shadow)
        p.poly([(9,6),(15,4),(17,7),(13,12),(8,11)],p.light)
        p.shaft(15,13,15,1); p.line([(8,14),(6,20),(10,23),(9,28)],p.deep,2)
        p.leaf(8,21,-1); p.leaf(16,13,1)
    elif n==2:
        p.gear(13,11,9,8); p.gem(13,11,3,4); p.shaft(16,18,11,2)
        p.line([(23,5),(25,8),(25,14),(23,17)],p.glow,2)
    elif n==3:
        p.poly([(4,7),(7,3),(24,3),(27,7),(23,12),(9,12)],p.metal)
        p.line([(8,5),(23,5)],p.light); p.box((13,12,18,19),p.shadow,p.dark)
        p.box((7,20,25,23),p.metal,p.dark); p.box((10,24,23,27),p.shadow,p.dark)
        p.gem(16,8,2,3); p.bolt(8,8); p.bolt(23,8)
    elif n==4:
        p.gear(16,16,13,10); p.box((11,11,21,21),p.shadow,p.dark)
        p.circuit(12,12,8,8); p.gem(16,16,2,3)
        p.shaft(16,24,6,1)
    elif n==5:
        p.shaft(16,17,12,1); p.leaf(16,18,-1); p.leaf(16,15,1)
        p.poly([(16,2),(20,7),(26,9),(22,14),(21,19),(16,17),(10,19),(9,13),(5,9),(12,7)],p.metal)
        p.gem(16,11,4,6); p.spark(6,4); p.spark(25,21)
    elif n==6:
        p.box((7,7,24,24),p.dark); p.box((8,8,23,23),p.metal)
        p.ring(16,13,6,2); p.line([(16,13),(19,10)],p.glow,2)
        p.box((4,14,7,20),p.shadow,p.dark); p.box((24,11,28,17),p.shadow,p.dark)
        p.box((11,25,13,29),p.metal,p.dark); p.box((19,25,21,29),p.metal,p.dark)
        p.line([(10,21),(21,21)],p.light); p.spark(7,4)
    elif n==7:
        p.poly([(12,2),(20,2),(23,6),(21,11),(23,17),(20,26),(16,30),(11,25),(9,17),(11,10),(9,6)],p.shadow)
        p.box((12,5,20,10),p.metal); p.box((11,14,21,21),p.metal)
        p.gem(16,17,3,5); p.rune(15,5,7)
        p.line([(8,8),(4,6),(5,3)],p.light); p.line([(23,8),(28,5),(26,2)],p.light)
    elif n==8:
        p.poly([(4,24),(12,9),(9,8),(13,3),(18,2),(17,7),(24,10),(18,12),(25,24)],p.shadow)
        p.box((3,24,28,27),p.metal,p.dark); p.line([(5,25),(26,25)],p.light)
        p.gem(16,19,4,5); p.spark(25,4); p.rune(8,19,8)
    elif n==9:
        p.ring(16,16,11,3,True); p.gem(16,15,4,7)
        p.leaf(9,23,-1); p.leaf(22,10,1); p.line([(4,27),(11,23),(23,8),(28,3)],p.metal,2)
        p.rune(6,11,9); p.spark(26,24)
    elif n==10:
        p.poly([(4,7),(14,5),(16,7),(19,5),(27,7),(27,25),(19,23),(16,25),(13,23),(4,25)],p.metal)
        p.box((6,8,13,21),p.shadow); p.box((19,8,25,21),p.shadow)
        p.line([(16,8),(16,23)],p.light); p.rune(9,11,10); p.rune(22,12,11)
        p.gem(16,15,3,5); p.bolt(5,6); p.bolt(26,24)
    elif n==11:
        p.ring(16,11,8,3); p.shaft(16,18,11,2)
        p.poly([(18,3),(10,13),(16,13),(13,20),(22,9),(16,9)],p.glow)
        p.line([(3,8),(6,10)],p.light); p.line([(27,16),(29,18)],p.light)
    elif n==12:
        p.ring(16,17,11,3,True); p.poly([(16,2),(22,14),(19,20),(13,21),(10,15)],p.deep)
        p.line([(16,6),(13,14),(14,17)],p.glow,2)
        p.poly([(16,11),(19,20),(16,18),(12,24)],p.light)
        p.box((12,28,20,30),p.metal,p.dark); p.bolt(6,17); p.bolt(26,17)
    elif n==13:
        p.box((13,2,19,7),p.metal,p.dark); p.poly([(13,7),(19,7),(19,13),(26,24),(23,28),(9,28),(6,24),(13,13)],p.shadow)
        p.poly([(10,19),(22,19),(24,24),(21,26),(11,26),(8,24)],p.deep)
        p.line([(12,17),(14,13),(14,9)],p.light); p.spark(18,22); p.rune(16,21,13)
        p.box((21,10,27,15),p.metal,p.dark); p.line([(23,11),(25,13),(23,14)],p.glow)
    elif n==14:
        p.box((6,9,24,23),p.shadow,p.dark); p.box((9,6,21,26),p.metal,p.dark)
        p.ring(16,15,6,2); p.gem(16,15,2,4)
        p.box((3,13,7,19),p.metal,p.dark); p.box((25,12,28,21),p.metal,p.dark)
        p.line([(12,5),(12,2),(20,2),(20,5)],p.light,2); p.rune(15,24,14)
    elif n==15:
        p.poly([(7,3),(12,8),(19,8),(25,3),(26,13),(23,18),(20,29),(12,29),(8,18),(5,12)],p.shadow)
        p.poly([(9,10),(14,12),(12,16),(9,15)],p.glow); p.poly([(23,10),(18,12),(20,16),(23,15)],p.glow)
        p.gem(16,21,3,5); p.line([(12,27),(20,27)],p.light)
    elif n==16:
        p.poly([(16,1),(24,8),(24,19),(17,26),(7,20),(7,8)],p.metal)
        p.gem(16,12,5,9); p.box((11,25,21,28),p.shadow,p.dark)
        p.box((9,28,23,30),p.metal,p.dark); p.line([(4,13),(7,13)],p.glow,2)
        p.line([(24,13),(28,13)],p.glow,2)
    elif n==17:
        p.circuit(4,6,23,19); p.box((9,9,23,21),p.metal,p.dark)
        p.box((11,11,21,19),p.shadow,p.dark); p.gem(16,15,3,4)
        for y in (8,13,18,23): p.line([(2,y),(4,y)],p.light); p.line([(27,y),(29,y)],p.light)
        p.box((8,27,24,29),p.metal,p.dark)
    elif n==18:
        p.poly([(13,2),(20,3),(25,9),(23,14),(18,15),(11,19),(9,24),(15,27),(21,25),(23,21),(28,22),(26,28),(21,30),(11,30),(5,25),(6,18),(12,13),(18,11),(19,8),(15,7),(10,10),(6,8),(9,4)],p.metal)
        p.line([(10,7),(15,5),(21,8),(21,11),(10,18),(7,23),(12,28),(21,28),(25,24)],p.glow)
        p.gem(16,18,3,4)
    elif n==19:
        p.poly([(9,3),(22,3),(25,8),(24,16),(21,20),(21,27),(18,30),(13,29),(12,23),(8,20),(6,13)],p.shadow)
        p.box((9,8,23,14),p.metal); p.box((10,9,13,12),p.glow); p.box((19,9,22,12),p.glow)
        p.poly([(16,13),(19,17),(13,17)],p.dark); p.line([(11,23),(20,23)],p.light)
        p.gem(16,25,2,3)
    elif n==20:
        p.box((10,5,22,14),p.metal,p.dark); p.box((8,16,24,25),p.shadow,p.dark)
        p.box((12,8,14,10),p.glow); p.box((18,8,20,10),p.glow)
        p.gem(16,20,3,4); p.line([(16,5),(16,2),(20,2)],p.light)
        p.poly([(7,16),(4,18),(3,25),(6,27),(8,24)],p.metal)
        p.poly([(25,16),(28,18),(29,25),(26,27),(24,24)],p.metal)
        p.box((10,26,13,30),p.metal,p.dark); p.box((19,26,22,30),p.metal,p.dark)
    elif n==21:
        p.poly([(3,12),(8,17),(10,5),(16,12),(22,4),(24,17),(29,10),(26,26),(7,26)],p.metal)
        p.line([(8,23),(24,23)],p.light); p.gem(16,19,4,5)
        p.leaf(9,19,-1); p.leaf(23,19,1); p.spark(16,4)
    elif n==22:
        p.box((9,5,13,27),p.metal,p.dark); p.box((20,5,24,27),p.metal,p.dark)
        for y in range(8,26,4):
            p.box((5,y,16,y+1),p.shadow,p.dark); p.line([(6,y),(15,y)],p.light)
            p.box((17,y+1,28,y+2),p.shadow,p.dark); p.line([(18,y+1),(27,y+1)],p.light)
        p.poly([(17,2),(12,16),(18,14),(15,29),(22,11),(16,13)],p.glow)
    elif n==23:
        p.poly([(16,2),(28,12),(24,26),(8,27),(3,12)],p.shadow)
        p.poly([(16,4),(25,13),(16,17),(6,13)],p.light)
        p.poly([(16,17),(25,13),(22,24),(16,27)],p.deep)
        p.gem(15,15,3,6); p.bolt(7,12); p.bolt(25,12); p.bolt(16,27)
    elif n==24:
        p.circuit(6,6,20,20); p.circuit(10,10,12,12); p.gem(16,16,3,5)
        for x,y in [(3,9),(28,9),(3,22),(28,22)]:p.bolt(x,y)
        p.box((11,2,21,4),p.metal,p.dark); p.box((11,28,21,30),p.metal,p.dark)
    elif n==25:
        p.poly([(8,5),(24,5),(27,13),(23,25),(20,29),(11,29),(7,23),(4,13)],p.metal)
        p.box((8,10,24,17),p.shadow,p.dark); p.gem(16,13,4,5)
        p.line([(9,22),(13,25),(21,25)],p.light)
        p.poly([(3,5),(7,7),(7,18),(3,17)],p.shadow); p.poly([(25,7),(29,4),(29,17),(25,19)],p.shadow)
    elif n==26:
        p.ring(16,17,11,3,True); p.poly([(15,25),(15,13),(9,8),(10,4),(16,8),(22,3),(25,5),(23,11),(18,14),(18,25)],p.deep)
        p.line([(16,24),(16,12),(22,7)],p.glow,2); p.leaf(15,15,-1)
        p.gem(16,23,3,4); p.bolt(7,25); p.bolt(25,25)
    elif n==27:
        p.box((7,3,25,29),p.metal,p.dark); p.box((10,5,22,27),p.shadow,p.dark)
        p.poly([(14,7),(18,7),(21,13),(20,21),(16,25),(12,20),(11,13)],p.deep)
        p.gem(16,15,3,7); p.line([(4,8),(7,8)],p.glow,2); p.line([(25,23),(29,23)],p.glow,2)
        for y in (7,13,20,26):p.bolt(8,y);p.bolt(24,y)
    elif n==28:
        for x,y in [(5,6),(26,6),(5,25),(26,25)]:
            p.line([(x,y),(16,16)],p.metal,3); p.box((x-3,y-3,x+3,y+3),p.dark);p.gem(x,y,2,2)
        p.ring(16,16,7,3,True);p.gem(16,16,3,4)
    elif n==29:
        p.poly([(11,2),(21,2),(28,10),(28,22),(21,30),(11,30),(3,22),(3,10)],p.shadow)
        p.ring(16,16,10,3,True);p.gem(16,16,4,7)
        for x,y in [(7,6),(25,6),(7,26),(25,26)]:p.bolt(x,y)
        p.line([(3,12),(6,12),(6,20),(3,20)],p.glow);p.line([(28,12),(25,12),(25,20),(28,20)],p.glow)
    elif n==30:
        p.poly([(2,15),(8,8),(15,6),(23,8),(30,16),(22,23),(15,25),(8,23)],p.metal)
        p.poly([(5,15),(10,11),(16,9),(22,12),(27,16),(20,21),(13,22),(8,19)],p.deep)
        p.gem(16,16,3,7);p.line([(15,11),(15,18)],p.white)
        p.poly([(5,9),(4,3),(11,8)],p.shadow);p.poly([(24,9),(29,3),(28,13)],p.shadow)
    elif n==31:
        p.ring(16,16,10,3);p.leaf(7,19,-1);p.leaf(24,19,1)
        p.poly([(16,1),(19,7),(25,5),(23,12),(30,16),(24,19),(26,26),(20,25),(16,31),(12,25),(5,27),(7,20),(1,16),(8,12),(6,5),(12,7)],p.deep)
        p.ring(16,16,8,3,True);p.gem(16,16,3,5);p.spark(5,5);p.spark(26,26)
    elif n==32:
        p.poly([(3,7),(8,12),(11,4),(16,10),(22,3),(24,12),(29,6),(27,21),(22,25),(10,25),(5,21)],p.metal)
        p.box((8,23,24,28),p.shadow,p.dark);p.gem(16,18,4,5)
        p.poly([(16,8),(12,17),(17,16),(15,24),(21,13),(16,14)],p.glow)
        p.bolt(8,25);p.bolt(24,25)
    elif n==33:
        p.box((11,2,21,6),p.metal,p.dark);p.poly([(11,6),(21,6),(25,12),(25,24),(20,29),(12,29),(7,24),(7,12)],p.shadow)
        p.box((9,12,23,24),p.metal,p.dark);p.ring(16,18,5,2)
        for a in (0,120,240):
            angle=math.radians(a);p.poly([(16,18),(round(16+6*math.cos(angle-.5)),round(18+6*math.sin(angle-.5))),
                                        (round(16+6*math.cos(angle+.5)),round(18+6*math.sin(angle+.5)))],p.glow)
        p.box((15,17,17,19),p.dark);p.line([(11,8),(21,8)],p.glow)
    elif n==34:
        p.poly([(4,17),(10,8),(20,5),(28,12),(26,24),(16,29),(6,25)],p.shadow)
        p.gem(12,17,5,8);p.gem(23,12,4,8);p.gem(20,24,4,5)
        p.line([(6,26),(12,29),(20,28)],p.light);p.spark(5,4)
    elif n==35:
        for x in (5,15,25):p.box((x-2,5,x+2,27),p.metal,p.dark);p.line([(x-1,7),(x-1,25)],p.light)
        for y in (7,15,24):p.box((3,y-1,29,y+2),p.shadow,p.dark);p.line([(5,y),(27,y)],p.glow)
        p.gem(15,15,4,6);p.box((12,2,18,5),p.metal,p.dark)
    elif n==36:
        p.ring(16,16,13,4,True);p.ring(16,16,7,2)
        p.gem(16,16,3,6)
        for a in range(0,360,60):
            rad=math.radians(a);x=round(16+math.cos(rad)*10);y=round(16+math.sin(rad)*10)
            p.box((x-1,y-1,x+1,y+1),p.glow);p.box((x,y,x,y),p.white)
        p.box((13,28,19,30),p.metal,p.dark)
    elif n==37:
        p.ring(16,16,12,2);p.line([(5,24),(25,5)],p.metal,3)
        p.d.ellipse((9,7,24,22),fill=p.light);p.d.ellipse((15,5,28,19),fill=(0,0,0,0))
        p.gem(15,20,3,5);p.spark(23,8);p.spark(8,5)
        p.box((12,28,20,30),p.metal,p.dark)
    elif n==38:
        p.poly([(4,5),(14,3),(17,5),(21,3),(28,6),(28,27),(20,25),(17,27),(13,25),(4,27)],p.shadow)
        p.ring(12,14,5,2);p.gem(12,14,2,3)
        p.d.ellipse((19,10,25,16),fill=p.glow);p.line([(18,15),(26,10)],p.light)
        p.line([(17,6),(17,25)],p.metal,2);p.rune(9,22,38);p.rune(23,21,39)
        p.spark(25,5)
    elif n==39:
        p.poly([(3,4),(12,9),(16,2),(20,9),(29,4),(24,15),(30,21),(21,22),(16,30),(12,22),(2,25),(7,15)],p.metal)
        p.poly([(16,5),(22,14),(20,23),(16,27),(12,21),(10,14)],p.dark)
        p.line([(17,7),(14,12),(18,16),(14,21),(16,25)],p.glow,2)
        p.spark(7,7);p.spark(26,25)
    elif n==40:
        p.poly([(16,5),(20,10),(24,4),(30,1),(28,12),(24,19),(21,16),(19,27),(13,27),(11,16),(7,20),(3,13),(1,2),(8,5),(12,11)],p.shadow)
        p.line([(3,4),(7,12),(11,14)],p.light);p.line([(28,4),(25,12),(21,14)],p.light)
        p.gem(16,17,4,8);p.box((13,28,19,30),p.metal,p.dark)
    elif n==41:
        p.poly([(9,7),(4,2),(4,12),(9,18),(8,24),(16,30),(24,23),(23,17),(28,11),(28,2),(22,7),(19,5),(16,8),(12,5)],p.metal)
        p.poly([(10,11),(16,14),(22,10),(24,17),(19,24),(16,27),(12,24),(8,17)],p.deep)
        p.gem(16,19,4,7);p.poly([(8,10),(13,11),(12,14)],p.glow);p.poly([(24,10),(19,11),(20,14)],p.glow)
        p.spark(16,3)
    elif n==42:
        p.poly([(16,1),(19,8),(28,3),(23,13),(31,16),(23,20),(28,28),(19,24),(16,31),(12,23),(3,28),(8,19),(1,15),(9,12),(4,3),(13,8)],p.shadow)
        p.poly([(16,4),(18,12),(25,7),(21,15),(27,16),(20,19),(24,25),(17,22),(16,28),(13,20),(6,25),(11,17),(5,15),(12,13),(8,6),(15,11)],p.metal)
        p.gem(16,16,3,6);p.spark(4,16);p.spark(27,15)
    elif n==43:
        p.gear(13,17,12,9);p.gear(24,8,6,6)
        p.circuit(6,12,13,11);p.gem(13,17,3,5)
        p.poly([(24,18),(29,22),(28,28),(21,29),(19,25)],p.shadow);p.rune(24,23,43)
    elif n==44:
        p.ring(16,14,11,3);p.d.ellipse((10,8,22,20),fill=p.deep)
        p.line([(11,14),(21,14)],p.glow);p.line([(16,9),(13,13),(16,19)],p.glow)
        p.box((10,24,22,29),p.metal,p.dark);p.box((13,21,19,25),p.shadow,p.dark)
        p.poly([(2,21),(8,15),(8,25),(5,27)],p.metal);p.poly([(30,21),(24,15),(24,25),(27,27)],p.metal)
    elif n==45:
        p.box((14,5,18,27),p.metal,p.dark);p.gem(16,6,3,4)
        p.line([(4,11),(28,11)],p.metal,3);p.line([(4,12),(1,21),(8,21),(4,12)],p.light)
        p.line([(27,12),(23,21),(30,21),(27,12)],p.light)
        p.poly([(1,21),(9,21),(7,25),(3,25)],p.deep);p.poly([(22,21),(31,21),(28,25),(25,25)],p.deep)
        p.box((9,28,23,30),p.metal,p.dark);p.spark(16,17)
    elif n==46:
        p.ring(16,16,12,2,True);p.ring(16,16,8,2)
        p.d.ellipse((12,12,20,20),fill=p.dark);p.d.arc((8,5,24,27),55,250,fill=p.glow,width=2)
        p.line([(2,10),(10,11)],p.metal,2);p.line([(21,22),(29,27)],p.metal,2)
        p.gem(16,16,2,3);p.spark(6,24);p.spark(25,7)
    elif n==47:
        for x,y in [(16,3),(28,12),(24,27),(8,27),(3,12)]:
            p.line([(x,y),(16,16)],p.metal,3);p.gem(x,y,2,3)
        p.ring(16,16,9,2,True);p.ring(16,16,5,2);p.gem(16,16,2,4)
        p.spark(5,3);p.spark(29,27)
    elif n==48:
        p.poly([(2,8),(7,12),(9,3),(14,9),(16,1),(19,9),(24,3),(25,12),(30,7),(27,22),(23,27),(9,27),(4,22)],p.metal)
        p.line([(8,24),(24,24)],p.light);p.ring(11,17,5,2);p.ring(22,17,5,2)
        p.line([(8,14),(24,20)],p.glow,2);p.line([(8,20),(24,14)],p.glow,2)
        p.gem(16,8,2,4);p.box((10,28,22,30),p.shadow,p.dark)
        p.spark(2,2);p.spark(29,29)
    return p.finish()


def component_art(kind,n):
    p=Pixel(n)
    tier=(n-1)//12
    if kind=='tech_matrix':
        off=(n-1)%3
        p.poly([(5,5+off),(24,3+off),(28,24-off),(8,28-off)],p.metal)
        p.circuit(9,8,14,14)
        p.box((12,11,20,19),p.shadow,p.dark)
        p.gem(16,15,2,3)
        for i in range(tier+1):p.line([(5+i*3,25),(7+i*3,25)],p.glow)
        p.bolt(6,7+off);p.bolt(25,23-off)
    elif kind=='arcane_catalyst':
        points=4+(n%5)
        for i in range(points):
            a=math.tau*i/points
            x=round(16+math.cos(a)*10);y=round(16+math.sin(a)*10)
            p.line([(16,16),(x,y)],p.metal,2);p.spark(x,y)
        p.ring(16,16,8,2,True);p.gem(16,15,4+tier%2,7)
        p.rune(6,23,n);p.rune(25,5,n+1)
    elif kind=='convergence_core':
        p.gear(16,16,12,6+(n%4));p.ring(16,16,7,2,True)
        p.gem(16,16,3,5)
        for j in range(tier+1):
            a=j*math.tau/(tier+1)+n%3*.3
            p.spark(round(16+9*math.cos(a)),round(16+9*math.sin(a)))
    else:
        side=6+n%3
        pts=[(round(16+13*math.cos(i*math.tau/side-math.pi/2)),
              round(16+13*math.sin(i*math.tau/side-math.pi/2))) for i in range(side)]
        p.poly(pts,p.shadow);p.ring(16,16,9,3,True)
        p.gem(16,15,3,5);p.rune(7,13,n);p.rune(25,13,n+2)
        for j in range(tier+1):p.box((12+j*2,26,12+j*2,27),p.glow)
    # Distinct engraved, native-pixel binary maker marks (not the key silhouette).
    for i in range(6):
        if n & (1<<i):p.box((10+i*2,29,10+i*2,29),p.light)
    return p.finish()


def chapter_art(n):
    p=Pixel(n)
    p.poly([(4,2),(27,2),(30,7),(28,24),(16,31),(3,25),(1,7)],p.shadow)
    p.line([(5,3),(26,3),(28,7),(26,23),(16,29)],p.light)
    # A chapter badge embeds a legible miniature of its own unique artifact.
    art=key_art(n).resize((24,24),Image.Resampling.NEAREST)
    p.im.alpha_composite(art,(4,3))
    p.box((10,25,22,30),p.dark)
    tiny_number(p, n, 12,26)
    return p.finish()


DIGITS = {'0':['111','101','101','101','111'],'1':['010','110','010','010','111'],
          '2':['111','001','111','100','111'],'3':['111','001','111','001','111'],
          '4':['101','101','111','001','001'],'5':['111','100','111','001','111'],
          '6':['111','100','111','101','111'],'7':['111','001','010','010','010'],
          '8':['111','101','111','101','111'],'9':['111','101','111','001','111']}


def tiny_number(p,n,x,y):
    for offset,char in enumerate(f'{n:02d}'):
        for yy,row in enumerate(DIGITS[char]):
            for xx,bit in enumerate(row):
                if bit=='1':p.box((x+offset*4+xx,y+yy,x+offset*4+xx,y+yy),p.light)


def section_art(section):
    p=Pixel(45)
    if section=='epochs':
        p.ring(16,16,13,3,True);p.shaft(16,17,12,2);p.gem(16,11,5,7)
    elif section=='technology':
        p.gear(13,18,12,9);p.circuit(15,3,12,11);p.gem(13,18,3,5)
    elif section=='magic':
        p.poly([(3,25),(12,10),(10,4),(17,1),(21,7),(18,12),(29,25)],p.deep)
        p.box((2,26,30,29),p.metal,p.dark);p.gem(16,19,4,6);p.spark(27,6)
    elif section=='adventure':
        p.poly([(23,2),(29,5),(14,23),(8,18)],p.metal);p.line([(24,5),(11,21)],p.light)
        p.poly([(6,17),(16,25),(13,28),(3,20)],p.shadow)
        p.line([(5,29),(10,23)],p.metal,3);p.gem(24,6,2,3)
        p.ring(9,9,6,2);p.line([(9,4),(9,12)],p.glow)
    else:
        p.poly([(5,9),(26,9),(29,14),(27,28),(4,28),(2,14)],p.shadow)
        p.box((4,17,27,20),p.metal,p.dark);p.box((13,17,18,24),p.metal,p.dark)
        p.gem(12,10,4,7);p.gem(22,8,3,6);p.spark(5,4)
    return p.finish()


def save_asset(item,texture,im,label,entries,lore=None):
    assert im.mode=='RGBA' and im.size==(32,32)
    relative=texture.split(':',1)[1]
    target=ASSETS/'textures'/f'{relative}.png'
    target.parent.mkdir(parents=True,exist_ok=True)
    im.save(target,optimize=False,compress_level=9)
    itempath=item.split(':',1)[1]
    model=ASSETS/'models/item'/f'{itempath}.json'
    model.parent.mkdir(parents=True,exist_ok=True)
    model.write_text(json.dumps({'parent':'minecraft:item/generated','textures':{'layer0':texture}},indent=2)+'\n')
    entry={'id':item,'name_uk':label,'texture':texture,'model':f'kubejs:item/{itempath}',
           'png':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest()}
    if lore:entry['lore_uk']=lore
    entries.append(entry)


def main():
    epochs=json.loads((ROOT/'design/progression.json').read_text())['epochs']
    entries=[]; keys=[]
    for e in epochs:
        n=e['number']; item=f'kubejs:aia2_epoch_key_{n:02d}'
        role=(f'Артефакт завершення епохи {n}. Відкриває наступний етап лише після законного виготовлення.'
              if n<48 else 'Фінальний артефакт. Законне виготовлення завершує ланцюг усіх 48 епох.')
        heritage=('Починає ланцюг артефактів. Використовується лише у прогресії ключів.' if n==1
                  else 'Зберігає спадок попереднього ключа. Використовується лише у прогресії ключів.')
        lore=[e['theme'],role,heritage]
        save_asset(item,f'kubejs:item/aia2/keys/epoch_key_{n:02d}',key_art(n),NAMES[n-1],entries,lore)
        keys.append(entries[-1])
        save_asset(f'kubejs:aia2_epoch_icon_{n:02d}',f'kubejs:item/aia2/chapters/epoch_{n:02d}',chapter_art(n),
                   f'Епоха {n}: '+e['title'],entries)
        for kind in KINDS:
            save_asset(f'kubejs:aia2_{kind}_{n:02d}',f'kubejs:item/aia2/components/{kind}_{n:02d}',component_art(kind,n),
                       KIND_UK[kind]+': '+e['title'],entries)
    for section,label in SECTIONS.items():
        save_asset('kubejs:aia2_section_'+section,'kubejs:item/aia2/sections/'+section,section_art(section),label,entries)
    lang={f'item.kubejs.{x["id"].split(":",1)[1]}':x['name_uk'] for x in entries}
    for name in ('uk_ua','en_us'):
        target=ASSETS/'lang'/f'{name}.json';target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(lang,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    manifest={'schema':1,'style':'32px native RGBA pixel art; individually composed key silhouettes',
              'generator':'tools/generate_resources.py','keys':keys,'assets':entries}
    dest=ROOT/'content/resources/manifest.json';dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    # QA reads back the saved assets and checks actual pixel content/model references.
    alphas=[];silhouettes=[]
    for e in entries:
        with Image.open(ROOT/e['png']) as im:
            assert im.mode=='RGBA' and im.size==(32,32),e['png']
            a=im.getchannel('A'); assert a.getextrema()==(0,255),e['png']
            opaque=sum(1 for x in a.tobytes() if x)
            assert 45<opaque<1000,(e['png'],opaque)
            alphas.append(opaque)
            if e in keys:silhouettes.append(hashlib.sha256(a.tobytes()).hexdigest())
        model=json.loads((ASSETS/'models/item'/f'{e["id"].split(":",1)[1]}.json').read_text())
        assert model['textures']['layer0']==e['texture']
    assert len(set(e['sha256'] for e in entries))==len(entries),'Identical texture bytes'
    assert len(set(silhouettes))==48,'Key silhouettes must all be different'
    report={'status':'passed_pixel_and_model_checks','png_textures':len(entries),'item_models':len(entries),
            'unique_keys':48,'unique_key_silhouettes':len(set(silhouettes)), 'chapter_icons':48,'section_icons':5,
            'component_textures':192,'dimensions':[32,32],'mode':'RGBA','transparent_pngs':len(entries),
            'opaque_pixel_range':[min(alphas),max(alphas)],'unique_png_hashes':len(set(e['sha256'] for e in entries)),
            'generator':'python3 tools/generate_resources.py','minecraft_resource_reload':'not_run'}
    (ROOT/'implementation/resource-report.json').write_text(json.dumps(report,indent=2)+'\n')
    contact_sheet(epochs)
    print(json.dumps(report,indent=2))


def contact_sheet(epochs):
    scale=4;cellw=180;cellh=170
    sheet=Image.new('RGB',(cellw*8,cellh*6),(20,24,34));draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',11)
    except OSError:font=ImageFont.load_default()
    for e in epochs:
        n=e['number'];x=(n-1)%8*cellw;y=(n-1)//8*cellh
        for yy in range(0,128,16):
            for xx in range(0,128,16):
                c=(34,40,51) if (xx//16+yy//16)%2 else (28,33,44)
                draw.rectangle((x+26+xx,y+4+yy,x+41+xx,y+19+yy),fill=c)
        sheet.paste(key_art(n).resize((128,128),Image.Resampling.NEAREST),(x+26,y+4),
                    key_art(n).resize((128,128),Image.Resampling.NEAREST))
        label=f'{n:02d}. {NAMES[n-1]}'
        words=label.split();lines=['']
        for word in words:
            if draw.textlength(lines[-1]+' '+word,font=font)>170:lines.append(word)
            else:lines[-1]=(lines[-1]+' '+word).strip()
        for j,line in enumerate(lines[:2]):draw.text((x+5,y+137+j*14),line,font=font,fill=(221,229,239))
    sheet.save(ROOT/'implementation/assets-preview.png')


if __name__=='__main__':main()
