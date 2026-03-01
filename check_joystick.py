import pygame
import sys

pygame.init()
pygame.joystick.init()

count = pygame.joystick.get_count()
print(f"检测到的手柄数量: {count}")

if count == 0:
    print("错误: 没有检测到任何手柄。请检查连接。")
else:
    for i in range(count):
        try:
            js = pygame.joystick.Joystick(i)
            js.init()
            print(f"手柄 {i}: {js.get_name()} (ID: {js.get_instance_id()})")
            print(f"  - 轴数量: {js.get_numaxes()}")
            print(f"  - 按钮数量: {js.get_numbuttons()}")
            print(f"  - HAT数量: {js.get_numhats()}")
            js.quit()
        except Exception as e:
            print(f"无法读取手柄 {i}: {e}")

pygame.quit()
