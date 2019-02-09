import pygame
import sys, getopt
import numpy as np
import time

#Constants
size_win_x = 600
size_win_y = 600
red = (255,0,0)
green = (0,255,0)
blue = (0,0,255)
white = (255,255,255)
black = (0,0,0)
circles = []
screen = []

def wait():
	while True:
		for event in pygame.event.get():
			if event.type == pygame.QUIT:
				pygame.quit()
				sys.exit()
			if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
				return

def init_gui():
	global screen
	global myfont
	pygame.init()
	pygame.font.init()
	myfont = pygame.font.SysFont('Comic Sans MS', 20)
	screen = pygame.display.set_mode((size_win_x,size_win_y))
	screen.fill((255,255,255))
	draw_circles()
	pygame.display.update()

def draw_circles():
	global circles
	for i in ("Farming","Design","Manufacturing","Packing","Transportation","President"):
		circle_unassigment(i)

def circle_assigment(id,value,assigned):
	global circles
	if assigned == True:
		color = green
	else:
		color = black

	nombre = {'Y':["You",0],'M': ["Mike",15],'J': ["James",30],'E': ["Emily",45],'T': ["Tom",60],'A': ["Amy",75]}

	if id == "Farming":
		x = 300
		y = 100
	elif id == "Design":
		x = 500
		y = 300
	elif id == "Manufacturing":
		x = 400
		y = 500
	elif id == "Packing":
		x = 200
		y = 500
	elif id == "Transportation":
		x = 100
		y = 300
	elif id == "President":
		x = 300
		y = 300

	radio = 50
	grosor = radio - 2
	textsurface = myfont.render(nombre[value][0], False, color)
	screen.blit(textsurface,(x-15,y-42 + nombre[value][1]))
	pygame.display.update()

def circle_unassigment(id):
	global circles
	radio = 50
	grosor = radio - 2
	if id == "Farming":
		pygame.draw.circle(screen,black,(300,100),radio)
		pygame.draw.circle(screen,white,(300,100),grosor)
		textsurface = myfont.render('Farming', False, black)
		screen.blit(textsurface,(270,35))
	elif id == "Design":
		pygame.draw.circle(screen,black,(500,300),radio)
		pygame.draw.circle(screen,white,(500,300),grosor)
		textsurface = myfont.render('Design', False, black)
		screen.blit(textsurface,(470,235))
	elif id == "Manufacturing":
		pygame.draw.circle(screen,black,(400,500),radio)
		pygame.draw.circle(screen,white,(400,500),grosor)
		textsurface = myfont.render('Manufacturing', False, black)
		screen.blit(textsurface,(350,435))
	elif id == "Packing":
		pygame.draw.circle(screen,black,(200,500),radio)
		pygame.draw.circle(screen,white,(200,500),grosor)
		textsurface = myfont.render('Packing', False, black)
		screen.blit(textsurface,(170,435))
	elif id == "Transportation":
		pygame.draw.circle(screen,black,(100,300),radio)
		pygame.draw.circle(screen,white,(100,300),grosor)
		textsurface = myfont.render('Transportation', False, black)
		screen.blit(textsurface,(50,235))
	elif id == "President":
		pygame.draw.circle(screen,black,(300,300),radio)
		pygame.draw.circle(screen,white,(300,300),grosor)
		textsurface = myfont.render('President', False, black)
		screen.blit(textsurface,(270,235))
	pygame.display.update()

def update_assign_domain(id,domain,has_assigment):
	global circles
	circle_unassigment(id)
	if has_assigment==False:
		for i in domain:
			circle_assigment(id,i,False)
	else:
		for i in domain:
			circle_assigment(id, i, True)
	pygame.display.update()