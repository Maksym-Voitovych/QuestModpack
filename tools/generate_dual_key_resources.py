#!/usr/bin/env python3
"""Reproduce AIA2's two-key 32px pixel-art set without touching legacy resources.

Each epoch has separately composed engineering and arcane/research artifacts.
All geometry is drawn at native resolution; no smoothing, source images or
palette-swapping of an existing key are used. Requires Pillow.
"""
from pathlib import Path
import hashlib
import json
import math
from PIL import Image, ImageDraw, ImageFont
from generate_resources import Pixel, color

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'kubejs/assets/kubejs'
TECH_NAMES = [
 'Кремінний різець табору','Водяний шпиндель','Ковальський бойок','Штамп андезитової лінії',
 'Маносталевий привід','Бронзовий парорегулятор','Резонатор тесляра','Сталева заслінка',
 'Різець живих рун','Латунний маніпулятор','Якір першого динамо','Дизельний колінвал',
 'Алхімічний випрямляч','Пневматичний клапан','Базальтовий охолоджувач','Осмієва інфузійна касета',
 'Кремнієвий індексатор','Полімерний екструдер','Душопривід сплавів','Механізм чарівного збирача',
 'Ельфійський сплавовузол','Індукційний трансформатор','Лінза збагачувальної лінії','Нейронна друкована плата',
 'Захват роботизованої кузні','Контролер тепличного циклу','Біореакторна касета','Маршрутизатор світових ліній',
 'Турбіна реакторного контуру','Просторовий якір Енду','Гіроскоп Ґаї','Шина високої напруги',
 'Радіохімічний стрижень','Рідкіснометалевий бур','Надпровідна петля','Фокусатор термоядерного кільця',
 'Місячний рушій','Планетарний ровер','Антиматеріальний затвор','Синтезатор виверни',
 'Пробуджений драконовий тигель','Поляризатор Хаосу','Еволюційний ротор','Орбітальна ливарня',
 'Трансмутаційний стабілізатор','Нейтронний колектор','Матриця космічного складання','Процесор нескінченності',
]
ARCANE_NAMES = [
 'Жолудь першого вогнища','Сльоза водяних коренів','Камінь ковальської обітниці','Спіраль природного порядку',
 'Пелюсткова зірка мани','Паровий дух бурштину','Рогатий оберіг сутінків','Відьомський місячний казан',
 'Чотирилистий знак рун','Гримуар латунної печаті','Громовий німб','Алхімічний серп нафти',
 'Кривава астролябія','Клітка викликаного духа','Вогонь забороненого знання','Трикристальна обітниця',
 'Астральний архіварій','Паросток полімерного саду','Маска душевного сплаву','Крила арканного слуги',
 'Вінець ельфійського договору','Призма грозової аури','Секстант живого збагачення','Лінза рунного провидця',
 'Ефірна долоня коваля','Плід упокореної есенції','Печатка життєвої крові','Путівна зоря вимірів',
 'Сонячний релікварій реактора','Неспляче око Енду','Квітучий клинок Ґаї','Щит високих небес',
 'Нічна радіохімічна амфора','Ланцюг міжсвітових уламків','Левітуюча грань духа','Подвійний оберт гармонії',
 'Селеновий знак мандрівника','Атлас чотирьох планет','Сльоза просторової ентропії','Крилата руна виверни',
 'Драконяче око пробудження','Нестала зірка Хаосу','Вінець плину еволюції','Планетарна мандала',
 'Терези смарагдового закону','Реліквія нейтронного провалля','Посох космічних сузір’їв','Арканний вінець безмежжя',
]


class DualPixel(Pixel):
    def ring(self,x,y,radius,width=3,octagonal=False):
        # Miniature hardware uses rings smaller than the legacy helper's
        # default bore; keep the cutout valid without changing any old art.
        return super().ring(x,y,radius,min(width,radius),octagonal)


