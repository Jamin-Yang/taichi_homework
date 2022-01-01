import taichi as ti
from color import getPixel
import time
ti.init(arch=ti.gpu)

resx = 1024
resy = 512
color = ti.Vector.field(3, ti.f32, shape=(resx,resy))

gui = ti.GUI('Sea', (resx, resy))

def SEA_TIME():
    t = time.localtime()
    return t.tm_sec

@ti.kernel
def draw(t:ti.f32):
     for i,j in color:
        color[i, j] = getPixel(i, j, t)

#for i in range(100000):
while gui.running:
    t = float(SEA_TIME()) * 0.03
    draw(t)

    gui.set_image(color.to_numpy())
    gui.show()

