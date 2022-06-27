import math
from pygame.math import Vector2
import pygame
from engine.core.objects import LogicComponent, Rigidbody, Object, SpriteRenderer
from engine.core.utilities import cast_to_int_vector, line_circle_intersection_test, scale_number_with_meter

class Collider(LogicComponent):
    """
    Todos os colisores devem herdar esta classe
    """
    def __init__(self):
        super().__init__()
        self.rigid_body = None

    def on_component_creation(self):
        self.rigid_body = self.get_owner().get_component(Rigidbody)
        self.get_owner().get_application().get_physic_manager().register_collider(self)
    def on_component_removal(self):
        self.get_owner().get_application().get_physic_manager().remove_collider(self)

class CircleCollider(Collider):
    """
    Este componente representa a forma geométrica de um circulo que pode se
    colidir com outras formas geométricas
    """


    def __init__(self):
        super().__init__()
        self.radius = 50
        self.center = None
    def update(self):
        self.center = self.get_owner().get_transform().position

    def on_component_creation(self):
        super().on_component_creation()
        self.center = self.get_owner().get_transform().position

    def on_enable(self):
        self.get_owner().get_application().get_physic_manager().register_collider(self)

    def on_disable(self):
        self.get_owner().get_application().get_physic_manager().remove_collider(self)

    def on_component_removal(self):
        self.get_owner().get_application().get_physic_manager().remove_collider(self)

#Este componente deve ser utilizado em conjunto com um SpriteRenderer
class RectCollider(Collider):
    def __init__(self):
        super().__init__()
        self.center = None
        self.width = None
        self.height = None
        self.top_left = None
        self.top_right = None
        self.bottom_right = None
        self.bottom_left = None

    def on_component_creation(self):
        super().on_component_creation()
        sprite_renderer = self.get_owner().get_component(SpriteRenderer)
        self.width = sprite_renderer.sprite.get_width()
        self.height = sprite_renderer.sprite.get_height()

    def update(self):
        fwd_vec = self.get_owner().get_transform().get_forward_vector()
        rgt_vec = self.get_owner().get_transform().get_right_vector()
        self.center = self.get_owner().get_transform().position
        self.top_left = self.center + fwd_vec*self.height/2 - rgt_vec*self.width/2
        self.top_right = self.center + fwd_vec*self.height/2 + rgt_vec*self.width/2
        self.bottom_right = self.center - fwd_vec*self.height/2 + rgt_vec*self.width/2
        self.bottom_left = self.center - fwd_vec*self.height/2 - rgt_vec*self.width/2

class PhysicManager(Object):

    """
    Esta classe processa todas as colisões do jogo
    """

    def __init__(self):
        super().__init__()
        self.__collider_list = list()

    def physic_step(self):
        """
        Essa função calcula e resolve todas as colisões a cada frame lógico
        """
        for i,collider_a in enumerate(self.__collider_list):
            for j in range(i+1, len(self.__collider_list)):
                if j == len(self.__collider_list):
                    continue
                collider_b = self.__collider_list[j]
                self.process_intersection(collider_a, collider_b)
                
    def process_intersection(self, collider_a: Collider, collider_b: Collider):
        """
        Essa função processa a intersecção e resolve a colisão para um par de colisores
        """
        if issubclass(type(collider_a), CircleCollider) and issubclass(type(collider_b), CircleCollider):
            distance_between_centers = (collider_a.center - collider_b.center).length()
            if distance_between_centers < collider_a.radius + collider_b.radius:
                
                transform_a = collider_a.get_owner().get_transform()
                transform_b = collider_b.get_owner().get_transform()

                distance_between = (collider_a.center - collider_b.center).magnitude() 

                overlap_distance = 0.5*(distance_between - collider_a.radius - collider_b.radius)
                transform_a.position.x -= overlap_distance *(collider_a.center.x - collider_b.center.x)/distance_between
                transform_a.position.y -= overlap_distance *(collider_a.center.y - collider_b.center.y)/distance_between

                transform_b.position.x += overlap_distance *(collider_a.center.x - collider_b.center.x)/distance_between
                transform_b.position.y += overlap_distance *(collider_a.center.y - collider_b.center.y)/distance_between
                collider_a.center = transform_a.position
                collider_b.center = transform_b.position

                distance_between = (collider_a.center - collider_b.center).magnitude()

                nx = (collider_b.center.x - collider_a.center.x)/distance_between
                ny = (collider_b.center.y - collider_a.center.y)/distance_between

                kx = collider_a.rigid_body.velocity.x - collider_b.rigid_body.velocity.x
                ky = collider_a.rigid_body.velocity.y - collider_b.rigid_body.velocity.y
                p = 2 * (nx*kx + ny*ky) / (collider_a.rigid_body.mass + collider_b.rigid_body.mass)
                collider_a.rigid_body.velocity.x = collider_a.rigid_body.velocity.x - p * collider_b.rigid_body.mass * nx
                collider_a.rigid_body.velocity.y = collider_a.rigid_body.velocity.y - p * collider_b.rigid_body.mass * ny
                
                collider_b.rigid_body.velocity.x = collider_b.rigid_body.velocity.x + p * collider_a.rigid_body.mass * nx
                collider_b.rigid_body.velocity.y = collider_b.rigid_body.velocity.y + p * collider_a.rigid_body.mass * ny

                collider_a.get_owner().broadcast_collision_to_components(collider_b, None, None)
                collider_b.get_owner().broadcast_collision_to_components(collider_a, None, None)

        elif (issubclass(type(collider_a), CircleCollider) and issubclass(type(collider_b), RectCollider)):
            self.process_rect_circle_intersection(collider_b, collider_a)
        elif (issubclass(type(collider_a), RectCollider) and issubclass(type(collider_b), CircleCollider)):
            self.process_rect_circle_intersection(collider_a, collider_b)

    def process_rect_circle_intersection(self, rect_collider, circle_collider):
        """
        Este método testa se um retangulo e um circulo estão se intersectando
        """
        cond1  = line_circle_intersection_test(rect_collider.top_left, rect_collider.top_right, circle_collider.center, circle_collider.radius)
        cond2  = line_circle_intersection_test(rect_collider.top_left, rect_collider.bottom_left, circle_collider.center, circle_collider.radius)
        cond3  = line_circle_intersection_test(rect_collider.bottom_left, rect_collider.bottom_right, circle_collider.center, circle_collider.radius)
        cond4  = line_circle_intersection_test(rect_collider.bottom_right, rect_collider.top_right, circle_collider.center, circle_collider.radius)
        
        if cond1 or cond2 or cond3 or cond4:
            rect_collider.get_owner().broadcast_collision_to_components(circle_collider, None, None)
            circle_collider.get_owner().broadcast_collision_to_components(rect_collider, None, None)


    def register_collider(self, collider: Collider):
        """
        Adiciona um novo colisor a lista de colisores
        """
        self.__collider_list.append(collider)
    
    def remove_collider(self, collider: Collider):
        """
        Remove o colisor da lista de colisores
        """
        self.__collider_list.remove(collider)


