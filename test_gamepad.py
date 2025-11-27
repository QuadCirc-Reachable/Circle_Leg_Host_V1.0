# cd C:\Users\Floriane\python_projects
# .\xbox\Scripts\activate
# python test_gamepad.py

import pygame
import math
import sys 

"""
README:
    - 这个脚本用 pygame 读取 Xbox 手柄数据，进行各种调试输出
    - uart相关功能在另一个脚本 test2.py
    - 一般直接用跑脚本的时候用7号选项就行，什么都能测
    - 记得先安装 pygame 库：pip install pygame (ubuntu小电脑上已经装好了）
"""

def check_gamepad_all(): #检查手柄所有按钮  （Y不能用）
    # 初始化 pygame
    pygame.init()
    
    # 初始化游戏手柄
    pygame.joystick.init()
    
    # 获取游戏手柄数量
    joystick_count = pygame.joystick.get_count()
    
    if joystick_count > 0:
        # 获取第一个游戏手柄
        joystick = pygame.joystick.Joystick(0)
        joystick.init()
    
        print(f"已连接游戏手柄: {joystick.get_name()}")
    
        # 主循环
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.JOYBUTTONDOWN:
                    print(f"按钮 {event.button} 被按下")
                elif event.type == pygame.JOYBUTTONUP:
                    print(f"按钮 {event.button} 被释放")
                elif event.type == pygame.JOYAXISMOTION:
                    print(f"摇杆 {event.axis} 的值为: {event.value}")
                    '''
                    左摇杆0为水平轴，1为垂直轴
                    右摇杆2为水平轴，3为垂直轴
                    '''
    
        # 退出 pygame
        pygame.quit()
    else:
        print("未检测到游戏手柄")
    
def check_gamepad_one_bottom():  ##检查手柄某一按钮

    # 初始化 pygame 和手柄模块
    pygame.init()
    pygame.joystick.init()

    joystick_count = pygame.joystick.get_count()

    if joystick_count <= 0:
        print("未检测到游戏手柄")
        return

    # 连接第一个手柄
    joystick = pygame.joystick.Joystick(0)
    joystick.init()
    print(f"已连接游戏手柄: {joystick.get_name()}")
    print("-----------------------------------------------")

    # 让用户选择监听的按钮
    print("你想监听哪个按钮？")
    print("可输入：A / B / X / Y，或数字按钮编号（0~3）")
    choice = input("请输入: ").strip().upper()

    # 按钮名称到编号的对应表
    name_to_button = {
        "A": 0,
        "B": 1,
        "X": 2,
        "Y": 3,
    }

    # 处理用户输入
    if choice.isdigit():
        button_id = int(choice)
        button_desc = f"按钮编号 {button_id}"
    elif choice in name_to_button:
        button_id = name_to_button[choice]
        button_desc = f"{choice} 按钮"
    else:
        print("输入不合法，只能是 A/B/X/Y 或 0~3")
        return

    print(f"\n现在开始监听：{button_desc}")
    print("按 Ctrl + C 可以退出程序。\n")

    # 主事件循环
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.JOYBUTTONDOWN:
                if event.button == button_id:
                    print(f"{button_desc} 被按下")

            elif event.type == pygame.JOYBUTTONUP:
                if event.button == button_id:
                    print(f"{button_desc} 被释放")

    pygame.quit()


def print_left_stick_angle_mag():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到手柄")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"已连接手柄: {js.get_name()}")
    print("移动左摇杆查看角度和幅度输出（Ctrl+C 退出）")

    clock = pygame.time.Clock()

    while True:
        pygame.event.pump()

        # 左摇杆 X/Y
        x = js.get_axis(0)  # 左右
        y = js.get_axis(1)  # 上下

        # 死区处理
        deadzone = 0.15
        if abs(x) < deadzone:
            x = 0
        if abs(y) < deadzone:
            y = 0

        # 幅度（力度） √(x²+y²)
        magnitude = math.sqrt(x*x + y*y)
        magnitude = min(1.0, magnitude)

        if magnitude == 0:
            print("angle=None   magnitude=0.0   ", end="\r")
        else:
            # 角度（注意 y 轴反向）
            angle = math.degrees(math.atan2(-y, x))
            if angle < 0:
                angle += 360

            print(f"angle={angle:6.1f}°   magnitude={magnitude:.2f}", end="\r")  #想要换行就把end="\r"删了

        clock.tick(30)

