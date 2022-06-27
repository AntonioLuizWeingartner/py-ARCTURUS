"""
Esse módulo contem a definição das classes mais importantes da aplicação
"""

from __future__ import annotations
import os
import time
from typing import Callable, Type, List, Tuple
import math
from abc import ABC
import pygame
from pygame.math import Vector2
from pygame import gfxdraw
from engine.core.utilities import cast_to_int_vector, angle_interpolation, scaled_vector, is_point_inside_rect
from pathlib import Path

class Object(ABC):
    """
    Essa classe representa o objeto base da aplicação.
    """

    __NextID = 0

    def __init__(self):
        self.__object_id = Object.__NextID
        self.__name = "Object" + str(self.__object_id)
        Object.__NextID += 1

    def get_id(self):
        """
        Esse método retorna o id do objeto
        """
        return self.__object_id

    def get_name(self) -> str:
        """
        Esse método retorna o nome do objeto
        """
        return self.__name

    def set_name(self, name: str):
        """
        Esse método seta o nome do objeto
        """
        self.__name = name

class Component(Object):
    """
    Essa classe abstrata representa o conceito de componente de um GameObject.
    Componentes compõe um GameObject. Eles são responsáveis por definir
    o comportamento e o estado de um GameObject.
    """

    def __init__(self):
        super().__init__()
        self.__owner = None
        self.__active = True

    def __repr__(self):
        return_str = "----------------------------------------------------------------\n"
        return_str += "Component class:\t{}\n".format(type(self))
        return_str += "Component id: \t\t{}\n".format(self.get_id())
        return_str += "Component name: \t{}\n".format(self.get_name())
        return_str += "Owner id: \t\t{}\n".format(self.get_owner().get_id())
        return return_str

    def set_owner(self, owner: GameObject):
        """
        Seta o dono desse GameObject
        """
        self.__owner = owner

    def get_owner(self):
        """
        Retorna o dono desse GameObject
        """
        return self.__owner

    def disable(self):
        """
        Desativa o componente
        """
        if self.__active:
            self.__active = False
            self.on_disable()

    def enable(self):
        """
        Ativa o componente
        """
        if not self.__active:
            self.__active = True
            self.on_enable()

    def on_component_creation(self):
        """
        Este método é chamado sempre que o componente é adicionado
        a algum GameObject
        """

    def on_component_removal(self):
        """
        Este método é chamado momentos antes de o objeto ser deletado.
        """

    def on_enable(self):
        """
        Este método é chamado sempre que o componente sofre a transição
        do estado desativo para ativado
        """

    def on_disable(self):
        """
        Este método é chamado sempre que o componente sofre a transição
        do estado ativado para desativado
        """


class LogicComponent(Component):
    """
    Essa classe representa componentes que executam algum tipo de ação.
    Esse componente tambem pode ser utilizado para armazenar informações.
    """

    def update(self):
        """
        A lógica do componente deve ser impletada aqui.
        Esta função é chamada 1 vez por frame lógico.
        """

    def async_update(self):
        """
        Função que é a chamada a cada loop da aplicação
        """
 
    def on_collision_enter(self, other: "Collider", contact_point: Vector2, relative_velocity: Vector2):
        """
        Função chamada quando uma colisão for detectada
        """

class Rigidbody(LogicComponent):
    """
    Este componente define o conceito de corpo rigido para esta aplicação
    Corpos rigidos não sofrem deformações e possuem densidade uniforme
    """

    def __init__(self):
        super().__init__()
        self.velocity = Vector2()
        self.angular_velocity = 0.0
        self.linear_drag = 0.0
        self.angular_drag = 0.0
        self.mass = 50

    def update(self):
        self.velocity -= self.velocity*self.linear_drag
        self.angular_velocity -= self.angular_velocity*self.angular_drag
        self.get_owner().get_transform().position += self.velocity
        self.get_owner().get_transform().rotation += self.angular_velocity

