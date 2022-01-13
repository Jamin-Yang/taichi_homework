# 该作业为生成海面波浪起伏的画面，加上视角的变换，带来在海洋上空飞行的视觉体验
# 基本思路：
# 1.生成天空淡蓝色的背景(getSkyColor)
# 2.生成海水表面的细节，使用伪随机数的生成方法(map,octave，noise)
# 3.生成海洋的颜色，颜色由三部分组成，海水基底+海水折射+海水反射(+高光)(getSeaColor)
# 4.海洋的颜色和天空的颜色混合(lerp)
# 5.加入视角的改变，即欧拉视角变换(fromEuler)
# 视角变换在euler_angle模组，高度计算和颜色渲染在height_color模组里，插值等小函数在modules模组里

import taichi as ti
from height_color import getPixel
ti.init(arch=ti.gpu)

output = True                       # false for output as gif, true for gui
resx = 1024
resy = 512
color = ti.Vector.field(3, ti.f32, shape=(resx,resy))


@ti.kernel
def draw(t:ti.f32):
     for i,j in color:
        color[i, j] = getPixel(i, j, t)

# 选择输出方式，使用gui或者是输出为gif
if output:
    gui = ti.GUI('sea', res=(resx,resy))
else:
    result_dir = "./finalresults"
    video_manager = ti.VideoManager(output_dir=result_dir, framerate=24, automatic_build=True)

if output:
    # 使用taichi的gui直接输出
    for i in range(100):
        t = i * 0.005
        draw(t)
        pixels_img = color.to_numpy()
        gui.set_image(pixels_img)
        gui.show()
else:
    # 使用write_frame储存到指定路径
    for i in range(100):
        t = i * 0.005
        draw(t)
        pixels_img = color.to_numpy()
        video_manager.write_frame(pixels_img)
        print(f'\rFrame {i+1} is recorded', end='')

if not output:
    print()
    print('Exporting .gif videos...')
    video_manager.make_video(gif=True, mp4=False)
    print(f'GIF video is saved to {video_manager.get_output_filename(".gif")}')