def canvas(n, arcane=False):
    p=DualPixel(n)
    # Metals evolve by epoch; role-specific luminous material is independent.
    tech=[('366b69','8ff9d8'),('2b658b','9ee8ff'),('634c9a','ceb4ff'),('a74c29','ffce79')]
    magic=[('427d39','c7ed88'),('6943a0','dfacff'),('9b356d','ffa8db'),('3f8197','c5fff0')]
    deep,glow=(magic if arcane else tech)[min((n-1)//12,3)]
    p.deep=color(deep);p.glow=color(glow)
    return p


def panel(p, x, y, w, h):
    p.box((x,y,x+w,y+h),p.dark)
    p.box((x+1,y+1,x+w-1,y+h-1),p.metal)
    p.box((x+3,y+3,x+w-3,y+h-3),p.shadow)
    p.line([(x+2,y+2),(x+w-2,y+2)],p.light)


def pipe(p, points, width=4):
    p.line(points,p.dark,width+2);p.line(points,p.shadow,width)
    p.line([(x-1,y-1) for x,y in points],p.metal,max(width-2,1))


def diamond(p,x,y,r=9):
    p.poly([(x,y-r),(x+r,y),(x,y+r),(x-r,y)],p.metal)
    p.poly([(x,y-r+3),(x+r-3,y),(x,y+r-3),(x-r+3,y)],p.deep)


def halo(p,x,y,r=11,phase=0):
    p.ring(x,y,r,2,True)
    for k in range(4):
        a=phase+k*math.pi/2
        xx=round(x+math.cos(a)*(r+2));yy=round(y+math.sin(a)*(r+2))
        p.spark(xx,yy)


def vessel(p,x,y,w=12,h=16):
    p.poly([(x+3,y),(x+w-3,y),(x+w-3,y+4),(x+w,y+h-3),
            (x+w-3,y+h),(x+3,y+h),(x,y+h-3),(x+3,y+4)],p.metal)
    p.poly([(x+4,y+5),(x+w-4,y+5),(x+w-2,y+h-4),(x+2,y+h-4)],p.deep)
    p.line([(x+4,y+6),(x+3,y+h-5)],p.glow)
    p.box((x+2,y-2,x+w-2,y+1),p.shadow,p.dark)


def book(p,x,y,w=20,h=20):
    p.poly([(x,y+1),(x+w//2-2,y),(x+w//2,y+2),(x+w//2+2,y),
            (x+w,y+1),(x+w,y+h),(x+w//2+2,y+h-1),
            (x+w//2,y+h+1),(x+w//2-2,y+h-1),(x,y+h)],p.metal)
    p.box((x+2,y+3,x+w//2-3,y+h-3),p.shadow)
    p.box((x+w//2+3,y+3,x+w-2,y+h-3),p.deep)
    p.line([(x+w//2,y+3),(x+w//2,y+h-2)],p.light)


def tech_art(n):
    p=canvas(n)
    if n==1:
        p.poly([(7,3),(14,2),(19,7),(15,13),(9,16),(5,11)],p.shadow)
        p.poly([(9,4),(14,4),(16,7),(11,12),(7,10)],p.light)
        p.poly([(13,13),(16,14),(24,26),(22,29),(19,28),(11,17)],p.metal)
        p.line([(14,17),(20,26)],p.shadow,2);p.bolt(15,17)
    elif n==2:
        p.gear(11,11,9,7);p.gem(11,11,2,3)
        pipe(p,[(17,14),(22,19),(22,28)],3);p.box((22,24,28,27),p.metal,p.dark)
        p.line([(3,22),(7,22),(10,19)],p.glow,2)
    elif n==3:
        p.poly([(4,5),(20,3),(24,7),(22,12),(8,14),(3,11)],p.metal)
        p.box((11,12,16,26),p.shadow,p.dark);p.line([(12,14),(12,25)],p.light)
        p.box((7,26,21,29),p.metal,p.dark);p.bolt(7,8);p.gem(17,8,2,3)
    elif n==4:
        panel(p,4,3,22,7);pipe(p,[(7,10),(7,25)],3);pipe(p,[(23,10),(23,25)],3)
        p.box((13,10,18,18),p.shadow,p.dark);p.box((9,18,22,21),p.metal,p.dark)
        p.gear(16,24,5,6);p.gem(16,24,1,2)
    elif n==5:
        p.gear(12,16,10,8);p.box((19,10,25,24),p.metal,p.dark)
        p.gem(12,15,4,6);pipe(p,[(25,14),(29,14),(29,8)],2)
        p.poly([(20,25),(24,25),(26,29),(18,29)],p.shadow);p.rune(22,15,5)
    elif n==6:
        vessel(p,7,7,17,19);p.ring(15,15,5,2)
        p.line([(15,15),(18,12)],p.glow);pipe(p,[(10,7),(10,3),(5,3)],2)
        p.box((21,9,27,12),p.shadow,p.dark);p.gear(25,25,5,6)
    elif n==7:
        p.poly([(7,5),(15,2),(24,5),(24,14),(20,17),(20,25),(11,29),(7,24)],p.shadow)
        p.box((8,7,22,12),p.metal,p.dark);p.box((10,16,21,21),p.deep,p.dark)
        p.ring(16,19,4,1);p.line([(12,25),(18,23)],p.light);p.bolt(12,8);p.bolt(20,8)
    elif n==8:
        panel(p,4,10,22,15);p.box((7,5,12,10),p.shadow,p.dark)
        p.box((18,3,24,10),p.metal,p.dark)
        for y in [14,18,22]:p.line([(8,y),(21,y)],p.dark,2)
        p.gear(26,18,4,6);p.gem(20,7,2,3)
    elif n==9:
        diamond(p,14,15,11);p.rune(14,11,9);p.rune(8,16,8)
        pipe(p,[(21,21),(26,26)],2);p.poly([(26,24),(29,27),(27,30),(24,27)],p.light)
        p.bolt(14,6);p.bolt(5,15)
    elif n==10:
        p.gear(8,8,6,7);pipe(p,[(11,10),(18,14),(17,22)],3)
        p.poly([(15,20),(22,20),(25,24),(22,29),(19,27),(21,24),(15,24)],p.metal)
        p.box((3,21,12,28),p.shadow,p.dark);p.line([(5,23),(10,23)],p.glow);p.gem(8,8,2,3)
    elif n==11:
        p.poly([(7,6),(23,6),(27,12),(27,21),(22,26),(7,26),(3,20),(3,12)],p.shadow)
        for x in range(8,23,3):p.line([(x,8),(x,24)],p.metal,2)
        p.ring(16,16,6,2);p.gem(16,16,2,4);p.box((12,2,20,5),p.metal,p.dark)
    elif n==12:
        p.gear(9,23,6,7);pipe(p,[(12,21),(20,13),(20,5)],4)
        panel(p,14,3,13,7);p.box((17,12,23,18),p.shadow,p.dark)
        p.line([(17,16),(23,16)],p.light);p.bolt(9,23);p.box((3,10,8,16),p.deep,p.dark)
    elif n==13:
        panel(p,4,5,14,17);p.circuit(6,8,10,10)
        vessel(p,17,10,10,17);pipe(p,[(12,5),(12,2),(24,2),(24,7)],2)
        p.gem(22,21,2,4)
    elif n==14:
        pipe(p,[(4,17),(26,17)],5);p.ring(15,11,7,2)
        p.line([(15,11),(19,8)],p.glow,2);p.box((12,20,19,25),p.shadow,p.dark)
        p.gear(15,26,4,6);p.box((2,13,6,21),p.metal,p.dark);p.box((25,13,29,21),p.metal,p.dark)
    elif n==15:
        p.poly([(6,4),(24,4),(27,9),(27,24),(22,29),(7,27),(3,21),(3,10)],p.shadow)
        for y in [8,12,16,20,24]:p.line([(7,y),(23,y)],p.metal)
        p.poly([(15,6),(20,14),(18,22),(13,25),(10,18)],p.deep);p.gem(15,17,2,5)
        p.bolt(6,5);p.bolt(25,24)
    elif n==16:
        panel(p,8,2,16,25);p.circuit(10,5,12,8);p.gem(16,20,3,5)
        p.box((3,10,7,20),p.shadow,p.dark);p.box((25,8,29,17),p.shadow,p.dark)
        p.line([(12,28),(12,30)],p.light);p.line([(21,28),(21,30)],p.light)
    elif n==17:
        p.circuit(5,5,21,21);p.box((10,10,21,21),p.metal,p.dark)
        p.circuit(12,12,7,7);p.poly([(7,27),(12,27),(12,30),(7,30)],p.metal)
        p.box((22,2,27,5),p.light,p.dark);p.gem(16,16,2,3)
    elif n==18:
        panel(p,3,8,18,14);p.poly([(21,10),(27,14),(29,15),(27,18),(21,20)],p.metal)
        p.line([(5,12),(18,12)],p.glow);p.line([(5,17),(18,17)],p.light)
        pipe(p,[(8,8),(8,3),(16,3),(16,8)],2);p.gear(9,25,5,6);p.box((21,23,27,28),p.deep,p.dark)
    elif n==19:
        p.gear(14,17,12,9);p.poly([(7,9),(14,5),(21,9),(21,21),(14,25),(7,21)],p.shadow)
        p.gem(14,15,4,6);p.poly([(11,19),(17,19),(16,23),(12,23)],p.deep)
        p.box((23,7,28,13),p.metal,p.dark);p.box((24,20,29,25),p.metal,p.dark)
    elif n==20:
        panel(p,9,9,14,16);p.ring(16,7,5,2);p.gem(16,17,3,4)
        pipe(p,[(8,13),(4,13),(4,21)],2);pipe(p,[(24,13),(28,13),(28,21)],2)
        p.box((9,26,13,29),p.metal,p.dark);p.box((19,26,23,29),p.metal,p.dark);p.rune(16,4,20)
    elif n==21:
        p.poly([(4,10),(12,4),(19,4),(27,10),(24,22),(16,29),(7,22)],p.metal)
        p.poly([(8,11),(14,8),(20,8),(23,12),(20,20),(15,24),(11,19)],p.deep)
        p.line([(9,10),(20,21)],p.light,2);p.line([(20,9),(10,21)],p.metal,2)
        p.gem(16,15,2,5);p.bolt(16,5)
    elif n==22:
        pipe(p,[(5,8),(5,25),(12,25)],3);pipe(p,[(26,8),(26,25),(20,25)],3)
        for x in [11,20]:
            p.box((x-3,7,x+3,22),p.shadow,p.dark)
            for y in range(9,22,3):p.line([(x-2,y),(x+2,y)],p.metal,2)
        p.box((11,3,20,7),p.metal,p.dark);p.gem(16,15,2,4)
    elif n==23:
        p.poly([(6,4),(22,4),(28,15),(22,26),(7,26),(2,15)],p.metal)
        p.ring(15,15,8,3);p.gem(15,15,3,6)
        p.line([(24,14),(30,14)],p.glow,2);p.line([(10,27),(8,30)],p.shadow,2)
        p.bolt(7,6);p.bolt(22,24)
    elif n==24:
        p.poly([(5,3),(25,3),(28,7),(28,23),(23,28),(5,28),(2,23),(2,7)],p.metal)
        p.circuit(6,7,17,17);p.box((12,11,20,19),p.shadow,p.dark)
        p.gem(16,15,2,3);p.line([(26,10),(30,10)],p.light);p.line([(26,18),(30,18)],p.light)
    elif n==25:
        p.gear(16,11,8,8);p.gem(16,11,2,4)
        pipe(p,[(10,17),(7,23),(12,28)],3);pipe(p,[(22,17),(25,23),(20,28)],3)
        p.box((4,8,8,13),p.shadow,p.dark);p.box((24,8,28,13),p.shadow,p.dark)
        p.rune(16,3,25)
    elif n==26:
        p.poly([(7,6),(16,2),(25,6),(28,19),(24,27),(8,27),(4,19)],p.metal)
        p.poly([(9,8),(16,5),(22,8),(24,19),(21,23),(10,23),(8,19)],p.deep)
        p.line([(16,22),(16,12)],p.glow,2);p.leaf(16,17,-1);p.leaf(16,13,1)
        p.box((11,27,21,30),p.shadow,p.dark);p.bolt(7,20);p.bolt(25,20)
    elif n==27:
        panel(p,8,3,16,25);p.box((11,7,21,22),p.deep,p.dark)
        for y in [10,15,20]:
            p.line([(12,y),(20,y+2)],p.glow);p.line([(12,y+2),(20,y)],p.metal)
        pipe(p,[(8,9),(3,9),(3,20),(8,20)],2);p.gem(26,17,2,4)
    elif n==28:
        diamond(p,16,16,9);p.circuit(11,11,10,10)
        for xx,yy in [(4,4),(26,4),(4,26),(26,26)]:
            pipe(p,[(xx,yy),(16,16)],2);p.box((xx-2,yy-2,xx+2,yy+2),p.metal,p.dark)
        p.gem(16,16,2,3)
    elif n==29:
        p.ring(16,16,12,4,True)
        for k in range(6):
            a=k*math.pi/3;p.poly([(16,16),(round(16+9*math.cos(a)),round(16+9*math.sin(a))),
                                  (round(16+6*math.cos(a+.6)),round(16+6*math.sin(a+.6)))],p.metal)
        p.gem(16,16,2,4);p.box((12,1,20,4),p.shadow,p.dark)
    elif n==30:
        p.poly([(5,4),(11,4),(11,9),(21,9),(21,4),(27,4),(27,26),(21,26),(21,21),(11,21),(11,26),(5,26)],p.shadow)
        p.ring(16,15,7,2,True);p.gem(16,15,3,5)
        p.line([(7,6),(7,24)],p.light);p.line([(25,6),(25,24)],p.light);p.box((12,27,20,30),p.metal,p.dark)
    elif n==31:
        p.ring(16,16,10,2)
        p.poly([(6,5),(15,11),(26,5),(21,16),(26,27),(16,22),(5,27),(10,16)],p.metal)
        p.ring(16,16,5,2);p.gem(16,16,2,4);p.bolt(4,16);p.bolt(28,16)
    elif n==32:
        for x in [7,15,23]:
            p.box((x-2,4,x+2,27),p.dark);p.box((x-1,5,x+1,26),p.metal)
            for y in [7,13,19,25]:p.line([(x-3,y),(x+3,y)],p.light)
        p.box((3,13,27,18),p.shadow,p.dark);p.gem(16,15,3,5)
    elif n==33:
        vessel(p,9,5,13,24);p.box((12,10,19,22),p.deep,p.dark)
        for a in [0,2*math.pi/3,4*math.pi/3]:
            p.poly([(16,16),(round(16+5*math.cos(a)),round(16+5*math.sin(a))),
                            (round(16+5*math.cos(a+.8)),round(16+5*math.sin(a+.8)))],p.glow)
        p.box((5,10,8,23),p.shadow,p.dark);p.box((23,10,26,23),p.shadow,p.dark)
    elif n==34:
        p.poly([(3,8),(9,3),(21,3),(28,10),(24,13),(18,8),(12,8),(7,12)],p.metal)
        pipe(p,[(16,8),(10,27)],3);p.gem(16,7,3,4)
        p.poly([(21,18),(27,15),(30,20),(26,27),(20,25)],p.shadow);p.gem(25,22,2,4)
    elif n==35:
        pipe(p,[(5,7),(22,7),(25,11),(25,23),(7,23),(5,19),(5,7)],4)
        p.line([(8,9),(20,9),(23,12),(23,20)],p.glow,2)
        p.circuit(10,13,10,6);p.gem(16,16,2,3);p.box((9,25,12,29),p.metal,p.dark)
    elif n==36:
        p.ring(16,16,11,4);p.ring(16,16,6,1)
        for a in range(0,360,45):
            t=math.radians(a);x=round(16+12*math.cos(t));y=round(16+12*math.sin(t));p.box((x-1,y-2,x+1,y+2),p.light,p.dark)
        p.gem(16,16,2,5);p.box((2,13,5,19),p.shadow,p.dark);p.box((27,13,30,19),p.shadow,p.dark)
    elif n==37:
        p.poly([(16,2),(21,8),(22,20),(26,26),(21,25),(20,29),(12,29),(11,25),(6,26),(10,20),(11,8)],p.metal)
        p.gem(16,12,3,5);p.box((12,22,20,26),p.shadow,p.dark)
        p.line([(14,28),(14,31)],p.glow);p.line([(18,28),(18,30)],p.glow)
    elif n==38:
        panel(p,10,10,12,11);p.gem(16,15,2,3)
        for x in [2,23]:
            p.circuit(x,6,7,12);p.box((x,21,x+6,26),p.shadow,p.dark)
            for y in [22,24]:p.line([(x+1,y),(x+5,y)],p.light)
        p.box((13,4,19,9),p.shadow,p.dark);p.box((13,23,19,29),p.metal,p.dark)
    elif n==39:
        p.poly([(4,8),(10,2),(22,2),(28,8),(28,24),(22,30),(10,30),(4,24)],p.shadow)
        p.ring(16,16,10,3,True);p.ring(16,16,5,1)
        p.poly([(16,6),(19,13),(17,16),(19,23),(13,18),(15,15),(12,10)],p.glow)
        for x,y in [(5,9),(26,9),(5,23),(26,23)]:p.bolt(x,y)
    elif n==40:
        p.poly([(3,5),(10,8),(16,4),(22,8),(29,5),(25,17),(21,19),(21,25),(16,29),(11,25),(11,19),(7,17)],p.metal)
        p.poly([(10,11),(16,8),(22,11),(20,21),(16,25),(12,21)],p.shadow)
        p.gem(16,17,3,6);p.box((4,23,8,27),p.deep,p.dark);p.box((24,23,28,27),p.deep,p.dark)
    elif n==41:
        p.poly([(7,4),(12,7),(16,2),(20,7),(25,4),(26,18),(22,27),(10,27),(6,18)],p.shadow)
        p.poly([(8,12),(12,8),(16,11),(20,8),(24,12),(20,19),(12,19)],p.metal)
        p.gem(16,18,4,8);p.box((9,28,23,30),p.metal,p.dark)
        p.line([(4,7),(3,15),(5,21)],p.glow);p.line([(28,7),(29,15),(27,21)],p.glow)
    elif n==42:
        p.gear(16,16,10,11)
        for a in [0,.9,2.1,3.0,4.2,5.3]:
            x=round(16+14*math.cos(a));y=round(16+14*math.sin(a));p.line([(16,16),(x,y)],p.shadow,2)
            p.poly([(x,y),(x-1,y+3),(x+2,y+1)],p.light)
        p.ring(16,16,5,2,True);p.gem(16,16,2,5)
    elif n==43:
        p.poly([(4,5),(13,7),(16,2),(19,7),(28,5),(25,13),(29,16),(25,20),(26,28),(18,25),(16,30),(13,25),(5,28),(7,20),(2,16),(7,12)],p.shadow)
        p.gear(16,16,10,9);p.circuit(11,12,10,8);p.gem(16,16,2,3)
    elif n==44:
        p.ring(16,15,13,1,True)
        p.poly([(7,3),(24,3),(27,8),(25,13),(27,23),(22,28),(9,28),(5,23),(7,13),(4,8)],p.metal)
        p.box((10,8,22,22),p.shadow,p.dark);p.gem(16,15,4,6)
        p.box((11,29,21,31),p.deep,p.dark)
    elif n==45:
        p.ring(16,16,12,1)
        p.gear(16,16,8,8);p.gem(16,16,2,4)
        p.line([(5,5),(27,27)],p.metal,3);p.line([(5,27),(27,5)],p.metal,3)
        for x,y in [(5,5),(27,27),(5,27),(27,5)]:p.box((x-2,y-2,x+2,y+2),p.shadow,p.dark);p.bolt(x,y)
    elif n==46:
        p.poly([(10,3),(22,3),(27,12),(25,25),(19,29),(12,29),(6,24),(4,12)],p.shadow)
        p.ring(16,15,8,3,True);p.gem(16,15,3,6)
        for x in [9,23]:p.box((x-1,7,x+1,24),p.metal,p.dark)
        p.box((12,1,20,4),p.light,p.dark);p.box((11,28,21,30),p.deep,p.dark)
    elif n==47:
        p.circuit(9,9,14,14)
        for x,y in [(4,4),(16,2),(28,4),(29,17),(25,28),(8,29),(2,17)]:
            p.line([(16,16),(x,y)],p.metal,2);p.box((x-2,y-2,x+2,y+2),p.shadow,p.dark);p.spark(x,y)
        p.gem(16,16,3,5)
    elif n==48:
        p.poly([(5,3),(26,3),(29,7),(29,24),(24,29),(7,29),(2,24),(2,7)],p.shadow)
        p.circuit(6,7,19,18);p.ring(11,15,5,2);p.ring(21,15,5,2)
        p.line([(8,12),(23,18)],p.glow,2);p.line([(8,18),(23,12)],p.glow,2)
        p.gem(16,15,2,4);p.box((11,1,21,3),p.light,p.dark);p.box((11,29,21,31),p.metal,p.dark)
    else:raise ValueError(n)
    return p.finish()


def arcane_art(n):
    p=canvas(n,True)
    if n==1:
        p.poly([(11,4),(17,2),(22,6),(20,12),(14,15),(9,11)],p.shadow)
        p.poly([(10,6),(15,4),(20,6),(18,8),(12,9)],p.metal)
        p.line([(15,14),(13,20),(16,26),(13,29)],p.metal,3)
        p.leaf(13,20,-1);p.leaf(15,24,1);p.gem(16,10,2,3)
    elif n==2:
        p.poly([(16,2),(21,9),(24,15),(23,21),(18,25),(11,24),(7,19),(9,12)],p.deep)
        p.poly([(15,5),(18,10),(18,19),(13,22),(10,18)],p.glow)
        p.line([(5,24),(10,27),(23,27),(27,23)],p.metal,2);p.rune(17,13,2)
    elif n==3:
        p.poly([(8,4),(20,2),(25,10),(22,24),(13,29),(5,22),(4,11)],p.shadow)
        p.rune(15,8,3);p.rune(12,17,4);p.line([(9,7),(20,5)],p.metal)
        p.gem(21,21,2,4);p.poly([(5,25),(9,28),(6,30),(3,27)],p.metal)
    elif n==4:
        p.line([(14,4),(23,6),(27,14),(23,23),(14,27),(6,22),(4,14),(9,8),(17,8),(21,13),(18,20),(12,20),(10,15),(14,12)],p.dark,5)
        p.line([(14,4),(23,6),(27,14),(23,23),(14,27),(6,22),(4,14),(9,8),(17,8),(21,13),(18,20),(12,20),(10,15),(14,12)],p.metal,3)
        p.gem(15,15,2,4);p.leaf(6,24,-1);p.spark(25,3)
    elif n==5:
        for k in range(5):
            a=k*math.tau/5-math.pi/2;x=round(16+8*math.cos(a));y=round(13+8*math.sin(a))
            p.poly([(16,13),(x-3,y-2),(x,y-5),(x+3,y+1),(16,16)],p.metal)
        p.gem(16,14,3,5);p.line([(16,18),(16,29)],p.deep,3);p.leaf(16,25,-1);p.leaf(16,22,1)
    elif n==6:
        vessel(p,7,9,18,17);p.gem(16,19,4,5)
        p.line([(12,8),(10,4),(12,1)],p.glow,2);p.line([(19,8),(22,4),(20,1)],p.metal,2)
        p.rune(16,12,6);p.box((10,27,22,30),p.shadow,p.dark)
    elif n==7:
        p.poly([(11,10),(16,6),(21,10),(23,19),(20,27),(12,27),(8,19)],p.shadow)
        p.gem(16,17,4,6)
        p.line([(11,11),(6,8),(5,3)],p.metal,3);p.line([(6,8),(3,7)],p.metal,2)
        p.line([(21,11),(26,8),(27,2)],p.metal,3);p.line([(26,8),(29,6)],p.metal,2)
        p.rune(16,24,7)
    elif n==8:
        p.poly([(5,16),(26,16),(28,22),(24,28),(9,28),(3,22)],p.shadow)
        p.box((3,14,28,17),p.metal,p.dark);p.gem(16,21,3,4)
        p.d.arc((9,1,23,15),45,310,fill=p.glow,width=3);p.spark(6,7)
        p.line([(9,29),(7,31)],p.metal,2);p.line([(23,29),(25,31)],p.metal,2)
    elif n==9:
        for x,y,d in [(15,14,-1),(16,16,1),(15,25,-1),(16,7,1)]:p.leaf(x,y,d)
        p.ring(16,16,8,2,True);p.gem(16,16,3,5)
        p.rune(4,12,9);p.rune(27,17,10);p.line([(16,2),(16,29)],p.metal)
    elif n==10:
        book(p,4,6,23,21);p.gem(16,16,4,6);p.rune(9,11,10);p.rune(23,16,11)
        p.poly([(12,3),(16,1),(21,3),(18,6),(14,6)],p.deep);p.bolt(4,10);p.bolt(27,23)
    elif n==11:
        halo(p,16,14,10,.4);p.poly([(18,4),(12,15),(17,15),(13,28),(23,12),(17,12)],p.glow)
        p.line([(3,17),(7,19),(5,23)],p.metal);p.line([(25,6),(29,8),(26,12)],p.metal)
    elif n==12:
        p.d.ellipse((5,3,27,28),fill=p.dark);p.d.ellipse((6,4,26,27),fill=p.metal)
        p.d.ellipse((12,1,30,23),fill=(0,0,0,0));vessel(p,9,12,11,15);p.gem(15,20,2,4)
        p.rune(8,11,12);p.spark(24,27)
    elif n==13:
        halo(p,16,15,11,.1);vessel(p,10,7,12,19)
        p.poly([(16,11),(20,18),(16,23),(12,18)],p.glow);p.rune(25,21,13)
        p.line([(16,2),(16,5)],p.light,2)
    elif n==14:
        p.poly([(16,2),(26,8),(26,23),(16,30),(6,23),(6,8)],p.metal)
        p.poly([(16,5),(23,10),(23,21),(16,26),(9,21),(9,10)],p.deep)
        for x in [11,16,21]:p.line([(x,8),(x,24)],p.metal)
        p.gem(16,16,3,6);p.rune(4,12,14);p.spark(28,25)
    elif n==15:
        p.poly([(16,1),(19,10),(25,5),(23,15),(28,13),(26,23),(20,29),(11,28),(5,22),(5,15),(10,17),(10,7),(14,13)],p.deep)
        p.poly([(16,9),(20,18),(18,26),(12,26),(10,21),(13,16)],p.glow)
        p.gem(16,21,2,4);p.rune(3,5,15)
    elif n==16:
        for x,y,rx,ry in [(8,12,3,6),(22,12,3,7),(16,19,4,8)]:p.gem(x,y,rx,ry)
        p.line([(5,21),(5,27),(27,27),(27,21)],p.metal,2)
        p.line([(16,2),(16,7)],p.light);p.spark(3,5);p.spark(27,4)
    elif n==17:
        book(p,5,10,21,18);p.gem(16,18,3,6)
        halo(p,16,7,5,.7);p.rune(9,16,17);p.rune(23,18,18)
        p.poly([(4,3),(8,4),(6,8),(2,7)],p.glow)
    elif n==18:
        vessel(p,6,7,20,22);p.line([(16,25),(16,13)],p.glow,2)
        p.leaf(16,20,-1);p.leaf(16,15,1);p.gem(16,9,2,3)
        p.line([(4,12),(2,17),(4,22)],p.metal);p.line([(28,12),(30,17),(28,22)],p.metal)
    elif n==19:
        p.poly([(4,5),(11,8),(16,4),(21,8),(28,5),(26,18),(21,26),(16,29),(10,26),(6,18)],p.shadow)
        p.poly([(8,11),(12,9),(13,16),(9,17)],p.glow);p.poly([(19,9),(24,11),(23,17),(19,16)],p.glow)
        p.gem(16,21,2,5);p.rune(15,5,19)
    elif n==20:
        p.poly([(16,5),(20,9),(23,17),(20,25),(12,25),(9,17),(12,9)],p.metal)
        p.poly([(11,12),(3,4),(2,16),(7,24),(11,20)],p.shadow)
        p.poly([(21,12),(29,4),(30,16),(25,24),(21,20)],p.shadow)
        p.gem(16,16,3,6);p.line([(13,26),(10,30)],p.glow);p.line([(19,26),(22,30)],p.glow)
    elif n==21:
        p.poly([(3,8),(9,14),(12,3),(16,12),(21,3),(24,14),(29,8),(26,26),(7,26)],p.metal)
        p.box((7,23,26,28),p.shadow,p.dark);p.gem(16,19,3,6)
        p.leaf(8,22,-1);p.leaf(25,22,1);p.rune(10,24,21)
    elif n==22:
        diamond(p,16,16,12);p.gem(16,16,5,9)
        p.poly([(5,4),(10,4),(8,12),(11,12),(4,24),(6,15),(3,15)],p.glow)
        p.poly([(25,6),(29,6),(26,15),(29,15),(22,28),(24,18),(21,18)],p.metal)
    elif n==23:
        p.ring(16,16,11,2);p.poly([(5,25),(13,5),(18,5),(28,25)],p.metal)
        p.poly([(10,22),(15,11),(17,11),(22,22)],(0,0,0,0))
        p.gem(16,17,2,4);p.line([(8,26),(25,8)],p.glow,2);p.rune(4,11,23)
    elif n==24:
        p.poly([(7,2),(25,6),(28,23),(12,29),(3,17)],p.shadow)
        p.ring(16,15,9,3,True);p.gem(16,15,4,7)
        p.rune(8,4,24);p.rune(23,24,25);p.spark(3,25)
    elif n==25:
        p.poly([(8,6),(11,3),(14,6),(14,12),(16,3),(19,3),(20,12),(24,5),(27,7),(24,18),(22,25),(15,29),(8,24),(5,15),(3,12),(5,10),(10,16)],p.metal)
        p.gem(16,19,3,6);p.rune(13,8,25);p.spark(28,25)
    elif n==26:
        p.line([(16,29),(15,20),(17,11),(15,3)],p.metal,3)
        p.leaf(16,24,-1);p.leaf(15,10,1);p.leaf(15,6,-1)
        p.poly([(16,12),(23,15),(24,21),(19,25),(13,22),(12,17)],p.deep)
        p.gem(18,19,3,5);p.ring(8,15,4,1)
    elif n==27:
        halo(p,16,16,12,.3);p.poly([(16,4),(22,15),(21,23),(16,27),(10,23),(10,16)],p.deep)
        p.poly([(16,9),(19,16),(18,22),(14,24),(12,20)],p.glow)
        p.line([(6,9),(25,24)],p.metal);p.line([(7,24),(25,8)],p.metal)
    elif n==28:
        p.poly([(16,1),(20,11),(30,15),(22,20),(20,29),(15,24),(8,29),(9,20),(1,15),(11,11)],p.metal)
        p.ring(16,15,6,2,True);p.gem(16,15,2,5)
        p.rune(7,4,28);p.spark(28,27)
    elif n==29:
        p.ring(16,16,9,3)
        for k in range(8):
            a=k*math.pi/4;p.poly([(round(16+11*math.cos(a-.12)),round(16+11*math.sin(a-.12))),
                                   (round(16+15*math.cos(a)),round(16+15*math.sin(a))),
                                   (round(16+11*math.cos(a+.12)),round(16+11*math.sin(a+.12)))],p.metal)
        p.gem(16,16,4,6);p.rune(15,10,29)
    elif n==30:
        p.poly([(2,15),(8,8),(16,5),(24,8),(30,15),(24,22),(16,25),(8,22)],p.metal)
        p.poly([(5,15),(10,11),(16,9),(22,11),(27,15),(22,19),(16,21),(10,19)],p.deep)
        p.gem(16,15,3,7);p.line([(10,26),(8,30)],p.glow);p.line([(22,26),(24,30)],p.glow);p.spark(6,3)
    elif n==31:
        p.poly([(6,5),(13,8),(17,3),(22,7),(19,15),(23,24),(17,29),(11,25),(10,17),(4,11)],p.metal)
        p.gem(16,17,3,7);p.leaf(9,20,-1);p.leaf(20,12,1)
        p.line([(8,26),(5,29)],p.glow,2);p.rune(24,18,31);p.spark(5,4)
    elif n==32:
        p.poly([(16,2),(28,8),(26,21),(21,27),(16,31),(10,27),(5,21),(3,8)],p.shadow)
        p.poly([(16,5),(25,10),(23,20),(16,27),(9,20),(6,10)],p.metal)
        p.gem(16,15,4,7);p.rune(5,3,32);p.rune(26,25,33)
    elif n==33:
        vessel(p,8,6,16,22);p.gem(16,19,4,7)
        p.d.arc((1,1,18,18),80,315,fill=p.metal,width=2)
        p.poly([(24,4),(28,6),(25,9),(22,7)],p.light)
        p.line([(6,22),(4,27),(7,29)],p.glow);p.line([(26,15),(29,20),(27,25)],p.glow)
    elif n==34:
        p.line([(6,6),(12,12),(22,16),(25,25)],p.metal,3)
        for x,y in [(6,6),(12,13),(23,18),(25,26)]:
            p.ring(x,y,4,1);p.gem(x,y,1,3)
        p.poly([(20,1),(24,6),(21,10),(17,6)],p.light);p.rune(4,21,34)
    elif n==35:
        p.gem(16,12,6,10);p.ring(16,24,9,2,True)
        p.line([(8,18),(5,21),(5,28)],p.metal,2);p.line([(24,18),(27,21),(27,28)],p.metal,2)
        p.spark(4,7);p.spark(27,4);p.rune(15,23,35)
    elif n==36:
        p.ring(12,15,9,3,True);p.ring(21,18,8,2)
        p.poly([(6,5),(10,2),(13,6),(9,9)],p.glow);p.gem(16,16,3,6)
        p.line([(4,25),(10,29),(22,28),(28,23)],p.metal);p.rune(25,6,36)
    elif n==37:
        p.d.ellipse((4,3,27,27),fill=p.dark);p.d.ellipse((5,4,26,26),fill=p.metal)
        p.d.ellipse((12,1,30,20),fill=(0,0,0,0));p.gem(15,18,3,6)
        p.line([(11,26),(14,30),(18,26)],p.deep,2);p.rune(8,11,37);p.spark(26,25)
    elif n==38:
        book(p,4,7,23,21)
        for x,y in [(9,13),(21,13),(9,22),(22,22)]:p.ring(x,y,3,1);p.gem(x,y,1,2)
        p.ring(16,3,2,1);p.line([(16,5),(16,9)],p.glow);p.bolt(4,26);p.bolt(27,9)
    elif n==39:
        p.poly([(16,1),(22,9),(25,16),(24,24),(18,30),(11,28),(6,22),(7,13)],p.deep)
        p.poly([(15,4),(19,12),(17,19),(20,25),(14,27),(10,20),(12,12)],p.glow)
        p.poly([(17,7),(15,15),(19,20),(16,26),(21,21),(19,14)],p.dark)
        p.spark(3,6);p.rune(27,12,39)
    elif n==40:
        p.poly([(16,4),(20,10),(19,25),(16,30),(12,25),(12,10)],p.shadow)
        p.poly([(12,12),(3,3),(3,16),(8,24),(11,18)],p.metal)
        p.poly([(20,12),(29,3),(29,16),(24,24),(21,18)],p.metal)
        p.gem(16,17,3,8);p.rune(15,6,40);p.spark(4,28)
    elif n==41:
        p.poly([(3,4),(11,8),(16,3),(21,8),(29,4),(27,17),(22,25),(16,30),(9,25),(5,17)],p.metal)
        p.poly([(7,15),(12,10),(20,10),(25,15),(20,21),(12,21)],p.deep)
        p.gem(16,15,3,6);p.line([(16,22),(16,27)],p.glow,2);p.rune(4,23,41)
    elif n==42:
        p.poly([(16,1),(20,9),(28,4),(24,13),(31,16),(24,20),(28,29),(20,24),(16,31),(12,24),(3,28),(8,20),(1,16),(8,12),(4,4),(12,8)],p.metal)
        p.poly([(16,6),(20,13),(25,16),(19,20),(16,26),(12,20),(6,16),(12,12)],p.deep)
        p.gem(16,16,3,6);p.line([(5,1),(8,5)],p.glow);p.line([(27,26),(30,30)],p.glow)
    elif n==43:
        p.ring(16,18,10,2);p.poly([(4,7),(11,12),(16,1),(21,12),(28,7),(24,25),(8,25)],p.metal)
        p.gem(16,17,3,7);p.line([(11,28),(21,28)],p.glow,2)
        p.line([(5,15),(2,18),(5,21)],p.deep);p.line([(27,15),(30,18),(27,21)],p.deep)
    elif n==44:
        halo(p,16,16,11,.5)
        p.ring(16,16,5,2);p.gem(16,16,2,4)
        for x,y in [(8,3),(28,12),(21,29),(3,23)]:p.ring(x,y,3,1);p.spark(x,y)
        p.rune(6,13,44);p.rune(24,22,45)
    elif n==45:
        p.line([(16,4),(16,28)],p.metal,3);p.line([(5,11),(27,11)],p.metal,2)
        p.poly([(16,1),(20,5),(16,9),(12,5)],p.glow)
        for x in [6,26]:
            p.line([(x,12),(x,20)],p.light)
            p.poly([(x-4,20),(x+4,20),(x+2,24),(x-2,24)],p.shadow)
        p.box((9,28,23,30),p.metal,p.dark);p.gem(16,19,2,4)
    elif n==46:
        p.ring(16,16,10,3,True);p.d.ellipse((10,10,22,22),fill=p.dark)
        p.line([(5,7),(9,3),(19,2),(26,6),(29,15),(26,24),(19,29)],p.glow,2)
        p.poly([(6,25),(10,23),(9,29),(5,30)],p.metal);p.spark(3,14);p.rune(25,24,46)
    elif n==47:
        p.line([(15,12),(18,30)],p.metal,3)
        p.ring(15,9,7,2,True);p.gem(15,9,3,5)
        for x,y in [(3,5),(27,3),(28,19),(5,22)]:p.line([(15,9),(x,y)],p.shadow);p.spark(x,y)
        p.rune(23,23,47);p.poly([(14,25),(22,24),(23,28),(15,29)],p.deep)
    elif n==48:
        p.poly([(2,8),(9,12),(12,2),(16,10),(21,2),(24,12),(30,8),(27,25),(22,29),(9,29),(5,25)],p.metal)
        p.ring(11,19,5,2);p.ring(22,19,5,2)
        p.line([(8,16),(25,22)],p.glow,2);p.line([(8,22),(25,16)],p.glow,2)
        p.gem(16,15,2,6);p.box((8,27,25,30),p.shadow,p.dark);p.spark(3,2);p.spark(29,29)
    else:raise ValueError(n)
    return p.finish()


def automation_art():
    p=canvas(24)
    pipe(p,[(4,5),(16,5),(16,14),(27,14),(27,26),(16,26)],3)
    p.gear(10,18,9,8);p.circuit(7,15,6,6)
    p.poly([(13,23),(18,26),(13,29)],p.glow)
    p.poly([(2,2),(7,5),(2,8)],p.metal)
    for x in [22,27]:p.bolt(x,6)
    return p.finish()


def write_asset(item,texture,image,name,entries,**fields):
    target=ASSETS/'textures'/(texture.split(':',1)[1]+'.png')
    target.parent.mkdir(parents=True,exist_ok=True)
    image.save(target,compress_level=9)
    model=ASSETS/'models/item'/(item.split(':',1)[1]+'.json')
    model.parent.mkdir(parents=True,exist_ok=True)
    model.write_text(json.dumps({'parent':'minecraft:item/generated','textures':{'layer0':texture}},indent=2)+'\n')
    entry={'id':item,'name_uk':name,'texture':texture,'model':'kubejs:item/'+item.split(':',1)[1],
           'png':target.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),**fields}
    entries.append(entry)
    return entry


def contact_sheet(keys):
    # Eight icons per row: two roles for four neighboring epochs.
    scale=4;cellw=310;cellh=170
    sheet=Image.new('RGB',(cellw*4,cellh*12),(20,24,34));draw=ImageDraw.Draw(sheet)
    try:font=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',10)
    except OSError:font=ImageFont.load_default()
    for n in range(1,49):
        x=(n-1)%4*cellw;y=(n-1)//4*cellh
        for i,role in enumerate(['tech','arcane']):
            entry=next(k for k in keys if k['epoch']==n and k['branch']==role)
            xx=x+i*151+10
            for a in range(0,128,16):
                for b in range(0,128,16):
                    c=(36,42,53) if (a//16+b//16)%2 else (28,33,44)
                    draw.rectangle((xx+a,y+b+3,xx+a+15,y+b+18),fill=c)
            im=Image.open(ROOT/entry['png']).resize((128,128),Image.Resampling.NEAREST)
            sheet.paste(im,(xx,y+3),im)
            text=f'{n:02d} {"Тех" if role=="tech" else "Маг"}: '+entry['name_uk']
            lines=['']
            for word in text.split():
                trial=(lines[-1]+' '+word).strip()
                if draw.textlength(trial,font=font)>145:lines.append(word)
                else:lines[-1]=trial
            for j,line in enumerate(lines[:2]):draw.text((xx,y+137+j*12),line,font=font,fill=(224,231,239))
    target=ROOT/'implementation/dual-keys-preview.png';target.parent.mkdir(exist_ok=True)
    sheet.save(target)


def main():
    epochs=json.loads((ROOT/'design/progression.json').read_text())['epochs']
    legacy_manifest=json.loads((ROOT/'content/resources/manifest.json').read_text())
    legacy_paths=[ROOT/entry['png'] for entry in legacy_manifest['assets']]
    before={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in legacy_paths}
    entries=[];keys=[]
    for e in epochs:
        n=e['number']
        for role,art,names in [('tech',tech_art,TECH_NAMES),('arcane',arcane_art,ARCANE_NAMES)]:
            lore=[e['theme'],
                  ('Технологічна складова переходу: підтверджує завершення виробничої гілки.' if role=='tech'
                   else 'Магічно-дослідницька складова переходу: підтверджує окрему гілку знань.'),
                  'Для переходу потрібні обидва ключі та фінальне випробування. Сам предмет не відкриває епоху.']
            entry=write_asset(f'kubejs:aia2_{role}_key_{n:02d}',f'kubejs:item/aia2/dual_keys/{role}_{n:02d}',
                              art(n),names[n-1],entries,epoch=n,branch=role,lore_uk=lore)
            keys.append(entry)
    automation=write_asset('kubejs:aia2_section_automation','kubejs:item/aia2/sections/automation',
                           automation_art(),'Автоматизація',entries,role='section')
    manifest={'schema':1,'generator':'tools/generate_dual_key_resources.py','dimensions':[32,32],
              'keys':keys,'automation_icon':automation,'assets':entries}
    output=ROOT/'content/resources/dual-keys.json';output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n')
    silhouettes=[];opaque=[]
    for entry in entries:
        with Image.open(ROOT/entry['png']) as im:
            assert im.mode=='RGBA' and im.size==(32,32),entry['id']
            alpha=im.getchannel('A');assert alpha.getextrema()==(0,255),entry['id']
            pixels=sum(bool(a) for a in alpha.tobytes());assert 40<pixels<1000,(entry['id'],pixels)
            opaque.append(pixels)
            if entry.get('branch'):silhouettes.append(hashlib.sha256(alpha.tobytes()).hexdigest())
        model=json.loads((ASSETS/'models/item'/(entry['id'].split(':')[1]+'.json')).read_text())
        assert model['textures']['layer0']==entry['texture'],entry['id']
    assert len(set(x['sha256'] for x in entries))==97,'Identical images'
    assert len(set(silhouettes))==96,'Dual-key silhouettes must be individually composed'
    assert all(hashlib.sha256(p.read_bytes()).hexdigest()==digest for p,digest in before.items()),'Legacy key changed'
    contact_sheet(keys)
    report={'status':'passed','keys':96,'tech_keys':48,'arcane_keys':48,'automation_icons':1,
            'png_textures':97,'item_models':97,'unique_texture_hashes':97,
            'unique_key_alpha_silhouettes':len(set(silhouettes)),
            'preserved_legacy_keys':len(legacy_manifest['keys']),
            'preserved_legacy_textures':len(before),
            'dimensions':[32,32],'transparent_pngs':97,'opaque_pixel_range':[min(opaque),max(opaque)],
            'minecraft_client_resource_loading':'not_run'}
    (ROOT/'implementation/resource-dual-report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
