import time
import random
import math
import pygame
from pygame.math import Vector2
from engine.game.asteroid import AsteroidManagerScript
from engine.core.objects import LogicComponent, TextRenderer, CircleRenderer, MouseFollower, Rigidbody
from engine.core.objects import SpriteRenderer, ShipController, BackgroundRenderer, Button
from engine.game.weapon import Weapon, BulletFactory
from engine.core.physics import RectCollider
from engine.core.utilities import scaled_number, scale_number_with_meter

class GameManager(LogicComponent):

    """
    Esta classe é responsavel pela lógica do jogo
    """

    def __init__(self):
        super().__init__()
        self.__asteroid_manager = None
        self.__time_between_asteroids = 1
        self.__next_asteroid_time = 0
        self.__max_asteroids = 40
        self.__start_time = time.time()
        self.__current_level = 0
        self.__level_in_last_frame = 0
        self.__min_size = 1
        self.__max_size = 6
        self.__min_velocity = 1
        self.__max_velocity = 60
        self.__screen_width = 0
        self.__screen_height = 0
        self.__player_score = 0
        self.__evt_sys = None
        self.__app = None
        self.__game_over_text = None
        self.__logo_gm = None
        self.__play_btn_gm = None
    
    def update_score(self, callback_params):
        """
        Atualiza a pontuação do jogador
        """
        if not 'score' in callback_params:
            return

        self.__player_score += callback_params['score']
        params = dict()
        params['score'] = self.__player_score
        self.__evt_sys.fire_event('ScoreUpdate', params)

    def create_menu(self):
        """
        Cria o menu inicial do jogo
        """
        play_button_gm = self.__app.add_game_object()
        txt = play_button_gm.add_component(TextRenderer)
        btn = play_button_gm.add_component(Button)
        txt.set_background_color((255, 255, 255))
        txt.set_font_color((0, 0 , 0))
        txt.set_text("PLAY")
        play_button_gm.get_transform().position = Vector2(self.__screen_width/2, self.__screen_height/2)
        btn.set_event_name("StartGame")

        logo_gm = self.__app.add_game_object()
        logo_text = logo_gm.add_component(TextRenderer)
        logo_text.set_font('Arial', 3)
        logo_text.set_text("ARCTURUS")
        logo_gm.get_transform().position = Vector2(self.__screen_width/2, self.__screen_height/3)

        self.__logo_gm = logo_gm
        self.__play_btn_gm = play_button_gm
    def create_objects(self):
        """
        Cria os objetos que compõe o cenário e a parte jogavel da aplicação
        """
        background_image_gm = self.__app.add_game_object()
        background_image_gm.set_sorting_layer_index(5)
        background_renderer = background_image_gm.add_component(BackgroundRenderer)
        background_renderer.set_new_sprite('starfield')
        score = self.__app.add_game_object()
        text_renderer = score.add_component(TextRenderer)
        text_renderer.set_text("0")
        score.get_transform().position = Vector2(self.__screen_width/2, 32)
        score.add_component(ScoreListener)
        GameOver = self.__app.add_game_object()
        txt_render = GameOver.add_component(TextRenderer)
        txt_render.set_text("GAME OVER - SCORE: ")
        self.__game_over_text = txt_render
        GameOver.get_transform().position = Vector2(self.__screen_width/2, self.__screen_height/2)
        GameOver.set_state(False)

    def start_game(self):
        """
        Inicia o jogo
        """
        self.__evt_sys.clear_event('1clickdown')
        self.__logo_gm.set_state(False)
        self.__play_btn_gm.set_state(False)
        self.create_objects()
        self.__app.enqueue_method(self.create_ship, 3)
        self.__asteroid_manager.remove_all_asteroids()
        pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
    def end_game(self, callback_params):
        """
        Termina o jogo atual
        """
        self.__game_over_text.set_text("GAME OVER - FINAL SCORE: {} - LEVEL: {}".format(int(self.__player_score), self.__current_level))
        self.__game_over_text.get_owner().set_state(True)
        self.__app.enqueue_method(self.restart_game, 500)

    def restart_game(self):
        """
        Essa função reinicia o jogo
        """
        self.__current_level = 0
        self.__start_time = time.time()
        self.__player_score = 0
        params = dict()
        params['score'] = 0
        self.update_score(params)
        self.__game_over_text.get_owner().set_state(False)
        self.start_game()        

    def create_ship(self):
        """
        Cria a nave do jogador
        """
        ship_cursor = self.__app.add_game_object()
        cr = ship_cursor.add_component(CircleRenderer)
        ship_cursor.add_component(MouseFollower)
        cr.set_radius(int(scale_number_with_meter(0.5)))
        cr.set_color((255, 127, 0))
        ship = self.__app.add_game_object()
        ship.get_transform().position = Vector2(self.__screen_width/2, self.__screen_height/2)
        spr = ship.add_component(SpriteRenderer)
        spr.set_new_sprite('ship_2')
        ship.set_sorting_layer_index(1)
        dimensions = spr.get_dimensions()
        spr.set_sprite_scale_in_meters(2)
        ship.add_component(RectCollider)
        ship.add_component(BulletFactory)
        ship.add_component(Weapon)
        rb = ship.add_component(Rigidbody)
        shipController = ship.add_component(ShipController)
        shipController.set_ship_cursor_transform(ship_cursor.get_transform())
        rb.linear_drag = scaled_number(0.01)
        rb.angular_drag = 0.1

    def on_component_creation(self):
        self.__asteroid_manager = self.get_owner().get_component(AsteroidManagerScript)
        self.__screen_width = self.get_owner().get_application().get_display().get_width()
        self.__screen_height = self.get_owner().get_application().get_display().get_height()
        self.__evt_sys = self.get_owner().get_application().get_event_system()
        self.__evt_sys.register_event_callback('CometExplosion', self.update_score)
        self.__app = self.get_owner().get_application()
        self.__evt_sys.register_event_callback('GameOver', self.end_game)
        self.create_menu()
        self.__evt_sys.register_event_callback('StartGame', lambda params: self.start_game())

    def calculate_curent_level(self):
        """
        Calcula o level em que o jogador esta com base no tempo decorrido desde o inicio da partida
        """
        self.__current_level = int((time.time() - self.__start_time)//10) + 1
        if self.__current_level != self.__level_in_last_frame:
            self.__level_in_last_frame = self.__current_level
            self.calculate_new_parameters()

    def calculate_new_parameters(self):
        """
        Calcula os novos parametros do jogo
        """
        self.__min_size = max(6.8192*math.pow(0.9380, self.__current_level), 3)
        self.__max_size = max(15.839214*math.pow(0.96, self.__current_level), 6)
        self.__min_velocity = min(math.pow(1.095, self.__current_level), 20)
        self.__max_velocity = min(8*math.pow(1.07, self.__current_level), 50)
        self.__max_asteroids = math.floor(min(5*math.pow(1.06, self.__current_level), 60))
        self.__time_between_asteroids = 3*math.pow(0.97, self.__current_level)

    def update(self):   
        self.calculate_curent_level()
        if time.time() >= self.__next_asteroid_time and self.__asteroid_manager.get_asteroid_count() < self.__max_asteroids:
            asteroid_size = random.uniform(self.__min_size, self.__max_size)
            asteroid_quadrant = random.randint(1, 4)
            position = Vector2()
            if asteroid_quadrant == 1:
                position.y = -500
                position.x = random.uniform(0, self.__screen_width)
            elif asteroid_quadrant == 2:
                position.y = self.__screen_height + 500
                position.x = random.uniform(0, self.__screen_width)
            elif asteroid_quadrant == 3:
                position.x = - 500
                position.y = random.uniform(0, self.__screen_height)
            else:
                position.x = self.__screen_width + 500
                position.y = random.uniform(0, self.__screen_height)

            angle = random.uniform(0, math.pi*2)
            initial_velocity = Vector2(math.cos(angle), math.sin(angle))*random.uniform(self.__min_velocity, self.__max_velocity)
            
            self.__asteroid_manager.instantiate_asteroid(asteroid_size, position, initial_velocity)
            self.__next_asteroid_time = time.time() + self.__time_between_asteroids

class ScoreListener(LogicComponent):

    def __init__(self):
        super().__init__()
        self.__evt_sys = None
        self.__text_renderer = None

    def on_component_creation(self):
        self.__evt_sys = self.get_owner().get_application().get_event_system()
        self.__text_renderer = self.get_owner().get_component(TextRenderer)
        self.__evt_sys.register_event_callback('ScoreUpdate', self.update_text)

    def update_text(self, callback_params):
        """
        Atualiza o texto no componente de texto
        """
        self.__text_renderer.set_text(str(int(callback_params['score'])))