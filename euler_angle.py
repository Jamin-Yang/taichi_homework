import taichi as ti
# 欧拉角->旋转矩阵->平面投影 
# 具体公式见 https://en.wikipedia.org/wiki/Euler_angles#Rotation_matrix 中的Tait–Bryan angles的Z1X2Y3变换
@ti.func
def fromEuler(ang:ti.template()):
    a1 = ti.Vector([ti.sin(ang.x), ti.cos(ang.x)])
    a2 = ti.Vector([ti.sin(ang.y), ti.cos(ang.y)])
    a3 = ti.Vector([ti.sin(ang.z), ti.cos(ang.z)])
    m = ti.Matrix([[a1.y*a3.y+a1.x*a2.x*a3.x,a1.y*a2.x*a3.x+a3.y*a1.x,-a2.y*a3.x],
     [-a2.y*a1.x,a1.y*a2.y,a2.x], 
     [a3.y*a1.x*a2.x+a1.y*a3.x,a1.x*a3.x-a1.y*a3.y*a2.x,a2.y*a3.y]])
    return m