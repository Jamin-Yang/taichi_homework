import taichi as ti
from modules import noise, lerp, clamp, smoothstep
from view import diffuse, specular, reflect, fromEuler
import time

resx = 1024
resy = 512
EPSILON_NUM = 0.1 / resx
NUM_StEPS = 8
ITER_GEOMETRY = 4
ITER_FRAGMENT = 8
SEA_HEIGHT = 0.6
SEA_CHOPPY = 4.0
SEA_SPEED = 0.8
SEA_FREQ = 0.16

octave_m = ti.Matrix([[1.6, 1.2],[-1.2, 1.6]])

def SEA_TIME():
    t = time.localtime()
    return 1.0 + t.tm_sec*SEA_SPEED  

# setting sky color
@ti.func
def getSkyColor(e):
    e.y = (max(e.y,0.0) * 0.8 + 0.2) * 0.8
    # sky goes more blue when looking up
    return ti.Vector([pow(1.0-e.y,2.0), 1.0-e.y, 0.6+(1.0-e.y)*0.4]) * 1.1 

# adding details to waves
@ti.func
def sea_octave(uv, choppy):
    nuv = noise(uv)
    uv = uv + ti.Vector([nuv,nuv])
    wv = 1.0 - abs(ti.sin(uv))
    swv = abs(ti.cos(wv))
    wv = lerp(wv, swv, wv)
    return pow(1.0-pow(wv.x*wv.y,0.65), choppy)

@ti.func
def map(p):
    freq = SEA_FREQ
    amp = SEA_HEIGHT
    choppy = SEA_CHOPPY
    uv = ti.Vector([0.75*p.x, p.z])
    d,h = 0.0, 0.0
    for i in range(ITER_GEOMETRY):
        d = sea_octave((uv+ti.Vector([SEA_TIME(),SEA_TIME()]))*freq, choppy)
        d += sea_octave((uv-ti.Vector([SEA_TIME(),SEA_TIME()]))*freq, choppy)
        h += d * amp
        uv = octave_m @ uv
        freq *= 1.9
        amp *= 0.22
        choppy = lerp(choppy, 1.0, 0.2)
    return p.y - h

@ti.func
def map_detailed(p):
    freq = SEA_FREQ
    amp = SEA_HEIGHT
    choppy = SEA_CHOPPY
    uv = ti.Vector([0.75*p.x, p.z])
    d,h = 0.0, 0.0
    for i in range(ITER_FRAGMENT):
        d = sea_octave((uv+ti.Vector([SEA_TIME(),SEA_TIME()]))*freq, choppy)
        d += sea_octave((uv-ti.Vector([SEA_TIME(),SEA_TIME()]))*freq, choppy)
        h += d * amp
        uv = octave_m @ uv
        freq *= 1.9
        amp *= 0.22
        choppy = lerp(choppy, 1.0, 0.2)
    return p.y - h

@ti.func
def getSeaColor(p, n, l, eye, dist):
    base = ti.Vector([0, 0.09, 0.18])       # sea base color
    waterc = ti.Vector([0.8, 0.9, 0.6]) * 0.6 # water color
    fresnel = clamp(1.0 - n.dot(eye), 0.0, 1.0)
    fresnel = pow(fresnel,3.0) * 0.5
    reflected = getSkyColor(reflect(eye, n))
    refracted = base + waterc * 0.12 * diffuse(n,l,80.0)
    
    color = lerp(refracted, reflected, fresnel)
    atten = max(1.0 - dist.dot(dist) * 0.001, 0.0)
    color = color + ti.Vector([0.8, 0.9, 0.6]) * 0.6 * (p.y - SEA_HEIGHT) * 0.18 * atten

    color = color + specular(n, l, eye, 60.0)  # lower

    return color

@ti.func
def getNormal(p, eps):
    y = map_detailed(p)
    x = map_detailed(ti.Vector([p.x+eps,p.y,p.z])) - y
    z = map_detailed(ti.Vector([p.x,p.y,p.z+eps])) - y
    y = eps
    return ti.Vector([x, y, z]).normalized()

@ti.func
def heightMapTracing(ori, dir, p):
    tm = 0.0
    tx = 1000.0
    hx = map(ori + dir * tx)
    if hx > 0.0:
        p = ori + dir * tx
    hm = map(ori + dir * tm)
    tmid = 0.0
    for i in range(NUM_StEPS):
        tmid = lerp(tm, tx, hm/(hm-hx))
        p = ori + dir * tmid
        hmid = map(p)
        if hmid < 0.0:
            tx = tmid
            hx = hmid
        else:
            hm = tmid
            hx = hmid
        return p

@ti.func
def getPixel(i:ti.i32, j:ti.i32, time:ti.f32) -> ti.template():
    uv = ti.Vector([float(i/resx), float(j/resy)])
    uv = uv * 2.0 - 1.0
    uv.x *= resx / resy

    # ray
    ang = ti.Vector([ti.sin(time*3.0)*0.1,ti.sin(time)*1.0+0.3,time])
    #ori = ti.Vector([0.0, 3.5, time*5.0])
    ori = ti.Vector([0.0, 3.5, 5.0])
    dir = ti.Vector([uv.x, uv.y, -2.0]).normalized()
    dir.z += uv.norm() * 0.14
    dir = fromEuler(ang) @ dir.normalized()

    # tracing
    p = ti.Vector([0.0, 0.0, 0.0])
    p = heightMapTracing(ori, dir, p)
    dist = p - ori
    n = getNormal(p, dist.dot(dist)*EPSILON_NUM)
    light = ti.Vector([0.0, 1.0, 0.8]).normalized()

    # color
    return lerp(getSkyColor(dir),
                getSeaColor(p, n, light, dir, dist),
                pow(smoothstep(0.0, -0.2, dir.y),0.2))