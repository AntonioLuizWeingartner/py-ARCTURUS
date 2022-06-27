"""
Ponto de entrada da aplicação
"""

from pygame.math import Vector2
from engine.core.application import Application
from engine.core.utilities import scale_vector_with_meter, scaled_number,scale_number_with_meter
from engine.core.objects import CircleRenderer,Rigidbody,ShipController,SpriteRenderer,MouseFollower
from engine.core.objects import AnimatedSprite, BackgroundRenderer, TextRenderer, Button
import engine
from engine.core.physics import RectCollider
from engine.game.asteroid import AsteroidManagerScript, ExplosionManager
from engine.game.game_logic import GameManager, ScoreListener
from engine.game.weapon import Weapon, BulletFactory
import os
app = Application()
engine.core.utilities.application_reference = app
app.get_img_loader().load_new_image('AI_SHIP.png','ship')
app.get_img_loader().load_new_image('F5S2.png', 'ship_2')
app.get_img_loader().load_new_image('asteroid.png', 'asteroid')
app.get_img_loader().load_new_image('starfield.jpg', 'starfield')
app.get_sound_manager().load_new_sound('PlasmaShot.wav','plasma_shot')
app.get_sound_manager().load_new_sound('bigExplosion.wav', 'big_explosion')
app.get_sound_manager().load_new_sound('CometExplosion01.wav', 'comet_explosion')
app.get_sound_manager().load_new_sound('shipExplosion.wav', 'ship_explosion')
app.get_sound_manager().load_new_sound('button_press.wav', 'button')
app.get_sound_manager().load_new_sound('pause_sound.wav', 'pause')

screen_width = app.get_display().get_width()
screen_height = app.get_display().get_height()

app.get_img_loader().create_sprite_sequence('explosion')
for i in range(254):
    index = "{:04d}".format(i)
    app.get_img_loader().load_image_to_sprite_sequence('explosion/explosion'+index+".png", 'explosion')


meter = app.get_meter()

explosion_manager = app.add_game_object()
explosion_manager.add_component(ExplosionManager)

game_and_level_manager = app.add_game_object()
game_and_level_manager.add_component(AsteroidManagerScript)
gm = game_and_level_manager.add_component(GameManager)


app.run()