class RenderComponent(Component):
    """
    Herde esta classe se seu componente irá realizar alguma operação relacionada à gráficos
    """
    def __init__(self):
        self.rigid_body = None
        super().__init__()  
        self.__sorting_layer_index = 0

    def get_sorting_layer_index(self) -> int:
        """
        Retorna o indice da sorting layer atual
        """
        return self.__sorting_layer_index

    def set_sorting_layer_index(self, index: int):
        """
        Altera a layer do componente para a camada escolhida
        """
        self.__sorting_layer_index = self.get_owner().change_component_sorting_layer(self, index)

    def get_draw_position(self):
        """
        Essa função calcula a posição que o objeto sera desenhado
        Se ele tiver um corpo rigido associado a ele, sera levado em conta
        a velocidade do objeto.
        """

        if self.rigid_body is None:
            self.rigid_body = self.get_owner().get_component(Rigidbody)
            if self.rigid_body is None:
                return self.get_owner().get_transform().position

        draw_position = self.rigid_body.velocity*self.get_owner().get_application().get_render_interpolation()
        draw_position += self.get_owner().get_transform().position
        return draw_position

    def get_draw_rotation(self):
        """
        Essa função retorna a rotação que sera utilizada para desenhar o objeto
        """
        if self.rigid_body is None:
            self.rigid_body = self.get_owner().get_component(Rigidbody)
            if self.rigid_body is None:
                return self.get_owner().get_transform().rotation
        return angle_interpolation(self.get_owner().get_transform().rotation, 
        self.get_owner().get_transform().rotation+self.rigid_body.angular_velocity,
        self.get_owner().get_application().get_render_interpolation())

    def draw(self):
        """
        O código de desenho do componente deve ser implementado aqui
        """
        raise NotImplementedError()

class DataComponent(Component):
    """
    Herde esta classe se seu componente apenas ira armazenar dados
    """

class Transform(DataComponent):
    """
    Este componente representa a posição e orientação do GameObject em questão
    """
    def __init__(self):
        super().__init__()
        self.position = Vector2()
        self.rotation = 0.0
        self.scale = Vector2(1, 1)

    def get_forward_vector(self):
        """
        Retorna o vetor que aponta para frente na perspectiva do objeto
        """
        return Vector2(math.cos(self.rotation+math.pi/2), -math.sin(self.rotation+math.pi/2))

    def get_right_vector(self):
        """
        Retorna o vetor que aponta para a direita na perspectiva do objeto
        """
        return Vector2(math.cos(self.rotation), -math.sin(self.rotation))


class CircleRenderer(RenderComponent):

    """
    Este componente desenha um circulo na tela com base na posição
    atual do GameObject que é dono deste componente
    """

    def __init__(self):
        super().__init__()
        self.__radius = 20
        self.__color = (255, 255, 255)

    def draw(self):
        draw_pos = self.get_draw_position()
        gfxdraw.aacircle(self.get_owner().get_application().get_display(),
        int(draw_pos[0]), int(draw_pos[1]), self.__radius, self.__color)
        gfxdraw.filled_circle(self.get_owner().get_application().get_display(),
        int(draw_pos[0]), int(draw_pos[1]), self.__radius, self.__color)

    def set_radius(self, radius: float):
        """
        Seta o raio do circulo
        """
        self.__radius = radius

    def set_color(self, color: Tuple[int, int, int]):
        """
        Seta a cor do circulo
        """
        self.__color = color

    def get_radius(self) -> float:
        """
        Retorna o raio do circulo
        """
        return self.__radius


