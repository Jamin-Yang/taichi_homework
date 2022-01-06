import taichi as ti
from color import getPixel
ti.init(arch=ti.gpu)

output = False                       # false for output as gif, true for gui
resx = 1024
resy = 512
color = ti.Vector.field(3, ti.f32, shape=(resx,resy))


@ti.kernel
def draw(t:ti.f32):
     for i,j in color:
        color[i, j] = getPixel(i, j, t)
     
if output:
    gui = ti.GUI('sea', res=(resx,resy))
else:
    result_dir = "./finalresults"
    video_manager = ti.VideoManager(output_dir=result_dir, framerate=24, automatic_build=True)



if output:
    for i in range(100):
        t = i * 0.005
        draw(t)
        pixels_img = color.to_numpy()
        gui.set_image(pixels_img)
        gui.show()
else:
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