def print_right_stick_angle_mag():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到手柄")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"已连接手柄: {js.get_name()}")
    print("移动左摇杆查看角度和幅度输出（Ctrl+C 退出）")

    clock = pygame.time.Clock()

    while True:
        pygame.event.pump()

        # 左摇杆 X/Y
        x = js.get_axis(2)  # 左右
        y = js.get_axis(3)  # 上下

        # 死区处理
        deadzone = 0.15
        if abs(x) < deadzone:
            x = 0
        if abs(y) < deadzone:
            y = 0

        # 幅度（力度） √(x²+y²)
        magnitude = math.sqrt(x*x + y*y)
        magnitude = min(1.0, magnitude)

        if magnitude == 0:
            print("angle=None   magnitude=0.0   ", end="\r")
        else:
            # 角度（注意 y 轴反向）
            angle = math.degrees(math.atan2(-y, x))
            if angle < 0:
                angle += 360

            print(f"angle={angle:6.1f}°   magnitude={magnitude:.2f}", end="\r")  #想要换行就把end="\r"删了

        clock.tick(30)



def print_left_stick_angle_mag_and_buttons():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到手柄")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"已连接手柄: {js.get_name()}")
    print("移动左摇杆查看角度/幅度 + 按 ABXY 查看按键（Ctrl+C 退出）")

    clock = pygame.time.Clock()

    while True:
        # 处理事件（按钮/退出）
        for event in pygame.event.get():

            if event.type == pygame.QUIT:
                return

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: #A按下
                    print("0")
                elif event.button == 1: #B按下
                    print("1")
                elif event.button == 2: #X按下
                    print("2")
                elif event.button == 3: #Y按下
                    print("3")

        # ========= 左摇杆角度 & 幅度 =========

       # 左摇杆 X/Y
        x = js.get_axis(0)  # 左右
        y = js.get_axis(1)  # 上下

        # 死区处理
        deadzone = 0.15
        if abs(x) < deadzone:
            x = 0
        if abs(y) < deadzone:
            y = 0

        # 幅度（力度） √(x²+y²)
        magnitude = math.sqrt(x*x + y*y)
        magnitude = min(1.0, magnitude)

        if magnitude == 0:
            print("angle: None    magnitude: 0.0   ")
        else:
            # 角度（注意 y 轴反向）
            angle = math.degrees(math.atan2(-y, x))
            if angle < 0:
                angle += 360

            print(f"angle={angle:6.1f}°   magnitude={magnitude:.2f}")  #想要换行就把end="\r"删了

        clock.tick(30)


def print_triggers():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到手柄")
        return

    js = pygame.joystick.Joystick(0)
    js.init()

    print(f"已连接手柄: {js.get_name()}")
    print("只输出扳机 LT / RT 的值（Ctrl+C 退出）")

    clock = pygame.time.Clock()

    while True:
        pygame.event.pump()

        # LT = axis 4（大部分手柄）
        # RT = axis 5（大部分手柄）
        lt = js.get_axis(4)
        rt = js.get_axis(5)

        # 死区（避免抖动）
        if lt < 0.05:
            lt = 0.0
        if rt < 0.05:
            rt = 0.0

        print(f"LT={lt:.2f}   RT={rt:.2f}")

        clock.tick(30)


def gamepad_all_1():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到手柄")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"已连接手柄: {js.get_name()}")
    print("ABXY 按钮 + 左摇杆角度/幅度 + LT/RT 扳机（Ctrl+C 退出）")

    clock = pygame.time.Clock()

    while True:
        # ====== 处理事件：按钮 / 退出 ======
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: #A
                    print("0")
                elif event.button == 1: #B
                    print("1")
                elif event.button == 2: #X
                    print("2")
                elif event.button == 3: #Y
                    print("3")
                else:
                    print(f"其他按钮 {event.button} 按下")

        # ====== 左摇杆：x, y, 角度, 幅度 ======
        x = js.get_axis(0)   # 左摇杆水平
        y = js.get_axis(1)   # 左摇杆垂直

        deadzone = 0.15
        if abs(x) < deadzone:
            x = 0.0
        if abs(y) < deadzone:
            y = 0.0

        magnitude = min(1.0, math.sqrt(x*x + y*y))

        if magnitude == 0:
            angle_text = "无"
        else:
            angle = math.degrees(math.atan2(-y, x))  # 注意 y 轴反向
            if angle < 0:
                angle += 360
            angle_text = f"{angle:6.1f}°"

        # ====== 扳机：LT / RT （假设在 axis 4 / 5）======
        lt = js.get_axis(4)
        rt = js.get_axis(5)

        trig_deadzone = 0.05
        if lt < trig_deadzone:
            lt = 0.0
        if rt < trig_deadzone:
            rt = 0.0

        # ====== 汇总打印一行 ======
        print(
            f"angle={angle_text} magnitude={magnitude:.2f} "
            f"| LT={lt:.2f} RT={rt:.2f}"
        )

        clock.tick(30)


