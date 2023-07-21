# -*- coding: utf-8 -*-
# @Author: Guillaume Viejo
# @Date:   2023-07-21 11:30:45
# @Last Modified by:   Guillaume Viejo
# @Last Modified time: 2023-07-21 14:32:18
import sys
import sdl2.ext
import sdl2

# RESOURCES = sdl2.ext.Resources(__file__, "/mnt/home/gviejo/Pictures")

# sdl2.ext.init()

# window = sdl2.ext.Window("Hello World!", size=(1240, 800))
# window.show()

# factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
# sprite = factory.from_image(RESOURCES.get_path("hello.png"))

# sprite.position = (100, 200)

# spriterenderer = factory.create_sprite_render_system(window)
# spriterenderer.render(sprite)

# processor = sdl2.ext.TestEventProcessor()
# processor.run(window)


# sdl2.ext.quit()

WHITE = sdl2.ext.Color(255, 255, 255)

class SoftwareRenderer(sdl2.ext.SoftwareSpriteRenderSystem):
    def __init__(self, window):
        super(SoftwareRenderer, self).__init__(window)

    def render(self, components):
        sdl2.ext.fill(self.surface, sdl2.ext.Color(0, 0, 0))
        super(SoftwareRenderer, self).render(components)


class Player(sdl2.ext.Entity):
    def __init__(self, world, sprite, posx=0, posy=0):
        self.sprite = sprite
        self.sprite.position = posx, posy


def run():
    sdl2.ext.init()
    window = sdl2.ext.Window("The game", size = (800, 600))
    window.show()

    world = sdl2.ext.World()

    spriterenderer = SoftwareRenderer(window)
    world.add_system(spriterenderer)

    factory = sdl2.ext.SpriteFactory(sdl2.ext.SOFTWARE)
    sp_paddle1 = factory.from_color(WHITE, size=(20, 100))
    sp_paddle2 = factory.from_color(WHITE, size=(20, 100))

    player1 = Player(world, sp_paddle1, 0, 250)
    player2 = Player(world, sp_paddle2, 780, 250)   

    running = True
    while running:      
        events = sdl2.ext.get_events()
        for event in events:
            if event.type == sdl2.SDL_QUIT:
                running = False
                break
        window.refresh()
    sdl2.ext.quit()
    return 0

if __name__ == "__main__":
    sys.exit(run())