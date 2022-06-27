import time
from pygame.math import Vector2
from engine.core.objects import SpriteRenderer, Rigidbody, Transform, LogicComponent, GameObject, AnimatedSprite
from engine.core.physics import CircleCollider
from engine.core.utilities import scaled_vector, scaled_number
import random

class AsteroidManagerScript(LogicComponent):
    """
    Esta classe é responsável por gerenciar os asteroids do jogo
    """
    def __init__(self):
        super().__init__()
        self.__asteroid_list = list()

    def get_asteroid_count(self):
        return len(self.__asteroid_list)

    def instantiate_asteroid(self, size_in_meters: float, initial_position: Vector2, initial_velocity: Vector2):
        """
        Cria uma novo asteroid
        """
        app = self.get_owner().get_application()
        asteroid_game_object = app.add_game_object()
        asteroid_game_object.set_sorting_layer_index(1)
        asteroid_game_object.get_transform().position = initial_position
        asteroid_rigid_body = asteroid_game_object.add_component(Rigidbody)
        asteroid_rigid_body.velocity = scaled_vector(initial_velocity)
        asteroid_rigid_body.mass = size_in_meters
        asteroid_rigid_body.angular_velocity = random.random()/60
        asteroid_sprite_renderer = asteroid_game_object.add_component(SpriteRenderer)
        asteroid_sprite_renderer.set_new_sprite('asteroid')
        asteroid_sprite_renderer.set_sprite_scale_in_meters(size_in_meters)
        radius = asteroid_sprite_renderer.sprite.get_width()/2
        asteroid_collider = asteroid_game_object.add_component(CircleCollider)
        asteroid_collider.radius = radius
        script = asteroid_game_object.add_component(AsteroidScript)
        script.asteroid_manager = self
        self.__asteroid_list.append(asteroid_game_object)

    def remove_asteroid(self, asteroid: GameObject):
        """
        Remove um asteroid especifico
        """
        self.__asteroid_list.remove(asteroid)
        self.get_owner().get_application().remove_game_object(asteroid)

    def remove_all_asteroids(self):
        """
        Remove todos os asteroids
        """
        id_list = [gm.get_id() for gm in self.__asteroid_list]

        for gm_id in id_list:
            self.get_owner().get_application().remove_game_object_by_id(gm_id)
        self.__asteroid_list.clear()

class AsteroidScript(LogicComponent):
    """
    Este componente define o comportamento de um asteroid
    """
    def __init__(self):
        super().__init__()
        self.transform = None
        self.circle_collider = None
        self.screen_width = None
        self.screen_height = None
        self.asteroid_manager = None
        self.__sound_manager = None
        self.__evt_system = None
        self.__rb = None

    def on_component_creation(self):
        self.transform = self.get_owner().get_transform()
        self.circle_collider = self.get_owner().get_component(CircleCollider)
        self.screen_width = self.get_owner().get_application().get_display().get_width()
        self.screen_height = self.get_owner().get_application().get_display().get_height()
        self.asteroid_manager = self.get_owner().get_component(AsteroidManagerScript)
        self.__sound_manager = self.get_owner().get_application().get_sound_manager()
        self.__evt_system = self.get_owner().get_application().get_event_system()
        self.__rb = self.get_owner().get_component(Rigidbody)
    
    def on_component_removal(self):
        self.asteroid_manager.remove_asteroid(self.get_owner())

    def update(self):
        if self.transform.position.x > self.screen_width + self.circle_collider.radius:
            self.transform.position.x = -self.circle_collider.radius
        elif self.transform.position.x < -self.circle_collider.radius:
            self.transform.position.x = self.screen_width + self.circle_collider.radius

        if self.transform.position.y < -self.circle_collider.radius:
            self.transform.position.y = self.screen_height + self.circle_collider.radius
        elif self.transform.position.y > self.screen_height + self.circle_collider.radius:
            self.transform.position.y = -self.circle_collider.radius

    def explode(self):
        """
        Explode o asteroid
        """
        self.__sound_manager.play_sound('comet_explosion', 1)
        params = dict()
        params['position'] = self.get_owner().get_transform().position
        params['score'] = 100*self.__rb.velocity.magnitude()/self.__rb.mass
        self.__evt_system.fire_event('CometExplosion', params)
        self.get_owner().get_application().remove_game_object(self.get_owner())


class ExplosionManager(LogicComponent):
    
    def create_explosion_at(self, params):
        explosion_gm = self.get_owner().get_application().add_game_object()
        explosion_gm.add_component(ExplosionScript)
        animated_sprite = explosion_gm.add_component(AnimatedSprite)
        animated_sprite.set_sprite_sequence(self.get_owner().get_application().get_img_loader().get_sprite_sequence('explosion'))
        explosion_gm.get_transform().position = params['position']
    
    def on_component_creation(self):   
        evt_sys = self.get_owner().get_application().get_event_system()
        evt_sys.register_event_callback('CometExplosion',self.create_explosion_at)

class ExplosionScript(LogicComponent):
    
    """
    Esta classe remove a explosão depois de 240 frames
    """

    def __init__(self):
        super().__init__()
        self.__death_time = time.time() + 4.2

    def on_component_creation(self):
        self.get_owner().get_application().enqueue_method(self.delete, 240)

    def delete(self):
        """
        Remove o objeto do jogo
        """
        self.get_owner().get_application().remove_game_object(self.get_owner())