class BackgroundRenderer(RenderComponent):
    
    """
    Este componente é responsavel por desenhar o plano de fundo
    """

    def __init__(self):
        super().__init__()
        self.__sprite = None
        self.__sprite_identifier = 'default'
        self.__display = None
        self.__img_loader = None

    def on_component_creation(self):
        self.__display = self.get_owner().get_application().get_display()
        self.__img_loader = self.get_owner().get_application().get_img_loader()
        self.__sprite = self.__img_loader.get_image(self.__sprite_identifier)
        self.fit_to_screen()

    def fit_to_screen(self):
        """
        Esse método faz a imagem ocupar a tela inteira
        """
        new_size = (self.__display.get_width(), self.__display.get_height())
        self.__sprite = pygame.transform.scale(self.__sprite, new_size)
        self.__sprite = self.__sprite.convert()

    def set_new_sprite(self, identifier: str):
        """
        Altera a imagem que sera renderizada no plano de fundo
        """
        self.__sprite = self.__img_loader.get_image(identifier)
        self.__sprite_identifier = identifier
        self.fit_to_screen()

    def draw(self):
        self.__display.blit(self.__sprite, (0,0))



class MouseFollower(LogicComponent):
    """
    Este componente é responsavel por alterar a posicao do game object para a posicao do mouse a cada frame
    """
    def async_update(self):
        self.get_owner().get_transform().position = self.get_owner().get_application().get_mouse().get_mouse_position()


class ImageLoader(Object):

    """
    Esta classe é responsável por carregar imagens
    """

    def __init__(self):
        super().__init__()
        self.__loaded_images = dict()
        
        self.load_new_image('default.png','default')

    def load_new_image(self, image_name: str, identifier: str):
        """
        Esse método carrega uma nova imagem e o associa ao identificador
        que foi passado para o método
        """
        path = os.path.join(os.getcwd(), "assets", "images", image_name)
        self.__loaded_images[identifier] = pygame.image.load(str(path))

    def get_image(self, identifier: str):
        """
        Retorna uma imagem que foi previamente carregada
        """
        return self.__loaded_images[identifier]

    def create_sprite_sequence(self, identifier: str):
        """
        Cria uma lista de sprites para ser usada em animacao
        """
        self.__loaded_images[identifier] = list()

    def load_image_to_sprite_sequence(self, image_name: str, sequence_identifier):
        """
        Carrega uma imagem para a sequencia desejada
        """
        path = os.path.join(os.getcwd(), "assets", "images", image_name)
        image = pygame.image.load(path)        
        self.__loaded_images[sequence_identifier].append(image.convert_alpha())

    def get_sprite_sequence(self, identifier: str):
        """
        Retorna a sequencia de sprites desejada
        """
        return self.__loaded_images[identifier]

class SoundManager(Object):

    """
    Esta classe é responsavel por carregar e tocar sons
    """

    def __init__(self):
        super().__init__()
        self.__loaded_sounds = dict()

    def load_new_sound(self, sound_name: str, identifier: str):
        """
        Esse método carrega um som a partir de um arquivo e o associa a um identificador
        """
        path = os.path.join(os.getcwd(), "assets", "sounds", sound_name);
        self.__loaded_sounds[identifier] = pygame.mixer.Sound(path)

    def play_sound(self, identifier, volume):
        """
        Esse método toca um som usando o seu identificador e com o volume fornecido
        """
        self.__loaded_sounds[identifier].set_volume(volume)
        self.__loaded_sounds[identifier].play()

