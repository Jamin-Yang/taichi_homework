# 计算海面高度和渲染
import taichi as ti
from modules import noise, lerp, clamp, reflect, smoothstep
from euler_angle import fromEuler
# 基本参数 
# 分辨率
resx = 1024
resy = 512
EPSILON_NUM = 0.1 / resx
PI = 3.141592
# 求光线和海面相交时的迭代次数
NUM_StEPS = 8
ITER_GEOMETRY = 4
ITER_FRAGMENT = 8
# 海水基本参数 波高，波浪起伏数量(越大，起伏的波浪越多)，波速，频率
SEA_HEIGHT = 0.6
SEA_CHOPPY = 4.0
SEA_SPEED = 1.2
SEA_FREQ = 0.16

# 坐标的映射矩阵，在迭代次数较少的时候，坐标轨迹类似于圆圈，迭代次数多了之后，轨迹类似于螺线
# 根据不同的需要来选取迭代的次数
octave_m = ti.Matrix([[1.6, 1.2],[-1.2, 1.6]])



# diffuse light
# 漫反射光照，将光照的强度限制在一定的范围内，p取80
@ti.func
def diffuse(n:ti.template(), l:ti.template(), p:ti.f32):
    return pow(n.dot(l)*0.4+0.6,p) 


# high light
# 高光反射，将几乎垂直入射，并且进入‘眼睛’的光设置很高，s取60，可以取更高获得更强的镜面反射
@ti.func
def specular(n:ti.template(), l:ti.template(), eye:ti.template(), s):
    nrm = (s + 8.0) / (PI * 8.0)
    return pow(max(reflect(-eye,n).dot(l),0.0),s) * nrm



# 按照视角y轴的值来设置天空的颜色
@ti.func
def getSkyColor(e):
    e.y = (max(e.y,0.0) * 0.8 + 0.2) * 0.8
    # 设置天空的rgb颜色，取y轴向上，当y值越大，头抬得越高天空越蓝；当y越小，即水天相交区域，为白色
    return ti.Vector([pow(1.0-e.y,2.0), 1.0-e.y, 0.6+(1.0-e.y)*0.4]) * 1.1 


# 生成波浪高度的伪随机数
@ti.func
def sea_octave(uv, choppy): # uv是水质点的平面坐标(x,z)
    nuv = noise(uv)         # 生成随机的'高度'噪声，起伏
    uv = uv + ti.Vector([nuv,nuv]) 

    # 该处的算法我没有找到具体的原理，其具体的效果是生成一种类似于条带状的'perlin noise'
    # 控制波浪的宽度，使得海面上的波峰线两侧的高度缓慢地下降
    wv = 1.0 - abs(ti.sin(uv))
    swv = abs(ti.cos(wv))
    wv = lerp(wv, swv, wv)
    return pow(1.0-pow(wv.x*wv.y,0.65), choppy)


# 生成每个像素点对应的水质点的海面高度，为海面起伏的基本状况
# 较为精细的海面由map_detailed(下方)求得
# 基本的，较为粗糙的海面起伏
@ti.func
def map(p,t):
    # 基本参数，freq决定波浪的密集程度，amp决定波浪的起伏大小，choppy决定波浪的粗糙程度
    freq = SEA_FREQ
    amp = SEA_HEIGHT
    choppy = SEA_CHOPPY

    uv = ti.Vector([0.75*p.x, p.z])
    # d为一个[0,1]的随机数，决定了某点的振幅大小，h=d*amp，为最终的振幅
    d,h = 0.0, 0.0

    # 迭代多次，次数越多，海面起伏的细节越多，该处迭代次数较少
    for i in range(ITER_GEOMETRY):
        # d由sea_octave生成，为生成波浪高度的随机数
        d = sea_octave((uv+ti.Vector([t,t]))*freq, choppy)
        d += sea_octave((uv-ti.Vector([t,t]))*freq, choppy)
        h += d * amp

        # 将坐标旋转，轨迹类似于曲率较小圆弧
        # 该圆弧类似于海洋中的波峰线，平直但又有弯曲
        uv = octave_m @ uv

        # 随着迭代次数增加，波浪高度越来越大，越来越密集，粗糙度也在增加
        freq *= 1.9
        amp *= 0.22
        choppy = lerp(choppy, 1.0, 0.2)
    return p.y - h



# 精细的海面高度
# 在获取法线，来设置折射反射光时使用，以获得更精细的海面起伏，以获得有许多小波浪的效果
# 与map函数的区别仅在于迭代的次数更多
@ti.func
def map_detailed(p, t):
    freq = SEA_FREQ
    amp = SEA_HEIGHT
    choppy = SEA_CHOPPY
    uv = ti.Vector([0.75*p.x, p.z])
    d,h = 0.0, 0.0
    for i in range(ITER_FRAGMENT):
        d = sea_octave((uv+ti.Vector([t, t]))*freq, choppy)
        d += sea_octave((uv-ti.Vector([t, t]))*freq, choppy)
        h += d * amp
        uv = octave_m @ uv
        freq *= 1.9
        amp *= 0.22
        choppy = lerp(choppy, 1.0, 0.2)
    return p.y - h