def gamepad_all_2():
    pygame.init()
    pygame.joystick.init()

    if pygame.joystick.get_count() == 0:
        print("未检测到手柄")
        return

    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"已连接手柄: {js.get_name()}")
    print("输出：LA,LM, RA,RM, LT,RT, bottom（Angle×10，Mag/LT/RT×100）")
    print("提示：按手柄 BACK 键 或 键盘 ESC 退出")

    clock = pygame.time.Clock()

    bottom = -1
    deadzone = 0.15
    running = True   # ★ 用这个控制循环退出

    while running:
        # ★ 强制刷新事件队列，防止卡死
        pygame.event.pump()

        # ====== 处理事件：按钮 / 退出 ======
        for event in pygame.event.get():
            # 关闭窗口之类的事件
            if event.type == pygame.QUIT:
                running = False

            # 键盘 ESC 退出（如果你有开窗口）
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.JOYBUTTONDOWN:
                # ★ 用 BACK 键（通常是 button 6）作为“退出键”
                if event.button == 6:
                    print("收到退出指令（Back 键），结束程序")
                    running = False
                    break  # 跳出 for event

                # 原来的 ABXY 逻辑
                if event.button in (0, 1, 2, 3):
                    bottom = event.button   # 0=A,1=B,2=X,3=Y
                else:
                    print(f"其他按钮 {event.button} 按下")

            if event.type == pygame.JOYBUTTONUP:
                if event.button in (0, 1, 2, 3):
                    any_down = False
                    for b in (0, 1, 2, 3):
                        if js.get_button(b):
                            bottom = b
                            any_down = True
                            break
                    if not any_down:
                        bottom = -1

        if not running:
            break

        # ====== 左摇杆 LA/LM ======
        x = js.get_axis(0)
        y = js.get_axis(1)

        if abs(x) < deadzone:
            x = 0.0
        if abs(y) < deadzone:
            y = 0.0

        if x == 0.0 and y == 0.0:
            LA = -1
            LM = 0
        else:
            mag_left = min(1.0, math.sqrt(x * x + y * y))
            angle_left = math.degrees(math.atan2(-y, x))
            if angle_left < 0:
                angle_left += 360
            LA = int(round(angle_left * 10))
            LM = int(round(mag_left * 100))

        # ====== 右摇杆 RA/RM ======
        rx = js.get_axis(2)
        ry = js.get_axis(3)

        if abs(rx) < deadzone:
            rx = 0.0
        if abs(ry) < deadzone:
            ry = 0.0

        if rx == 0.0 and ry == 0.0:
            RA = -1
            RM = 0
        else:
            mag_right = min(1.0, math.sqrt(rx * rx + ry * ry))
            angle_right = math.degrees(math.atan2(-ry, rx))
            if angle_right < 0:
                angle_right += 360
            RA = int(round(angle_right * 10))
            RM = int(round(mag_right * 100))

        # ====== LT / RT ======
        lt_raw = js.get_axis(4)
        rt_raw = js.get_axis(5)

        lt_norm = (lt_raw + 1) / 2.0
        rt_norm = (rt_raw + 1) / 2.0
        lt_norm = max(0.0, min(1.0, lt_norm))
        rt_norm = max(0.0, min(1.0, rt_norm))

        LT = int(round(lt_norm * 100))
        RT = int(round(rt_norm * 100))

        # ★ 每一帧都输出一行，确认循环在跑
        print(f"LA={LA},LM={LM}, RA={RA},RM={RM}, LT={LT}, RT={RT}, bottom={bottom}")

        clock.tick(30)

    pygame.quit()
    print("程序已正常退出")
    sys.exit()


def main_menu():
    while True:
        print("\n====== 主菜单 Main Page ======")
        print("1. 手柄初始化调试")
        print("2. 按钮输入")
        print("3. 输出左摇杆信息")
        print("4. 输出右摇杆信息")
        print("5. 输出扳机LT+RT信息")
        print("6. 按钮输入+输出左摇杆信息")
        print("7. 手柄所有输入综合调试（ABXY + 左摇杆 + 扳机）")

        print("0. 退出")
        choice = input("请输入数字选择功能: ")

        if choice == "1":
            check_gamepad_all()
        elif choice == "2":
            check_gamepad_one_bottom()
        elif choice == "3":
            print("角度遵循数学正方向，0°在正右方，逆时针增加。幅度为0~1之间。")
            print_left_stick_angle_mag()
        elif choice == "4":
            print("角度遵循数学正方向，0°在正右方，逆时针增加。幅度为0~1之间。")
            print_right_stick_angle_mag()
        elif choice == "5":
            print_triggers()
        elif choice == "6":
            print_left_stick_angle_mag_and_buttons()
        elif choice == "7":
            gamepad_all_2()
        elif choice == "0":
            print("再见！")
            break
        else:
            print("无效的选择，请重新输入。")

if __name__ == "__main__":
    main_menu()