class SpriteRenderer(RenderComponent):

    """
    Este componente desenha imagens na tela
    """

    def __init__(self):
        super().__init__()
        self.sprite = None
        self.sprite_half_size = None
        self.__sprite_identifier = None
        self.current_scale = None

    def on_component_creation(self):
        self.set_new_sprite('default')
    def get_dimensions(self) -> Vector2:
        """
        Retorna as dimensões do sprite atual
        """
        img_loader = self.get_owner().get_application().get_img_loader()
        default_sprite = img_loader.get_image(self.__sprite_identifier)
        return Vector2(default_sprite.get_width(), default_sprite.get_height())


    def get_original_sprite(self):
        """
        Retorna o sprite original, sem transformações aplicadas a ele
        """
        img_loader = self.get_owner().get_application().get_img_loader()
        return img_loader.get_image(self.__sprite_identifier)

    def set_new_sprite(self, image_identifier: str):
        """
        Esse método altera o sprite que sera desenhado por este componente
        """
        self.__sprite_identifier = image_identifier
        self.set_sprite_scale_in_meters(1)
        
    def set_sprite_scale(self, scale_vector: Vector2):
        """
        Este método redimensiona o sprite para o tamanho desejado
        """
        self.sprite = pygame.transform.scale(self.sprite, (int(self.sprite.get_width()*scale_vector.x),
        int(self.sprite.get_height()*scale_vector.y)))
        self.sprite_half_size = Vector2(self.sprite.get_width(),self.sprite.get_height())*0.5

    def set_sprite_scale_in_meters(self, scale_factor):
        """
        Redimensiona o sprite com base no metro
        """
        dimensions = self.get_dimensions()
        scale = dimensions.x/self.get_owner().get_application().get_meter()
        self.sprite = pygame.transform.scale(self.get_original_sprite(), (int(scale_factor*dimensions.x/scale),
        int(scale_factor*dimensions.y/scale)))
        self.sprite_half_size = Vector2(self.sprite.get_width(),self.sprite.get_height())*0.5

    def draw(self):
        rotated_image = pygame.transform.rotate(self.sprite, self.get_draw_rotation()*(180/math.pi))
        half_size = Vector2(rotated_image.get_width(), rotated_image.get_height())*0.5
        self.get_owner().get_application().get_display().blit(rotated_image,
        self.get_owner().get_transform().position - half_size)

class TextRenderer(RenderComponent):
    """
    Esta classe é utilizada para renderizar texto
    """

    def __init__(self):
        super().__init__()
        self.__text_surface = None
        self.__text = None
        self.__screen_width = 0
        self.__screen_height = 0
        self.__font = None
        self.__font_color = (255, 255, 255)
        self.__transform = None
        self.__display = None
        self.__half_dimensions = Vector2()
        self.__background_color = None

    def on_component_creation(self):
        self.__screen_width = self.get_owner().get_application().get_display().get_width()
        self.__screen_height = self.get_owner().get_application().get_display().get_height()
        self.__transform = self.get_owner().get_transform()
        self.__display = self.get_owner().get_application().get_display()
        self.set_font('Arial', 2)
        self.set_text('default')


    def get_rect_points(self):
        """
        Retorna os extremos do retangulo que emcobre o texto
        """
        top_left = self.__transform.position - self.__half_dimensions*2
        bottom_right = self.__transform.position + self.__half_dimensions
        return (top_left, bottom_right)


    def set_text(self, text: str):
        """
        Essa função altera o texto que sera exibido na tela
        """
        self.__text = text
        self.__text_surface = self.__font.render(self.__text, True, self.__font_color, self.__background_color)
        self.__half_dimensions.x = self.__text_surface.get_width()/2
        self.__half_dimensions.y = self.__text_surface.get_height()/2

    def calculate_draw_pos(self):
        """
        Calcula uma posição de forma que a surface do texto fique centralizada na posição do game object
        """
        return self.__transform.position - self.__half_dimensions

    def set_font(self, font_name: str, font_size: float):
        """
        Seleciona uma fonte especifica com um tamanho definido
        """
        self.__font = pygame.font.SysFont(font_name, int(font_size*self.__screen_width/100))

    def set_font_color(self, font_color):
        """
        Altera a cor da fonte
        """
        self.__font_color = font_color

    def set_background_color(self, background_color):
        """
        Altera a cor de fundo
        """
        self.__background_color = background_color

    def draw(self):
        self.__display.blit(self.__text_surface, self.calculate_draw_pos())


