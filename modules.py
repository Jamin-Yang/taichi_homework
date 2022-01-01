import taichi as ti

@ti.func
def lerp(a, b, frac):
    return a + frac * (b - a)

@ti.func
def reflect(e, n):
    return e - 2 * e.dot(n) * n  

@ti.func
def clamp(v, vmin, vmax):
    return max(min(v, vmax), vmin)

@ti.func
def smoothstep(vl, vr, v):
    t = (v - vl) / (vr - vl)
    t = clamp(t, 0.0, 1.0)
    return (3 - 2*t) * t ** 2

@ti.func
def hash(p:ti.template()):
    h = p.dot(ti.Vector([127.1,311.7]))
    sinh = ti.sin(h) * 43758.5453123
    return sinh - ti.floor(sinh)

@ti.func
def noise(p:ti.template()):
    fp = ti.Vector([float(p.x), float(p.y)])
    i = ti.floor(fp)
    f = fp - i
    u = f * f * (3.0 - 2.0 * f)
    return -1.0 + 2.0 * lerp(lerp(hash(i+ti.Vector([0, 0])),
                            hash(i+ti.Vector([1.0, 0])), u.x),
                        lerp(hash(i+ti.Vector([0, 1.0])),
                            hash(i+ti.Vector([1.0, 1.0])),u.x),u.y)