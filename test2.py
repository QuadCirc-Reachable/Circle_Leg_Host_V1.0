import pygame
import math
import sys
import serial   
import struct 

"""
README:
    - 这个脚本用 pygame 读取 Xbox 手柄数据，并把数据打包成特定格式通过 UART 发送出去
    - 要测试手柄状态的用另一个脚本 test_gamepad.py
    - uart从155行起-看具体注释
    - 记得先安装 pygame 库：pip install pygame (ubuntu小电脑上已经装好了）
    - 记得先安装 pyserial 库：pip install pyserial
    - 运行前请修改 SERIAL_PORT 为实际串口号，比如 "/dev/ttyUSB0"
"""


SERIAL_PORT = "COM6"     # 开发板时改成实际串口号，比如"/dev/ttyUSB0"
BAUD_RATE   = 2000000


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

    # 尝试打开串口（打开失败就只做 print）
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"串口 {SERIAL_PORT} 打开成功，将同步发送 UART 数据")
    except serial.SerialException as e:
        print(f"⚠ 串口 {SERIAL_PORT} 打不开，只做 print", e)
        ser = None   # 标记为“没有串口”

    clock = pygame.time.Clock()
    
    bottom = -1
    
    button_map = {
        0: 0,   # A
        1: 1,   # B
        2: 2,   # X
        3: 3,   # Y
        6: 4,   # 自定义：物理 6 → 逻辑 4
        7: 5,   # 自定义：物理 7 → 逻辑 5
        11: 6,  # 自定义：物理 11 → 逻辑 6
    }

    deadzone = 0.15
    running = True

    while running:
        pygame.event.pump()

        # ====== 处理事件：按钮 / 退出 ====== 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False

            if event.type == pygame.JOYBUTTONDOWN:
                # BACK 键（一般是 6）退出
                if event.button == 8:
                    print("收到退出指令（Back 键），结束程序")
                    running = False
                    break

                if event.button in button_map:
                    bottom = button_map[event.button]  
                    print(f"逻辑按钮 {bottom} 按下（物理 {event.button}）")  #监控/debug用，可隐藏
                else:
                    print(f"其他按钮 {event.button} 按下")  #监控/debug用，可隐藏

                if event.type == pygame.JOYBUTTONUP:
                    if event.button in button_map:
                        any_down = False
                        # 看看当前还有没有 *任何* 映射内的按钮是按下的
                        """
                        按钮按下 → bottom 变成 0-6
                        松开一个按钮时，如果还有别的按钮没松开 → bottom 保持成那个还按着的按钮号
                        按钮都松开 → bottom = -1
                        """
                        for phys_btn, logical_btn in button_map.items():
                            if js.get_button(phys_btn):
                                bottom = logical_btn
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



        # ====== “协议 + 调试输出”部分 ,修改只改这部分，前面是读xbox数据的不要动======
        # 把 LM/RM 从 x100 变成 x1000（0~1000），对应 r_x1000_msg   
        '''
        其实这里不用乘，原本100倍就可以了，但是如果按照华给的协议（一千倍）写的话就乘了
        '''
        left_r_1000  = max(0, min(1000, LM * 10))   # 左摇杆半径
        right_r_1000 = max(0, min(1000, RM * 10))   # 右摇杆半径

        # 2. LT / RT
        LT_val = max(0, min(100, LT))  # 左扳机
        RT_val = max(0, min(100, RT))  # 右扳机

        # 3. 按钮打成 bit（button_status）
        BTN_A  = 0
        BTN_B  = 1
        BTN_X  = 2
        BTN_Y  = 3
        BTN_LB = 4     # 左肩键（L1），顶部按键
        BTN_RB = 5     # 右肩键（R1），顶部按键
        BTN_ML = 8     # 左摇杆按下（L3）
        BTN_MR = 9     # 右摇杆按下（R3）

        button_status = 0
        # 顺序：| LB | RB | X | A | B | Y | ML | MR |
        # 这里先用：bit7:LB, bit6:RB, bit5:X, bit4:A, bit3:B, bit2:Y, bit1:ML, bit0:MR
        if js.get_button(BTN_LB): button_status |= (1 << 7)
        if js.get_button(BTN_RB): button_status |= (1 << 6)
        if js.get_button(BTN_X):  button_status |= (1 << 5)
        if js.get_button(BTN_A):  button_status |= (1 << 4)
        if js.get_button(BTN_B):  button_status |= (1 << 3)
        if js.get_button(BTN_Y):  button_status |= (1 << 2)
        if js.get_button(BTN_ML): button_status |= (1 << 1)
        if js.get_button(BTN_MR): button_status |= (1 << 0)

        # 4. PC_Msg 结构体（13 字节，小端）
        # struct PC_Msg{
        #   int16  left.angle_x10_msg;
        #   uint16 left.r_x1000_msg;
        #   int16  right.angle_x10_msg;
        #   uint16 right.r_x1000_msg;
        #   uint16 Left_trigger_x100_msg;
        #   uint16 Right_trigger_x100_msg;
        #   uint8  button_status;
        # } __attribute__((packed));
        try:
            payload = struct.pack(
                "<hHhHHHB",
                LA,            # 左摇杆角度×10
                left_r_1000,   # 左摇杆半径×1000 -->其实100就够
                RA,            # 右摇杆角度×10
                right_r_1000,  # 右摇杆半径×1000 -->其实100就够
                LT_val,        # Left_trigger_x100_msg (0~100)
                RT_val,        # Right_trigger_x100_msg (0~100)
                button_status  # 按钮 bit
            )
        except struct.error as e:
            print("⚠ struct.pack 出错，检查数值范围：", e)
            payload = b""

        # 5. 加 3 字节 header：sof=0xAA, protocolID=0xFF, dataLen=13
        if payload:
            sof        = 0xAA
            protocolID = 0xFF
            dataLen    = len(payload)       # 13
            header = struct.pack("<BBB", sof, protocolID, dataLen)
            frame = header + payload        # 总长度 = 3 + 13 = 16 字节
        else:
            frame = b""

        # 6. debug：打印逻辑值 + 真实发出去的 16 字节
        print(
            f"[LOGIC] LA={LA}, LM={LM}({left_r_1000}), "
            f"RA={RA}, RM={RM}({right_r_1000}), "
            f"LT={LT}({LT_val}), RT={RT}({RT_val}), "
            f"button_status=0b{button_status:08b}"
        )
        if frame:
            print("[UART HEX]", " ".join(f"{b:02X}" for b in frame),
                  f"(len={len(frame)})")

        # 7. 上面是在检测+debug,当真的有串口时发送整帧（header + PC_Msg）
        if ser is not None and frame:
            try:
                ser.write(frame)
            except serial.SerialException as e:
                print("⚠ 写串口失败，之后不再发送", e)
                ser = None

        clock.tick(30)


    # ====== 收尾 ====== 
    if ser is not None:
        ser.close()
    pygame.quit()
    print("程序已正常退出")
    sys.exit()


def main_menu():
    while True:
        gamepad_all_2()


if __name__ == "__main__":
    main_menu()