class Button(LogicComponent):

    """
    Essa classe representa um botão que é clicavel, deve ser utilizado em conjunto em com text renderer
    """

    def __init__(self):
        super().__init__()
        self.__event_name = 'button_clicked'
        self.__evt_sys = None
        self.__text_renderer = None
        self.__sound_identifier = 'button'
    
    def on_component_creation(self):
        self.__evt_sys = self.get_owner().get_application().get_event_system()
        self.__text_renderer = self.get_owner().get_component(TextRenderer)
        self.__evt_sys.register_event_callback('1clickdown', self.check_mouse_click)
    
    def set_sound_identifier(self, identifier: str):
        self.__sound_identifier = identifier

    def set_event_name(self, event_name):
        """
        Seta o nome do evento que sera disparado quando esse botem for clicado
        """
        self.__event_name = event_name

    def check_mouse_click(self, callback_params):
        """
        Este método é executado sempre que o mouse for pressionado.
        Se o ponto onde o usuario clicou for um botão, um evento
        com o nome definido em self.__event_name sera disparado
        """
        rect_points = self.__text_renderer.get_rect_points()
        if is_point_inside_rect(callback_params['position'], rect_points[0], rect_points[1]):
            self.__evt_sys.fire_event(self.__event_name)
            self.get_owner().get_application().get_sound_manager().play_sound(self.__sound_identifier, 1.0)


class AnimatedSprite(SpriteRenderer):

    def __init__(self):
        super().__init__()
        self.__sprite_scale = None
        self.__current_sprite = None
        self.__sprite_sequence = None
        self.__frame_duration = 1/60
        self.__next_frame_time = 0
        self.__i = 0
        self.__j = 0

    def set_sprite_sequence(self, sprite_list):
        self.__sprite_sequence = sprite_list
        self.__sprite_scale = Vector2(1,1)
    
    def draw(self):
        
        if time.time() >= self.__next_frame_time and not self.get_owner().get_application().get_pause_state():
            self.__next_frame_time = time.time() + self.__frame_duration
            self.__i += 1
            if self.__i == len(self.__sprite_sequence):
                self.__i = 0
                self.__j += 1

        half_size = Vector2(self.__sprite_sequence[self.__i].get_width(), self.__sprite_sequence[self.__i].get_height())*0.5
        self.get_owner().get_application().get_display().blit(self.__sprite_sequence[self.__i],
        self.get_owner().get_transform().position - half_size)

class ShipController(LogicComponent):

    """
    Este componente representa os controles de uma nave
    """

    def __init__(self):
        super().__init__()
        self.__ship_rigid_body = None
        self.__ship_cursor_transform = None
        self.__ship_transform = None
        self.__keyboard_reference = None
        self.__sound_manager = None
        self.__display_size = None
        self.__evt_sys = None

    def enforce_bounds(self):
        pos = self.get_owner().get_transform().position

        if pos.x < 0 or pos.x > self.__display_size.x or pos.y < 0 or pos.y > self.__display_size.y:
            vel = ((self.__display_size/2) - pos)
            vel.normalize_ip()
            self.__ship_rigid_body.velocity += vel

    def set_ship_cursor_transform(self, transform: Transform):
        """
        Seta o Transform do cursor que sera responsavel por guiar a nave
        """
        self.__ship_cursor_transform = transform
        self.__ship_transform = self.get_owner().get_transform()
        self.__keyboard_reference = self.get_owner().get_application().get_keyboard_manager()
       

    def on_component_creation(self):
        self.__ship_rigid_body = self.get_owner().get_component(Rigidbody)
        self.__sound_manager = self.get_owner().get_application().get_sound_manager()
        disp = self.get_owner().get_application().get_display()
        self.__display_size = Vector2(disp.get_width(), disp.get_height())
        self.__evt_sys = self.get_owner().get_application().get_event_system()

    def rotate_to_cursor_position(self):
        """
        Rotaciona o game_object para apontar para o cursor
        """
        delta = self.__ship_cursor_transform.position - self.__ship_transform.position
        target_angle = math.atan2(delta[1], delta[0])
        self.__ship_transform.rotation = (-target_angle - math.pi/2)

    def calculate_velocity(self):
        """
        Calcula a velocidade que sera aplicada a nave com base nas teclas pressionadas
        """
        velocity = Vector2()

        if self.__keyboard_reference.get_key(119):
            velocity += scaled_vector(self.__ship_transform.get_forward_vector()*0.6)

        self.__ship_rigid_body.velocity += scaled_vector(velocity)

    def update(self):
        self.rotate_to_cursor_position()
        self.calculate_velocity()
        self.enforce_bounds()
    
    def on_collision_enter(self, other, contact_point, relative_velocity):
        self.__sound_manager.play_sound('big_explosion', 0.1)
        self.explode()

    def explode(self):
        """
        Gerar explosao aqui
        """
        params = dict()
        params['position'] = self.get_owner().get_transform().position
        self.get_owner().get_application().get_event_system().fire_event('CometExplosion', params)
        self.get_owner().get_application().remove_game_object(self.get_owner())
        self.__evt_sys.fire_event('GameOver')

