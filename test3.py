import pygame
import math
import sys
import serial   
import struct 

"""
README:
    - 这个脚本用 pygame 读取 Xbox 手柄数据，并把数据打包成特定格式通过 UART 发送出去
    - 协议格式已适配 RosComm.cpp 驱动：
      [Header(3)] + [HeaderCRC(2)] + [Payload(13)] + [PayloadCRC(2)] = 20 Bytes
    - 修正：Left Trigger (LT) 和 Right Trigger (RT) 的范围现在是 0-1000。
    - 记得先安装库：pip install pygame pyserial
    - 运行前请修改 SERIAL_PORT 为实际串口号
"""

SERIAL_PORT = "COM10"     # 开发板时改成实际串口号，比如"/dev/ttyUSB0"
#/dev/ttyACM0
BAUD_RATE   = 2000000
OUTPUT_MODE = 1         # 1: 正常输出逻辑和HEX; 0: 调试模式，输出检测到的原始按钮ID

# ==============================================================================
# CRC16 Implementation (移植自 CRC.cpp)
# ==============================================================================
wCRC_Table = [
    0x0000, 0x1189, 0x2312, 0x329b, 0x4624, 0x57ad, 0x6536, 0x74bf, 0x8c48, 0x9dc1, 0xaf5a, 0xbed3, 0xca6c, 0xdbe5, 0xe97e, 0xf8f7, 
    0x1081, 0x0108, 0x3393, 0x221a, 0x56a5, 0x472c, 0x75b7, 0x643e, 0x9cc9, 0x8d40, 0xbfdb, 0xae52, 0xdaed, 0xcb64, 0xf9ff, 0xe876, 
    0x2102, 0x308b, 0x0210, 0x1399, 0x6726, 0x76af, 0x4434, 0x55bd, 0xad4a, 0xbcc3, 0x8e58, 0x9fd1, 0xeb6e, 0xfae7, 0xc87c, 0xd9f5, 
    0x3183, 0x200a, 0x1291, 0x0318, 0x77a7, 0x662e, 0x54b5, 0x453c, 0xbdcb, 0xac42, 0x9ed9, 0x8f50, 0xfbef, 0xea66, 0xd8fd, 0xc974, 
    0x4204, 0x538d, 0x6116, 0x709f, 0x0420, 0x15a9, 0x2732, 0x36bb, 0xce4c, 0xdfc5, 0xed5e, 0xfcd7, 0x8868, 0x99e1, 0xab7a, 0xbaf3, 
    0x5285, 0x430c, 0x7197, 0x601e, 0x14a1, 0x0528, 0x37b3, 0x263a, 0xdecd, 0xcf44, 0xfddf, 0xec56, 0x98e9, 0x8960, 0xbbfb, 0xaa72, 
    0x6306, 0x728f, 0x4014, 0x519d, 0x2522, 0x34ab, 0x0630, 0x17b9, 0xef4e, 0xfec7, 0xcc5c, 0xddd5, 0xa96a, 0xb8e3, 0x8a78, 0x9bf1, 
    0x7387, 0x620e, 0x5095, 0x411c, 0x35a3, 0x242a, 0x16b1, 0x0738, 0xffcf, 0xee46, 0xdcdd, 0xcd54, 0xb9eb, 0xa862, 0x9af9, 0x8b70, 
    0x8408, 0x9581, 0xa71a, 0xb693, 0xc22c, 0xd3a5, 0xe13e, 0xf0b7, 0x0840, 0x19c9, 0x2b52, 0x3adb, 0x4e64, 0x5fed, 0x6d76, 0x7cff, 
    0x9489, 0x8500, 0xb79b, 0xa612, 0xd2ad, 0xc324, 0xf1bf, 0xe036, 0x18c1, 0x0948, 0x3bd3, 0x2a5a, 0x5ee5, 0x4f6c, 0x7df7, 0x6c7e, 
    0xa50a, 0xb483, 0x8618, 0x9791, 0xe32e, 0xf2a7, 0xc03c, 0xd1b5, 0x2942, 0x38cb, 0x0a50, 0x1bd9, 0x6f66, 0x7eef, 0x4c74, 0x5dfd, 
    0xb58b, 0xa402, 0x9699, 0x8710, 0xf3af, 0xe226, 0xd0bd, 0xc134, 0x39c3, 0x284a, 0x1ad1, 0x0b58, 0x7fe7, 0x6e6e, 0x5cf5, 0x4d7c, 
    0xc60c, 0xd785, 0xe51e, 0xf497, 0x8028, 0x91a1, 0xa33a, 0xb2b3, 0x4a44, 0x5bcd, 0x6956, 0x78df, 0x0c60, 0x1de9, 0x2f72, 0x3efb, 
    0xd68d, 0xc704, 0xf59f, 0xe416, 0x90a9, 0x8120, 0xb3bb, 0xa232, 0x5ac5, 0x4b4c, 0x79d7, 0x685e, 0x1ce1, 0x0d68, 0x3ff3, 0x2e7a, 
    0xe70e, 0xf687, 0xc41c, 0xd595, 0xa12a, 0xb0a3, 0x8238, 0x93b1, 0x6b46, 0x7acf, 0x4854, 0x59dd, 0x2d62, 0x3ceb, 0x0e70, 0x1ff9, 
    0xf78f, 0xe606, 0xd49d, 0xc514, 0xb1ab, 0xa022, 0x92b9, 0x8330, 0x7bc7, 0x6a4e, 0x58d5, 0x495c, 0x3de3, 0x2c6a, 0x1ef1, 0x0f78
]

