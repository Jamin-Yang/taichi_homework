# 海洋表面波浪的模拟
使用算法生成的海面波浪，并使用ray tracing进行渲染
# 背景简介
参考shadertoy上的一份海洋波浪模拟
网址 https://www.shadertoy.com/view/Ms2SD1

# 成果展示
![ezgif com-gif-maker](https://user-images.githubusercontent.com/91379790/148377586-5947b384-c5f9-4f61-b2ba-cfb799292d18.gif)

# 基本思路
该作业为生成海面波浪起伏的画面，加上视角的变换，带来在海洋上空飞行的视觉体验

基本思路：

1.生成天空淡蓝色的背景

根据视线点的高度来决定天空的颜色(getSkyColor)

2.生成海水表面的细节，使用伪随机数的生成方法

设定水平面的高度为0.6，使用伪随机数的方法生成波浪。首先根据坐标，使用octave函数生成一个'随机'高度，随机高度类似于perlin noise生成的高度图(noise)，类似条带状连续，以模仿实际波浪的形状。
接着使用map函数生成全局的波浪高度。

3.生成海洋的颜色，颜色由三部分组成，海水基底+海水折射+海水反射(+高光)(getSeaColor)

使用ray tracing的方法来渲染颜色。根据taichi课上讲述的方法类似，进行了漫反射和镜面反射两个过程。

4.海洋的颜色和天空的颜色混合(lerp)

5.加入视角的改变，即欧拉视角变换(fromEuler)

使用欧拉变换矩阵，进行视角的变换。实现原理参考 https://en.wikipedia.org/wiki/Euler_angles#Rotation_matrix 中的Tait–Bryan angles的Z1X2Y3变换

# 整体结构

-main.py 程序运行主体

-height_color.py 海面波浪高度的计算和海水、天空颜色的渲染

-modules.py 运算过程使用的function

-euler_angle.py 欧拉视角变换

# 运行环境和运行方式
[Taichi] version 0.8.3

win, python 3.9.9

python3 main.py
