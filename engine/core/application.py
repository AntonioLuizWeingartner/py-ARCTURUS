"""
Esse módulo contem a classe que representa a aplicação
é o objeto que contem todos os objetos da aplicação
"""

from typing import List, Dict, Callable, Any
import time
import pygame
from pygame.math import Vector2
from engine.core.objects import GameObject, ImageLoader, Object, SoundManager, TextRenderer
from engine.core.physics import PhysicManager

class EventSystem(Object):

    """
    Essa classe é responsável por realizar a comunicação entre as classes
    da aplicação. Extremamente útil para desacoplar código.
    """

    def __init__(self):
        super().__init__()
        self.__registered_events: Dict[str, List[Callable[[Dict[str, Any]], None]]] = dict()
        self.__registered_events_one_shot: Dict[str, List[Callable[[Dict[str, Any]], None]]] = dict()


    def clear_event(self, event_name: str):
        """
        Remove todos as callbacks registradas para um evento especifico
        """
        self.__registered_events[event_name] = list()
        
    def register_event_callback(self, event_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Registra uma função que sera chamada quando o evento
        identificado por 'event_name' for disparado
        """

        if event_name not in self.__registered_events:
            self.__registered_events[event_name] = list()

        self.__registered_events[event_name].append(callback)

    def register_event_callback_one_shot(self, event_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Registra uma função que sera chamada quando o evento
        identificado por 'event_name' for disparado
        """

        if event_name not in self.__registered_events:
            self.__registered_events_one_shot[event_name] = list()

        self.__registered_events_one_shot[event_name].append(callback)

    def fire_event(self, event_name: str, evt_args: Dict[str, Any] = None):
        """
        dispara o evento identificado por 'event_name'
        """
        if event_name not in self.__registered_events:
            return
        else:
            for callback in self.__registered_events[event_name]:
                callback(evt_args)

    def fire_event_one_shot(self, event_name: str, evt_args: Dict[str, Any] = None):
        """
        dispara o evento identificado por 'event_name'
        """
        if event_name not in self.__registered_events_one_shot:
            return
        else:
            for callback in self.__registered_events_one_shot[event_name]:
                callback(evt_args)
                self.__registered_events_one_shot[event_name].remove(callback)

    def remove_callback(self, event_name: str, callback: Callable[[Dict[str, Any]], None]):
        """
        Remove a relação entre a função e o evento identificado por 'event_name'
        """

        if event_name in self.__registered_events:
            for clbk in self.__registered_events[event_name]:
                if clbk == callback:
                    self.__registered_events[event_name].remove(callback)

class KeyboardManager(Object):

    """
    Essa classe faz interface com o teclado
    """

    def __init__(self):
        super().__init__()
        self.keyboard_states: Dict[int, bool] = dict()

    def set_key_state(self, key: int, state: bool):
        """
        Seta o estado de uma tecla.
        Essa função não deve ser chamada pelo usuario.
        """
        self.keyboard_states[key] = state

    def get_key(self, key: int) -> bool:
        """
        Retorna o estado de uma tecla
        """
        if key in self.keyboard_states:
            return self.keyboard_states[key]
        return False

class MouseManager(Object):
    """
    Essa classe faz interface com o mouse
    """
    def get_mouse_position(self) -> Vector2:
        """
        Este método retorna a posição atual do mouse
        """
        m_pos = pygame.mouse.get_pos()
        return Vector2(m_pos[0], m_pos[1])

    def get_mouse_key_state(self, key_index: int) -> bool:
        """
        Este método retorna o estado de um botão especifico do mouse
        """
        return pygame.mouse.get_pressed()[key_index]


class Application(Object):
    """
    Essa classe contem todos os objetos da aplicação e controla o fluxo do programa
    """
    def __init__(self):
        super().__init__()
        pygame.mixer.pre_init(44100, -16, 2, 512)
        pygame.mixer.init()
        pygame.init()
        pygame.font.init()
        self.__game_objects = list()
        self.__application_display = pygame.display.set_mode((1400,850))
        self.__run_game = True
        self.__event_system = EventSystem()
        self.__keyboard = KeyboardManager()
        self.__img_loader = ImageLoader()
        self.__mouse = MouseManager()
        self.__physic = PhysicManager()
        self.__sound_manager = SoundManager()
        self.__logic_frame_rate = 60.0
        self.__logic_frame_duration = 1/self.__logic_frame_rate
        self.__logic_frame_duration_ns = self.__logic_frame_duration*1e9
        self.__last_update_timestamp = 0.0
        self.__pause_game = False
        self.__current_frame = 0
        self.__queued_methods = list()
        self.__sorting_layers: List[List[GameObject]] = list()
        
      
        for i in range(32):
            self.__sorting_layers.append(list())

        self.__meter = self.__application_display.get_size()[0]/100
        self.__render_interpolation = 0.0
        
        self.__pause_text = self.add_game_object()
        txt = self.__pause_text.add_component(TextRenderer)
        txt.set_font('Arial', 3.2)
        txt.set_text("GAME PAUSED - PRESS 'Q' TO QUIT OR ESC TO UNPAUSE")
        self.__pause_text.get_transform().position = Vector2(self.__application_display.get_width()/2, self.__application_display.get_height()/2)
        self.__pause_text.set_state(False)

    def add_game_object(self) -> GameObject:
        """
        Adiciona um novo GameObject à aplicação e retorna ele
        """
        game_object = GameObject()
        game_object.set_application(self)
        self.__game_objects.append(game_object)
        self.__sorting_layers[0].append(game_object)
        return game_object
    
    def get_game_object_by_id(self, id):
        """
        Retorna um game object por id
        """
        for gm in self.__game_objects:
            if gm.get_id() == id:
                return gm
    
    def remove_game_object_by_id(self, id):
        """
        Remove um game object por id
        """
        self.remove_game_object(self.get_game_object_by_id(id))

    def remove_game_object(self, game_object: GameObject):
        """
        Delete um game_object especifico
        """
        try:
            self.__sorting_layers[game_object.get_sorting_layer_index()].remove(game_object)
        except:
            pass
        try:
            self.__game_objects.remove(game_object)
        except:
            pass
        try:
            game_object.destroy()
        except:
            pass
        del game_object

    def change_game_object_sorting_layer(self, game_object: GameObject, target_layer: int) -> int:
        """
        Altera a layer de um game object
        """
        current_layer = game_object.get_sorting_layer_index()
        if current_layer == target_layer:
            return current_layer

        for i,sorting_layer in enumerate(self.__sorting_layers):
            if i == target_layer:
                sorting_layer.append(game_object)
            if i == current_layer:
                sorting_layer.remove(game_object)

        return target_layer

    def get_pause_state(self):
        """
        Retorna se o jogo esta pausado ou nao
        """
        return self.__pause_game

    def get_event_system(self) -> EventSystem:
        """
        retorna o sistema de eventos principal
        """
        return self.__event_system

    def get_keyboard_manager(self) -> KeyboardManager:
        """
        Retorna o sistema responsavel pelo teclado
        """
        return self.__keyboard

    def get_mouse(self) -> MouseManager:
        """
        Retorna o sistema responsavel pelo mouse
        """
        return self.__mouse

    def get_img_loader(self) -> ImageLoader:
        """
        Retorna o sistema responsavel pelo carregamento de imagens
        """
        return self.__img_loader

    def get_sound_manager(self) -> SoundManager:
        """
        Retorna o sistema responsavel pelos sons do jogo
        """
        return self.__sound_manager

    def get_display(self):
        """
        retorna o display principal da aplicação
        """
        return self.__application_display

    def get_render_interpolation(self):
        """
        Retorna a interpolação atual que foi calculada
        """
        return self.__render_interpolation

    def get_meter(self):
        """
        Retorna a grandeza que representa o metro
        """
        return self.__meter

    def get_frame_rate(self):
        """
        Retorna o frame rate lógico da aplicação
        """
        return self.__logic_frame_rate

    def get_physic_manager(self):
        """
        Retorna o sistema responsavel pela fisica
        """
        return self.__physic

    def enqueue_method(self, method, frames):
        """
        Armazena um método para ser executado após o número especificado de frames
        """
        self.__queued_methods.append((method, self.__current_frame, frames))

    def execute_queued_methods(self):
        """
        Executa os métodos armazenados
        """
        for queued_method in self.__queued_methods:
            if self.__current_frame - queued_method[1] >= queued_method[2]:
                queued_method[0]()
                self.__queued_methods.remove(queued_method)

    def __update(self):
        """
        Executa o método update de todos os GameObjects registrados
        """
        if time.time() - self.__last_update_timestamp >= self.__logic_frame_duration and not self.__pause_game:
            self.__current_frame += 1
            self.__last_update_timestamp = time.time()
            self.__event_system.fire_event_one_shot("LogicFrameStart")
            self.execute_queued_methods()
            for game_object in self.__game_objects:
                if game_object.get_state():
                    game_object.update()
            self.__physic.physic_step()

    def __draw(self):
        """
        Execute o método draw de todos os GameObjects registrados
        e executa o método async_update de todos os GameObjects
        """


        self.__render_interpolation = ((time.time() - self.__last_update_timestamp)
        / self.__logic_frame_duration)
        if self.__pause_game:
            self.__render_interpolation = 0

        self.__application_display.fill((0, 0, 0))
        if not self.__pause_game:
            for game_object in self.__game_objects:
                game_object.async_update()
            for sorting_layer in self.__sorting_layers[::-1]:
                for game_object in sorting_layer:
                    if game_object.get_state():
                        game_object.draw()
        else:
            self.__pause_text.draw()

        pygame.display.flip()

    def run(self):
        """
        Inicia o loop principal da aplicação
        """
        mouse_event_params = dict()
        mouse_event_params['position'] = Vector2()

        while self.__run_game:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.__run_game = False
                elif event.type == pygame.KEYDOWN:
                    self.__keyboard.set_key_state(event.key, True)
                    self.__event_system.fire_event("{}keydown".format(event.key))
                    if event.key == pygame.K_ESCAPE:
                        self.__pause_game = not self.__pause_game
                        self.__sound_manager.play_sound('pause', 1.0)
                    if event.key == pygame.K_q and self.__pause_game:
                        self.__run_game = False
                elif event.type == pygame.KEYUP:
                    self.__keyboard.set_key_state(event.key, False)
                    self.__event_system.fire_event("{}keyup".format(event.key))
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mouse_event_params['position'] = self.__mouse.get_mouse_position()
                    self.__event_system.fire_event("{}clickdown".format(event.button),mouse_event_params)
                elif event.type == pygame.MOUSEBUTTONUP:
                    self.__event_system.fire_event("{}clickup".format(event.button))

            self.__update()
            self.__draw()