def get_crc16_checksum(data, init=0xFFFF):
    """计算数据的 CRC16"""
    crc = init
    for byte in data:
        crc = (crc >> 8) ^ wCRC_Table[(crc ^ byte) & 0x00ff]
    return crc

def append_crc16_checksum(data):
    """计算 CRC 并追加到数据末尾 (小端序)"""
    crc = get_crc16_checksum(data, 0xFFFF)
    return data + struct.pack("<H", crc)

# ==============================================================================
# Main Logic
# ==============================================================================

def draw_text(surface, text, x, y, size=20, color=(255, 255, 255)):
    font = pygame.font.SysFont("Arial", size)
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def gamepad_all_2():
    pygame.init()
    pygame.joystick.init()
    pygame.font.init()

    # --- Window Setup ---
    WIDTH, HEIGHT = 800, 500
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Robot Controller Host")

    # --- 等待手柄连接 ---
    print("正在扫描手柄... (请连接手柄)")
    while pygame.joystick.get_count() == 0:
        pygame.event.pump()
        pygame.time.wait(500)  # 每500ms检查一次
        
        # 绘制扫描界面
        screen.fill((30, 30, 30))
        draw_text(screen, "Scanning for Gamepad...", WIDTH//2 - 100, HEIGHT//2, 30)
        draw_text(screen, "Please connect a controller", WIDTH//2 - 100, HEIGHT//2 + 40, 20)
        pygame.display.flip()

        # 允许用户在等待时退出
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                sys.exit()

    # 连接第一个手柄
    js = pygame.joystick.Joystick(0)
    js.init()
    print(f"✅ 已连接手柄: {js.get_name()}")
    
    if OUTPUT_MODE == 1:
        print("当前模式: 1 (正常输出)")
        print("输出：LA,LM, RA,RM, LT,RT, bottom（Angle×10，Mag/LT/RT×1000）")
    else:
        print("当前模式: 0 (调试映射)")
        print("请按下手柄按钮，屏幕将显示其原始ID")

    print("提示：按手柄 BACK 键 或 键盘 ESC 退出")

    # 尝试打开串口（打开失败就只做 print）
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
        print(f"串口 {SERIAL_PORT} 打开成功，将同步发送 UART 数据")
    except serial.SerialException as e:
        print(f"⚠ 串口 {SERIAL_PORT} 打不开，只做 print", e)
        ser = None   # 标记为“没有串口”

    clock = pygame.time.Clock()
    
    last_reconnect_time = 0
    RECONNECT_INTERVAL = 2000  # 2秒重连尝试间隔

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

        # ====== 处理事件：按钮 / 退出 / 手柄热插拔 ====== 
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                sys.exit() # 直接退出

            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                running = False
                sys.exit()

            # 检测手柄断开 (Pygame 2.0+)
            if event.type == pygame.JOYDEVICEREMOVED:
                # 检查是否是当前使用的手柄断开了
                # event.instance_id 是 Joystick 的 instance_id，需要对比
                if event.instance_id == js.get_instance_id():
                    print("⚠ 手柄已断开连接！正在返回重新扫描...")
                    running = False # 退出当前循环，触发外层 main_menu 重新调用 gamepad_all_2
                    break

            if event.type == pygame.JOYBUTTONDOWN:
                # BACK 键（一般是 6 或 8，视手柄而定，这里保留原代码的 8）退出
                if event.button == 8:
                    print("收到退出指令（Back 键），结束程序")
                    running = False
                    break

                if OUTPUT_MODE == 0:
                    print(f"【DEBUG模式】检测到原始按钮ID: {event.button}")

                if event.button in button_map:
                    bottom = button_map[event.button]  
                    if OUTPUT_MODE == 1:
                        print(f"逻辑按钮 {bottom} 按下（物理 {event.button}）")  #监控/debug用
                else:
                    if OUTPUT_MODE == 1:
                        print(f"其他按钮 {event.button} 按下")  #监控/debug用

                if event.type == pygame.JOYBUTTONUP:
                    if event.button in button_map:
                        any_down = False
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

        # ====== LT / RT (修改为 0-1000) ====== 
        lt_raw = js.get_axis(4)
        rt_raw = js.get_axis(5)

        # Pygame 中 Trigger 初始是 -1.0，按下是 1.0。这里归一化到 0.0 ~ 1.0
        lt_norm = (lt_raw + 1) / 2.0
        rt_norm = (rt_raw + 1) / 2.0
        lt_norm = max(0.0, min(1.0, lt_norm))
        rt_norm = max(0.0, min(1.0, rt_norm))

        # 映射到 0-1000
        LT = int(round(lt_norm * 1000))
        RT = int(round(rt_norm * 1000))

        # ====== “协议 + 调试输出”部分 ======
        left_r_1000  = max(0, min(1000, LM * 10))   # 左摇杆半径 (0-1000)
        right_r_1000 = max(0, min(1000, RM * 10))   # 右摇杆半径 (0-1000)

        # 2. LT / RT (确保不超限)
        LT_val = max(0, min(1000, LT))  # 左扳机 0-1000
        RT_val = max(0, min(1000, RT))  # 右扳机 0-1000

        # 1. 手柄按键 ID 定义 (这是 Pygame/手柄驱动读取到的物理按键编号，保持不变)
        BTN_A_ID  = 0
        BTN_B_ID  = 1
        BTN_X_ID  = 2
        BTN_Y_ID  = 3
        BTN_LB_ID = 4     
        BTN_RB_ID = 5     
        BTN_ML_ID = 6  
        BTN_MR_ID = 7     

        # 2. 生成 button_status
        
        button_status = 0
        
        # Bit 0: LB
        if js.get_button(BTN_LB_ID): button_status |= (1 << 0)
        
        # Bit 1: RB
        if js.get_button(BTN_RB_ID): button_status |= (1 << 1)
        
        # Bit 2: X
        if js.get_button(BTN_X_ID):  button_status |= (1 << 2)
        
        # Bit 3: A
        if js.get_button(BTN_A_ID):  button_status |= (1 << 3)
        
        # Bit 4: B
        if js.get_button(BTN_B_ID):  button_status |= (1 << 4)
        
        # Bit 5: Y
        if js.get_button(BTN_Y_ID):  button_status |= (1 << 5)
        
        # Bit 6: ML (Menu Left)
        if js.get_button(BTN_ML_ID): button_status |= (1 << 6)
        
        # Bit 7: MR (Menu Right)
        if js.get_button(BTN_MR_ID): button_status |= (1 << 7)

        # 4. PC_Msg 结构体（13 字节，小端）
        try:
            payload = struct.pack(
                "<hHhHHHB",
                LA,            # 左摇杆角度×10
                left_r_1000,   # 左摇杆半径×1000
                RA,            # 右摇杆角度×10
                right_r_1000,  # 右摇杆半径×1000
                LT_val,        # Left_trigger_x1000_msg (0-1000)
                RT_val,        # Right_trigger_x1000_msg (0-1000)
                button_status  # 按钮 bit
            )
        except struct.error as e:
            print("⚠ struct.pack 出错，检查数值范围：", e)
            payload = b""

        # 5. 构造完整帧 (适配 RosComm.cpp)
        # 结构: [Header(3)] + [HeaderCRC(2)] + [Payload(13)] + [PayloadCRC(2)]
        if payload:
            sof        = 0xAA
            protocolID = 0xFF  # 对应 PC_Comm.cpp 中的注册ID
            dataLen    = len(payload) # 13
            
            # 1. 构造 Header: 注意顺序是 sof, dataLen, protocolID (RosCommProtocol.hpp)
            header = struct.pack("<BBB", sof, dataLen, protocolID)
            
            # 2. 追加 Header CRC
            header_with_crc = append_crc16_checksum(header)
            
            # 3. 拼接 Payload
            frame_partial = header_with_crc + payload
            
            # 4. 追加 Payload CRC (对整个包计算)
            frame = append_crc16_checksum(frame_partial)
            
        else:
            frame = b""

        # 6. debug：打印逻辑值 + 真实发出去的 HEX
        if OUTPUT_MODE == 1:
            print(
                f"[LOGIC] LA={LA}, LM={LM}, RA={RA}, RM={RM}, "
                f"LT={LT_val}, RT={RT_val}, BTN={button_status:08b}"
            )
            if frame:
                # 应该打印 20 个字节
                print("[UART HEX]", " ".join(f"{b:02X}" for b in frame),
                      f"(len={len(frame)})")

        # 7. 发送串口数据
        current_time = pygame.time.get_ticks()

        # 如果串口断开，尝试重连
        if ser is None:
            if current_time - last_reconnect_time > RECONNECT_INTERVAL:
                last_reconnect_time = current_time
                try:
                    print(f"正在尝试重连串口 {SERIAL_PORT} ...")
                    ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=0.1)
                    print(f"串口 {SERIAL_PORT} 重连成功！")
                except serial.SerialException:
                    # 静默失败，等待下次重试
                    pass

        if ser is not None and frame:
            try:
                ser.write(frame)
            except serial.SerialException as e:
                print("⚠ 写串口失败，连接已断开", e)
                ser.close()
                ser = None

        # ====== Visualization ======
        screen.fill((30, 30, 30)) # Dark Grey Background

        # 1. Connection Status
        status_color = (0, 255, 0) if ser is not None else (255, 0, 0)
        status_text = f"Serial: {SERIAL_PORT} [{'CONNECTED' if ser else 'DISCONNECTED'}]"
        draw_text(screen, status_text, 20, 20, 24, status_color)
        draw_text(screen, f"Gamepad: {js.get_name()}", 20, 50, 20)
        draw_text(screen, f"Protocol: [HEAD] [CRC] [PAYLOAD] [CRC]", 20, HEIGHT - 30, 16, (150, 150, 150))

        # 2. Joysticks
        # Left Stick
        pygame.draw.circle(screen, (50, 50, 50), (150, 250), 60, 2)
        ls_x = 150 + int(x * 60)
        ls_y = 250 + int(y * 60)
        pygame.draw.circle(screen, (0, 150, 255), (ls_x, ls_y), 10)
        draw_text(screen, f"L-Stick: {LA/10:.1f}deg, {LM/100:.2f}", 90, 330, 18)

        # Right Stick
        pygame.draw.circle(screen, (50, 50, 50), (650, 250), 60, 2)
        rs_x = 650 + int(rx * 60)
        rs_y = 250 + int(ry * 60)
        pygame.draw.circle(screen, (0, 150, 255), (rs_x, rs_y), 10)
        draw_text(screen, f"R-Stick: {RA/10:.1f}deg, {RM/100:.2f}", 590, 330, 18)

        # 3. Triggers (Bars)
        # Left Trigger
        pygame.draw.rect(screen, (50, 50, 50), (100, 100, 30, 100), 2)
        pygame.draw.rect(screen, (255, 100, 0), (102, 200 - int(lt_norm * 96), 26, int(lt_norm * 96)))
        draw_text(screen, f"LT: {int(LT_val)}", 90, 80, 18)

        # Right Trigger
        pygame.draw.rect(screen, (50, 50, 50), (670, 100, 30, 100), 2)
        pygame.draw.rect(screen, (255, 100, 0), (672, 200 - int(rt_norm * 96), 26, int(rt_norm * 96)))
        draw_text(screen, f"RT: {int(RT_val)}", 660, 80, 18)

        # 4. Buttons
        center_x = 400
        center_y = 250
        
        # A, B, X, Y
        btn_positions = {
            'Y': (center_x + 100, center_y - 40),
            'B': (center_x + 140, center_y),
            'A': (center_x + 100, center_y + 40),
            'X': (center_x + 60, center_y)
        }
        
        # Check logic bits from button_status
        # BTN_A: bit 3, BTN_B: bit 4, BTN_X: bit 2, BTN_Y: bit 5
        # BTN_LB: bit 0, BTN_RB: bit 1
        # BTN_ML: bit 6, BTN_MR: bit 7
        
        is_pressed = lambda bit: (button_status & (1 << bit)) != 0
        
        cols = {True: (0, 255, 0), False: (80, 80, 80)}
        
        # Draw ABXY
        for name, pos in btn_positions.items():
            bit = {'A': 3, 'B': 4, 'X': 2, 'Y': 5}[name]
            pygame.draw.circle(screen, cols[is_pressed(bit)], pos, 15)
            draw_text(screen, name, pos[0]-5, pos[1]-10, 18, (0,0,0) if is_pressed(bit) else (200,200,200))

        # Bumpers
        pygame.draw.rect(screen, cols[is_pressed(0)], (100, 60, 60, 20)) # LB
        draw_text(screen, "LB", 115, 60, 16, (0,0,0))
        
        pygame.draw.rect(screen, cols[is_pressed(1)], (640, 60, 60, 20)) # RB
        draw_text(screen, "RB", 655, 60, 16, (0,0,0))

        # Menu Buttons (Start/Select)
        pygame.draw.circle(screen, cols[is_pressed(6)], (center_x - 40, center_y), 10) # ML (Select)
        draw_text(screen, "ML", center_x - 38, center_y + 15, 14, (200,200,200))

        pygame.draw.circle(screen, cols[is_pressed(7)], (center_x + 20, center_y), 10) # MR (Start)
        draw_text(screen, "MR", center_x + 22, center_y + 15, 14, (200,200,200))

        pygame.display.flip()
        
            try:
                ser.write(frame)
            except serial.SerialException as e:
                print("⚠ 写串口失败，连接已断开", e)
                ser.close()
                ser = None

        clock.tick(30)

    # ====== 收尾 ====== 
    if ser is not None:
        ser.close()
    
    # 尝试安全退出 pygame (只是清理本次 session 资源)
    try:
        pygame.quit()
    except:
        pass

    print("准备重启扫描手柄程序...")
    return

def main_menu():
    while True:
        try:
            gamepad_all_2()
        except KeyboardInterrupt:
            print("\n用户中断，退出程序")
            sys.exit()
        except Exception as e:
            print(f"发生错误: {e}")
            pass # 稍微等待避免过快循环
        
        # 简单等待
        import time
        time.sleep(1)

if __name__ == "__main__":
    main_menu()