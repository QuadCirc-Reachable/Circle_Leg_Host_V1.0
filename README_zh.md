# Circle_Leg_Host — REACHABLE 轮椅的手柄转串口上位机

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/pygame-2.6-green" alt="pygame">
  <img src="https://img.shields.io/badge/pyserial-3.5-lightgrey" alt="pyserial">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20(Jetson)-informational" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

<p align="center">
  <a href="README.md">English</a> | <b>中文</b>
</p>

**REACHABLE（QuadCirc）** CircLeg 轮腿轮椅的上位机操控链路：读取 Xbox 手柄，把摇杆、扳机、按键和
D-pad 状态打包成固件的 `PC_Msg`，通过 2 Mbit/s 串口发送给 STM32 底盘控制器。部署时以无界面模式
运行在车载 Jetson Orin Nano 上。香港科技大学毕业设计项目 SL05a-25。

> **已由 [Circle_Leg_Host_V2.0](https://github.com/QuadCirc-Reachable/Circle_Leg_Host_V2.0) 取代。**
> 2.0 版完整保留了本仓库的协议（字节级一致），把它重构成带测试的 Python 包，并加入了可选的
> RealSense 台阶视觉。本单文件版本作为参考保留；配合半尺寸 V1 固件时，请使用 `7adb072` 这个提交。

---

## 项目概述

- **协议一致**：生成与固件解析完全相同的 RosComm 帧（帧头、长度、协议 ID、两级 CRC16），
  14 字节小端载荷，30 Hz 发送。
- **链路稳健**：串口自动识别（可预设端口）、每 2 s 自动重连、处理 USB 转串口掉线，以及 MCU 心跳
  看门狗：1 s 无回包暂停发送，8 s 无回包强制重连。
- **手柄稳健**：等待手柄连接、拔出后自动重新扫描，并容忍 pygame 偶发的事件异常。
- **两种运行模式**：部署用的无界面模式，或显示摇杆 / 扳机 / 按键 / 连接状态的 pygame 窗口。
- **按系统映射**：Windows（XInput）与 Linux（xpadneo / SDL）两套按键和轴映射。

| 仓库 | 内容 |
|------|------|
| [Circle_Leg_V2.0](https://github.com/QuadCirc-Reachable/Circle_Leg_V2.0) | 全尺寸固件（使用本桥接的 14 字节 `PC_Msg`） |
| [Circle_Leg_V1.0](https://github.com/QuadCirc-Reachable/Circle_Leg_V1.0) | 半尺寸固件（13 字节 `PC_Msg`，见[兼容性](#固件兼容性)） |
| [Circle_Leg_Host_V2.0](https://github.com/QuadCirc-Reachable/Circle_Leg_Host_V2.0) | 当前上位机：手柄链路 + 可选台阶视觉 |
| **Circle_Leg_Host_V1.0**（本仓库） | 旧版单文件手柄 → 串口桥接 |

---

## 演示

<p align="center">
  <a href="https://youtu.be/onJCvx1d8Sw">
    <img src="docs/demo_video.jpg" width="640" alt="REACHABLE 项目视频（YouTube）">
  </a>
</p>

<p align="center">
  ▶ <a href="https://youtu.be/onJCvx1d8Sw">在 YouTube 观看 REACHABLE 项目视频</a>
</p>

---

## 架构

```
┌────────────────────┐ USB / BT ┌──────────────────────────── main.py ─────────────────────────────┐
│ Xbox controller    │ ───────► │ pygame read → deadzone / normalize → PC_Msg (14 B, struct.pack)   │
└────────────────────┘          │      → RosComm frame [SOF|len|ID|CRC16|payload|CRC16] (21 B)      │
                                │      → pyserial @ 2 Mbit/s, 30 Hz        ◄── MCU replies (liveness) │
                                └───────────────────────────────┬───────────────────────────────────┘
                                                                │ CH343 USB-UART
                                                                ▼
                                          STM32G473 USART2 → PC_Comm → Chassis (500 Hz)
```

---

## 快速开始

```bash
pip install -r requirements.txt      # pygame 2.6.1, pyserial 3.5
python main.py
```

修改 `main.py` 顶部的常量：

| 常量 | 默认值 | 含义 |
|------|--------|------|
| `PREFERRED_SERIAL_PORT` | `"/dev/ttyACM0"` | 无界面模式下直接使用的端口，Windows 上例如 `COM4`；端口不存在时回退到自动扫描 |
| `BAUD_RATE` | `2000000` | 必须与固件的 USART2 一致 |
| `HEADLESS` | `True` | `True`：不开窗口，命令行选口菜单 5 s 超时；`False`：pygame 窗口，可选口并实时可视化 |
| `OUTPUT_MODE` | `1` | `1`：正常输出；`0`：打印原始按键 ID，用于制作新的映射表 |

Linux 上需要把用户加入 `dialout` 组才能访问串口；Xbox 无线手柄需要 `xpadneo` 驱动才符合下面的
Linux 映射。按 `ESC` 退出；Windows 上手柄按键 8 也可退出，Linux 上该功能已禁用。

---

## 通信协议

```
| SOF 0xAA | len = 14 | ID 0xFF | CRC16(header) | payload (14 B) | CRC16(frame) |   → 21 bytes
```

CRC16 为查表实现，初值 `0xFFFF`，以小端追加。第一个 CRC 覆盖 3 字节帧头，第二个覆盖
帧头 + CRC + 载荷。该实现移植自固件的 `CRC.cpp`。

载荷（`struct.pack("<hHhHHHBB", ...)`，与固件中的 `Protocol::PC_Msg` 对应）：

| 字段 | 类型 | 编码 |
|------|------|------|
| 左摇杆角度 | int16 | 角度 × 10（0–3600，从 +x 轴逆时针），回中时为 −1 |
| 左摇杆幅度 | uint16 | 0–1000 |
| 右摇杆角度 | int16 | 角度 × 10，回中时为 −1 |
| 右摇杆幅度 | uint16 | 0–1000 |
| LT / RT | uint16 | 0–1000 |
| `button_status` | uint8 | bit 0 LB · 1 RB · 2 X · 3 A · 4 B · 5 Y · 6 ML（View）· 7 MR（Menu） |
| `dpad_status` | uint8 | bit 0 上 · 1 下 · 2 左 · 3 右 |

摇杆死区为 0.15；扳机由 pygame 的 −1…1 归一化到 0…1000。

### 手柄映射

| 逻辑按键 | Windows 按键 / 轴 | Linux（xpadneo）按键 / 轴 |
|----------|-------------------|---------------------------|
| A · B · X · Y | 0 · 1 · 2 · 3 | 0 · 1 · 2 · 3 |
| LB · RB | 4 · 5 | 4 · 5 |
| ML（View）· MR（Menu） | 6 · 7 | 6 · 7 |
| 左摇杆 X / Y | 轴 0 / 1 | 轴 0 / 1 |
| 右摇杆 X / Y | 轴 2 / 3 | 轴 3 / 4 |
| LT · RT | 轴 4 · 5 | 轴 2 · 5 |

每个输入在轮椅上的具体功能（模式切换、高度预设、速度档、攀爬触发）见固件仓库的 README。

### 固件兼容性

| 上位机版本 | 载荷 | 对应固件 |
|------------|------|----------|
| `80bce10` 及之后（当前） | 14 字节（新增 `dpad_status`） | Circle_Leg_V2 |
| `cb1623c` … `7adb072` | 13 字节 | Circle_Leg_V1 |

配合半尺寸原型使用时：`git checkout 7adb072`。

---

## 目录结构

```
Circle_Leg_Host_V1.0/
├── main.py                  # 主程序：选口、手柄循环、组帧、重连、可视化
├── requirements.txt         # pygame, pyserial
├── test/                    # 调试期用的手柄 / 串口诊断脚本
│   ├── check_joystick.py    # 列出已连接的手柄
│   ├── check_joystick_v2.py # 带窗口的手柄诊断工具
│   ├── test_gamepad.py      # 菜单式手柄测试（按键、摇杆、扳机、综合）
│   └── test2.py             # 早期的串口打包原型（固定端口）
└── LICENSE
```

---

## 团队

REACHABLE（QuadCirc），香港科技大学毕业设计项目 SL05a-25：LIU Hualin（嵌入式控制负责人）、
FANG Ruoyun（感知与人机交互）、WU Ziyao（机械架构与通信）、XU Jusen（机械负责人）。
各人的具体贡献见提交历史。

## 许可证

[MIT](LICENSE)
