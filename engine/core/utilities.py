"""
Esse método contem apenas funções auxiliares
"""
import math
from typing import Tuple
from pygame.math import Vector2


application_reference = None

def cast_to_int_vector(vector: Vector2) -> Tuple[int, int]:
    """
    Essa função converte uma sequencia de floats em uma sequencia de inteiros
    """

    return tuple(map(int, vector))

def angle_interpolation(angle_a: float, angle_b: float, interpolation: float) -> float:
    """
    Retorna um angulo entre angle_a e angle_b com base no valor de interpolação definido
    """
    return angle_a + (angle_b - angle_a)*interpolation


def scale_number_with_meter(n : float) -> float:
    """
    Esacala um número com base no metro
    """
    return n*application_reference.get_meter()

def scale_vector_with_meter(vector: Vector2) -> Vector2:
    """
    Essa função redimensiona um vetor com base no metro, ex:
    Entrada: Vector(2, 2)
    Saida: Vector(2*metro, 2*metro)
    """
    return vector*application_reference.get_meter()

def scale_vector_with_frame_rate(vector: Vector2) -> Vector2:
    """
    Essa função redimensiona um vetor com base no frame rate, ex:
    Entrada: Vector2(2, 2)
    Saida: Vector2(2/frame_rate, 2/frame_rate)
    """
    return vector*(1/application_reference.get_frame_rate())

def scaled_vector(vector: Vector2) -> Vector2:
    """
    Essa função cria um vetor dimensionado
    """
    return vector*application_reference.get_meter()*(1/application_reference.get_frame_rate())

def scaled_number(n : float) -> float:
    """
    Essa função dimensiona um numero usando metros e o frame rate
    """
    return n*application_reference.get_meter()*(1/application_reference.get_frame_rate())

def line_circle_intersection_test(line_start: Vector2, line_end: Vector2, center: Vector2, radius: float) -> bool:
    """
    Essa função retorna verdadeiro se uma linha esta intersectando
    """

    if is_point_inside_circle(line_start, center, radius) or is_point_inside_circle(line_end, center, radius):
        return True
 
    distance = distance_between_point_and_line(center, line_start, line_end)
    if distance <= radius:
        print("Sucesso")
        return True
    else:
        return False

def is_point_inside_circle(point: Vector2, center: Vector2, radius: Vector2) -> bool:
    """
    Esta função checa se um ponto esta dentro de um circulo
    """
    if (point - center).magnitude_squared() <= radius*radius:
        return True
    else:
        return False

def is_point_inside_rect(point: Vector2, rect_top_left: Vector2, rect_bottom_right: Vector2):
    """
    Essa função ira checar se um ponto esta dentro de um AABB (retangulo alinhado com o eixo y)
    """
    if point.x > rect_top_left.x and point.x < rect_bottom_right.x and point.y > rect_top_left.y and point.y < rect_bottom_right.y:
        return True

    return False

def distance_between_point_and_line(point: Vector2, line_start: Vector2, line_end: Vector2) -> float:
    """
    Essa função retorna a menor distancia entre um segmento de linha e um ponto
    """
    line = line_end - line_start
    point_v = line_end - point
    line_magnitude = line.magnitude()
    line_unitary = Vector2(line.x, line.y).normalize()
    point_vector_scaled = point_v/line_magnitude
    d = line_unitary.dot(point_vector_scaled)
    if d < 0.0:
        d = 0.0
    elif d > 1.0:
        d = 1.0
    return (point_v - line*d).magnitude()