@ti.func
def getSeaColor(p, n, l, eye, dist):
    # 海水的基底颜色和海水的颜色
    base = ti.Vector([0, 0.09, 0.18])       
    waterc = ti.Vector([0.8, 0.9, 0.6]) * 0.6 

    # 由天空反射的颜色
    reflected = getSkyColor(reflect(eye, n))
    # 由海水折射的颜色
    refracted = base + waterc * 0.12 * diffuse(n,l,80.0)
    
    # 使用菲涅尔定理得到海面上光线反射和折射的颜色的占比
    # 该处使用了近似
    fresnel = clamp(1.0 - n.dot(eye), 0.0, 1.0)
    fresnel = pow(fresnel,3.0) * 0.5
    # 将海水折射和反射的颜色进行线性插值
    color = lerp(refracted, reflected, fresnel)

    # 颜色衰减，距离眼睛越远颜色会变淡，波浪高度越低也会越淡，起到一种渐变的效果
    atten = max(1.0 - dist.dot(dist) * 0.001, 0.0)
    color = color + ti.Vector([0.8, 0.9, 0.6]) * 0.6 * (p.y - SEA_HEIGHT) * 0.18 * atten

    # 加上高光
    color = color + specular(n, l, eye, 60.0)  

    return color



# 计算交点的法向量
# 使用map_detailed获取更精细的海表面高度，以获得的法线
@ti.func
def getNormal(p, eps, t):
    # 获得某水质点的高度
    y = map_detailed(p, t)

    # 使用一阶泰勒展开求x、z方向的导数，即(h(x+Δx)-h(x))/1 
    # Δx的取值，即eps取决于该水质点到眼睛的距离 eps=distance^2 * a small number
    x = map_detailed(ti.Vector([p.x+eps,p.y,p.z]), t) - y
    z = map_detailed(ti.Vector([p.x,p.y,p.z+eps]), t) - y
    y = eps
    # 返回法线的单位向量
    return ti.Vector([x, y, z]).normalized()



# 计算ray和水体或天空的交点
# 采用类似于二分法求交点，每次前进的步长是插值获得的
@ti.func
def heightMapTracing(ori, dir, p, t):
    tm = 0.0                            # 距离眼睛最近的t
    tx = 1000.0                         # 距离眼睛最远的t
    tmid = 0.0                          # 由tm和tx插值获得
    
    hx = map(ori + dir * tx, t)         # 最远点的海面高度
    hm = map(ori + dir * tm, t)         # 最近点的海面高度

    if hx > 0.0:                        # 如果无穷远还在海上就直接返回p
        p = ori + dir * tx
    else:                               # 射到了海底，进行迭代靠近海面
        for i in range(NUM_StEPS):           # 类似于二分法迭代
            tmid = lerp(tm, tx, hm/(hm-hx))  # 使用线性插值获得每次前进的步长
            p = ori + dir * tmid
            hmid = map(p, t)                 # 计算当前高度
            if hmid < 0.0:                   # 当交点为水面下时，h<0，水平面的高度为0.6
               tx = tmid
               hx = hmid
            else:                            # 当交点在水面上时，h>0
                hm = tmid
                hx = hmid
    return p


# 计算每个像素点的颜色
@ti.func
def getPixel(i:ti.i32, j:ti.i32, time:ti.f32) -> ti.template():
    uv = ti.Vector([float(i/resx), float(j/resy)])
    # 将坐标映射到[-2,2]and[-1,1]
    uv = uv * 2.0 - 1.0
    uv.x *= resx / resy

    # ray
    # 欧拉角
    ang = ti.Vector([ti.sin(time*3.0)*0.1,ti.sin(time)*1.0+0.3,time])

    # 设置眼睛的位置
    ori = ti.Vector([0.0, 3.5, 5.0])

    # 设置眼睛到画布每个像素点的单位向量
    # 画布的位置为[x,y,-2]，即z轴从眼睛到画布的距离为5-(-2)=7
    dir = ti.Vector([uv.x, uv.y, -2.0]).normalized()
    # 距离画布的中心越远的像素点，距离眼睛的距离就越近
    dir.z += uv.norm() * 0.14

    # 欧拉视角变换，投影到屏幕上，其中包含时间变量t，故投影随着时间而变化
    dir = fromEuler(ang) @ dir.normalized()

    # tracing

    # 设置碰撞点
    p = ti.Vector([0.0, 0.0, 0.0])
    # 碰撞并返回碰撞点坐标，并得到两点之间的向量dist
    p = heightMapTracing(ori, dir, p, time)
    dist = p - ori

    # 获得碰撞点(面)的法相线
    n = getNormal(p, dist.dot(dist)*EPSILON_NUM, time)
    # 设置太阳的位置
    light = ti.Vector([0.0, 1.0, 0.8]).normalized()

    # color
    # 将天空和海水的颜色混合
    return lerp(getSkyColor(dir),
                getSeaColor(p, n, light, dir, dist),
                pow(smoothstep(0.0, -0.2, dir.y),0.2))