class GameObject(Object):

    """
    Esta classe representa todos os objetos pertinentes ao jogo.
    O comportamento e o estado dos GameObjects são definidos pelos componentes
    que são adicionados ao GameObject.
    """
    
    def __init__(self):
        super().__init__()
        self.__logic_components = list()
        self.__render_components = list()
        self.__data_components = list()
        self.__active = True
        self.__application = None
        self.__transform = self.add_component(Transform)
        self.__sorting_layers: List[List[RenderComponent]] = list()
        
        self.__game_object_sorting_layer_index = 0

        for i in range(32):
            self.__sorting_layers.append(list())


    def __repr__(self):
        return_str = "____________GameObject Info____________\n"
        return_str += "GameObject id: \t\t\t{}\n".format(self.get_id())
        return_str += "GameObject name: \t\t{}\n".format(self.get_name())
        return_str += "GameObject state: \t\t{}\n".format(str(self.get_state()))
        return_str += "Logic component count: \t\t{}\n".format(len(self.__logic_components))
        return_str += "Render component count: \t{}\n".format(len(self.__render_components))
        return_str += "Data component count: \t\t{}\n".format(len(self.__data_components))
        return_str += "____________Components details____________\n"
        for component in self.__logic_components:
            return_str += component.__repr__()
        for component in self.__render_components:
            return_str += component.__repr__()
        for component in self.__data_components:
            return_str += component.__repr__()

        return return_str

    def get_sorting_layer_index(self) -> int:
        """
        Esse método retorna a sorting layer do game object
        """
        return self.__game_object_sorting_layer_index

    def set_sorting_layer_index(self, index: int):
        """
        Esse método altera a sorting layer do game object
        """
        self.__game_object_sorting_layer_index = self.get_application().change_game_object_sorting_layer(self, index)

    def set_application(self, application: "Application"):
        """
        seta o objeto que representa a aplicacao
        """
        self.__application = application

    def get_application(self) -> "Application":
        """
        Retorna o objeto que representa a aplicacao
        """
        return self.__application

    def get_transform(self) -> Transform:
        """
        Retorna o componente Transform associado a esse objeto
        """
        return self.__transform

    def change_component_sorting_layer(self, component: RenderComponent, target_layer: int) -> int:
        """
        Altera a sorting layer de um componente especifico
        """
        current_layer = component.get_sorting_layer_index()
        if current_layer == target_layer:
            return current_layer

        for i,sorting_layer in enumerate(self.__sorting_layers):
            if i == target_layer:
                sorting_layer.append(component)
            if i == current_layer:
                sorting_layer.remove(component)

        return target_layer

    def broadcast_collision_to_components(self, other: "Collider", point: Vector2, relative_velocity: Vector2):
        """
        Este método chama a função "on_collision_enter" de todos os componentes lógicos assim que uma colisão
        for detectada envolvendo esse GameObject
        """
        try:
            for logic_component in self.__logic_components:
                logic_component.on_collision_enter(other, point, relative_velocity)
        except AttributeError:
            return
    def update(self):
        """
        Executa a função update de todos os componentes lógicos de forma sequencial
        """
        for component in self.__logic_components:
            component.update()

    def async_update(self):
        """
        Execute a função async_update de todos os componentes lógicos de forma sequencia,kl
        """
        for component in self.__logic_components:
            component.async_update()

    def draw(self):
        """
        Executa a função draw de todos os componentes gráficos de forma sequencial
        """
        for sorting_layer in self.__sorting_layers[::-1]:
            for component in sorting_layer:
                component.draw()

    def toggle_state(self):
        """
        Altera o estado do objeto para o estado oposto
        """
        self.__active = not self.__active

    def set_state(self, state: bool):
        """
        Seta o estado do objeto para o valor especificado
        """
        self.__active = state

    def get_state(self) -> bool:
        """
        Retorna o estado do objeto
        """
        return self.__active

    def add_component(self, component_constructor: Callable[[], Component]) -> Component:
        """
        Constroi um componente com base no construtor fornecido,
        adiciona o componente construido ao GameObject e retorna
        o componente.
        """
        new_component = component_constructor()
        new_component.set_owner(self)
        new_component.on_component_creation()

        if issubclass(type(new_component), LogicComponent):
            self.__logic_components.append(new_component)
        elif issubclass(type(new_component), RenderComponent):
            self.__render_components.append(new_component)
            self.__sorting_layers[0].append(new_component)
        elif issubclass(type(new_component), DataComponent):
            self.__data_components.append(new_component)
        else:
            raise Exception("Objetos do tipo {} não".format(type(new_component)) +
        "são componentes válidos e não podem ser adicionados a um GameObject")
        return new_component

    def __get_search_space(self, component_class:Type) -> List[Component]:
        """
        Função auxiliar que retorna uma lista com base no tipo do componente
        """
        search_space: List[Component] = None
        if issubclass(component_class, LogicComponent):
            search_space = self.__logic_components
        elif issubclass(component_class, RenderComponent):
            search_space = self.__render_components
        elif issubclass(component_class, DataComponent):
            search_space = self.__data_components
        else:
            raise Exception("Objeto do tipo {} não é um componente valido!".format(component_class))

        return search_space

    def get_component(self, component_class: Type, component_id: int=None) -> Component:
        """
        Retorna um componente especificando seu tipo
        component_id é um parametro opcional,
        quando for diferente de None a busca sera feita pelo id
        """
        search_space: List[Component] = self.__get_search_space(component_class)

        for component in search_space:
            if component_id is not None:
                if component.get_id() == component_id:
                    return component
            else:
                if isinstance(component, component_class):
                    return component

    def remove_component(self, component_class: Type, component_id: int=None):
        """
        Remove e destrói um componente especificando o seu tipo.
        Se o id for diferente de None a busca sera realizada pelo id.
        """
        search_space: List[Component] = self.__get_search_space(component_class)

        def delete_component(component: Component):
            search_space.remove(component)
            if issubclass(type(component), RenderComponent):
                layer = component.get_sorting_layer_index()
                self.__sorting_layers[layer].remove(component)
            component.on_component_removal()
            del component

        for component in search_space:
            if component_id is not None:
                if component.get_id() == component_id:
                    delete_component(component)
                    return
            else:
                if isinstance(component, component_class):
                    delete_component(component)
                    return

    def destroy(self):
        """
        Essa função destroi todos os componentes deste GameObject
        """
        for cp in self.__logic_components:
            cp.on_component_removal()
        
        for cp in self.__render_components:
            cp.on_component_removal()

        for cp in self.__data_components:
            cp.on_component_removal()

        del self.__logic_components
        del self.__render_components
        del self.__data_components