import taichi as ti
from color import getPixel
ti.init(arch=ti.gpu)

resx = 1024
resy = 512
color = ti.Vector.field(3, ti.f32, shape=(resx,resy))

gui = ti.GUI('Waves', (resx, resy))

@ti.kernel
def draw(t:ti.f32):
     for i,j in color:
        color[i, j] = getPixel(i, j, t)

while gui.running:
    for i in range(10000):
        t = i * 0.003
        draw(t)
    
        gui.set_image(color.to_numpy())
        gui.show()

