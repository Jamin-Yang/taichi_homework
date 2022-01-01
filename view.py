import taichi as ti
from modules import reflect
PI = 3.141592

@ti.func
def fromEuler(ang:ti.template()):
    a1 = ti.Vector([ti.sin(ang.x), ti.cos(ang.x)])
    a2 = ti.Vector([ti.sin(ang.y), ti.cos(ang.y)])
    a3 = ti.Vector([ti.sin(ang.z), ti.cos(ang.z)])
    m = ti.Matrix([[a1.y*a3.y+a1.x*a2.x*a3.x,a1.y*a2.x*a3.x+a3.y*a1.x,-a2.y*a3.x],
     [-a2.y*a1.x,a1.y*a2.y,a2.x], 
     [a3.y*a1.x*a2.x+a1.y*a3.x,a1.x*a3.x-a1.y*a3.y*a2.x,a2.y*a3.y]])
    return m

# diffuse light
@ti.func
def diffuse(n:ti.template(), l:ti.template(), p:ti.f32):
    return pow(n.dot(l)*0.4+0.6,p) 

# high light
@ti.func
def specular(n:ti.template(), l:ti.template(), eye:ti.template(), s):
    nrm = (s + 8.0) / (PI * 8.0)
    return pow(max(reflect(-eye,n).dot(l),0.0),s) * nrm