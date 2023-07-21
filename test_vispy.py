# -*- coding: utf-8 -*-
# @Author: Guillaume Viejo
# @Date:   2023-07-21 16:36:26
# @Last Modified by:   Guillaume Viejo
# @Last Modified time: 2023-07-21 16:41:52
import sys
from vispy import app, gloo

app.use_app("SDL2")

canvas = app.Canvas(keys='interactive')


@canvas.connect
def on_draw(event):
    gloo.set_clear_color((0.2, 0.4, 0.6, 1.0))
    gloo.clear()


canvas.show()

# if __name__ == '__main__' and sys.flags.interactive == 0:
app.run()