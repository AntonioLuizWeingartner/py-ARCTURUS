import time
import pygame
from typing import Tuple
from pygame.math import Vector2
from engine.core.objects import LogicComponent, GameObject, Rigidbody, CircleRenderer, RenderComponent
from engine.core.physics import Collider, CircleCollider
from engine.game.asteroid import AsteroidScript
from engine.core.utilities import scale_number_with_meter, scaled_number


class BulletFactory(LogicComponent):
    """
    Esta classe é responsavel por criar GameObjects que se comportam como projéteis
    """
    def __init__(self):
        super().__init__()
        self.__app = None

    def on_component_creation(self):
        self.__app = self.get_owner().get_application()

    def get_new_object(self, radius_in_meters: float, initial_velocity: Vector2, initial_position: Vector2,color: Tuple[int, int, int] = (0, 255, 0)) -> GameObject:
        """
        Retorna um novo projétil
        """

        bullet = self.__app.add_game_object()
        bullet.get_transform().position = initial_position
        rb = bullet.add_component(Rigidbody)
        rb.mass = 0.000001
        rb.velocity = initial_velocity
        cr = bullet.add_component(CircleRenderer)
        cr.set_radius(int(scale_number_with_meter(radius_in_meters)))
        cr.set_color(color)
        cc = bullet.add_component(CircleCollider)
        cc.radius = scale_number_with_meter(radius_in_meters)
        bullet.add_component(BulletScript)
        return bullet

class BulletScript(LogicComponent):
    """
    Esta classe define o comportamento de um projétil
    """

    def __init__(self):
        super().__init__()
        self.__physic_system = None

    def on_component_creation(self):
        self.__physic_system = self.get_owner().get_application().get_physic_manager()
        self.get_owner().get_application().enqueue_method(self.delete, 250)

    def delete(self):
        """
        Remove o objeto do jogo
        """
        self.get_owner().get_application().remove_game_object(self.get_owner())

    def on_collision_enter(self, other: Collider, contact_point: Vector2, relative_velocity: float):
        evt_sys = self.get_owner().get_application().get_event_system()
        asteroid_script = other.get_owner().get_component(AsteroidScript)
        if asteroid_script is not None:
            asteroid_script.explode()
            evt_sys.register_event_callback_one_shot("LogicFrameStart", lambda params: asteroid_script.explode())
        evt_sys.register_event_callback_one_shot("LogicFrameStart", self.self_destroy)

    def self_destroy(self, callback_params):
        self.__physic_system.remove_collider(self.get_owner().get_component(CircleCollider))
        self.get_owner().get_application().remove_game_object(self.get_owner())


class Weapon(LogicComponent):
    """
    Esta classe permite que a nave dispare projéteis
    """
    def __init__(self):
        super().__init__()
        self.__keyboard = None
        self.__bullet_factory = None
        self.__bullet_delay = 0.333333333333333333
        self.__next_bullet_time = 0
        self.__sound_manager = None

    def on_component_creation(self):
        self.__keyboard = self.get_owner().get_application().get_mouse()
        self.__bullet_factory = self.get_owner().get_component(BulletFactory)
        self.__sound_manager = self.get_owner().get_application().get_sound_manager()
        
    def update(self):
        if self.__keyboard.get_mouse_key_state(0) and time.time() >= self.__next_bullet_time:
            self.__sound_manager.play_sound('plasma_shot',0.5)
            self.__next_bullet_time = time.time() + self.__bullet_delay
            fwd_vec = self.get_owner().get_transform().get_forward_vector()
            initial_velocity = self.get_owner().get_transform().get_forward_vector()*scaled_number(80)
            initial_position = self.get_owner().get_transform().position + fwd_vec*scale_number_with_meter(1)
            self.__bullet_factory.get_new_object(0.2, initial_velocity, initial_position)
            