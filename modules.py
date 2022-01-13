# 基本的小函数，如lerp，reflect获得反射光线，smoothstep多项式平滑插值，hash获得一个近似随机的小数
# noise
import taichi as ti
#线性插值
@ti.func
def lerp(a, b, frac):
    return a + frac * (b - a)

# 获得反射光线
@ti.func
def reflect(e, n):
    return e - 2 * e.dot(n) * n  

# 夹值 tmin<=t<=tmax
@ti.func
def clamp(v, vmin, vmax):
    return max(min(v, vmax), vmin)

# 多项式插值，更加平滑
@ti.func
def smoothstep(vl, vr, v):
    t = (v - vl) / (vr - vl)
    t = clamp(t, 0.0, 1.0)
    return (3 - 2*t) * t ** 2

# '随机'生成一个小数
@ti.func
def hash(p:ti.template()):
    h = p.dot(ti.Vector([127.1,311.7]))
    sinh = ti.sin(h) * 43758.5453123
    return sinh - ti.floor(sinh)

#噪声函数，范围[-1,1]，p为某点的位置
@ti.func
def noise(p:ti.template()):
    fp = ti.Vector([float(p.x), float(p.y)])
    i = ti.floor(fp)
    # f为diff
    f = fp - i
    # u为多项式插值后的diff，使得最终的结果更加平滑，结果更加集中
    u = f * f * (3.0 - 2.0 * f)
    # 二维线性插值，即在水平方向上用diff.x插值两次，后在y方向上用diff.y插值一次
    return -1.0 + 2.0 * lerp(lerp(hash(i+ti.Vector([0, 0])),
                            hash(i+ti.Vector([1.0, 0])), u.x),
                        lerp(hash(i+ti.Vector([0, 1.0])),
                            hash(i+ti.Vector([1.0, 1.0])),u.x),u.y)
