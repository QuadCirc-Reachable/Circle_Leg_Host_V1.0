# Circle_Leg_Host — Gamepad-to-UART Bridge for the REACHABLE Wheelchair

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.8%2B-blue?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/pygame-2.6-green" alt="pygame">
  <img src="https://img.shields.io/badge/pyserial-3.5-lightgrey" alt="pyserial">
  <img src="https://img.shields.io/badge/Platform-Windows%20%7C%20Linux%20(Jetson)-informational" alt="Platform">
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License">
</p>

<p align="center">
  <a href="#overview">English</a> | <a href="#项目概述">中文</a>
</p>

Host-side operator link for the **REACHABLE (QuadCirc)** CircLeg wheel-leg wheelchair. It reads an
Xbox gamepad, packs every stick, trigger, button and D-pad state into the firmware's `PC_Msg`, and
streams it to the STM32 chassis controller over a 2 Mbit/s UART. It runs headless on the vehicle's
Jetson Orin Nano. HKUST Final Year Design Project SL05a-25.

> **Superseded by [Circle_Leg_Host_V2.0](https://github.com/QuadCirc-Reachable/Circle_Leg_Host_V2.0).**
> V2.0 keeps this bridge's protocol byte-for-byte, restructures it into a tested package and adds
> optional RealSense curb vision. This single-script version is kept for reference, and commit
> `7adb072` is the one to use with the half-size V1 firmware.

---

## Overview

- **Protocol-exact**: builds the same RosComm frame the firmware parses (SOF, length, protocol ID,
  two CRC16 checks) with a 14-byte little-endian payload, sent at 30 Hz.
- **Robust link**: serial-port auto-detection with a preferred port, reconnection every 2 s,
  handling of USB-serial drop-outs, and an MCU liveness watchdog. It stops sending after 1 s
  without replies and forces a reconnect after 8 s.
- **Robust gamepad**: waits for a controller, detects unplugging and rescans, and survives
  occasional pygame event errors.
- **Two run modes**: headless for deployment, or a pygame window showing the sticks, triggers,
  buttons and link state.
- **Per-OS mapping**: Windows (XInput) and Linux (xpadneo / SDL) button and axis layouts.

| Repository | Content |
|------------|---------|
| [Circle_Leg_V2.0](https://github.com/QuadCirc-Reachable/Circle_Leg_V2.0) | Full-size firmware (consumes this bridge's 14-byte `PC_Msg`) |
| [Circle_Leg_V1.0](https://github.com/QuadCirc-Reachable/Circle_Leg_V1.0) | Half-size firmware (13-byte `PC_Msg`, see [compatibility](#firmware-compatibility--固件兼容性)) |
| [Circle_Leg_Host_V2.0](https://github.com/QuadCirc-Reachable/Circle_Leg_Host_V2.0) | Current host: gamepad link + optional curb vision |
| **Circle_Leg_Host_V1.0** (this repo) | Previous single-script gamepad → UART bridge |

---

## 项目概述

<details>
<summary>点击展开中文说明</summary>

REACHABLE（QuadCirc）CircLeg 轮腿轮椅的上位机操控链路：用 pygame 读取 Xbox 手柄，把摇杆、扳机、按键和
D-pad 状态打包成固件的 `PC_Msg`，通过 2 Mbit/s 串口发送给 STM32 底盘控制器。部署时以无界面（headless）
模式运行在车载 Jetson Orin Nano 上。

- **协议一致**：与固件解析的 RosComm 帧完全相同（帧头、长度、协议 ID、两级 CRC16），14 字节小端载荷，30 Hz 发送。
- **链路稳健**：串口自动识别（可预设端口）、每 2 s 自动重连、处理 USB 转串口掉线；MCU 心跳看门狗：1 s 无回包
  暂停发送，8 s 无回包强制重连。
- **手柄稳健**：等待手柄连接、拔出后自动重新扫描、容忍 pygame 偶发事件异常。
- **两种运行模式**：headless 部署模式，或显示摇杆 / 扳机 / 按键 / 连接状态的 pygame 可视化窗口。
- **按系统映射**：Windows（XInput）与 Linux（xpadneo / SDL）两套按键和轴映射。

</details>

---

## Demo | 演示

<p align="center">
  <a href="https://youtu.be/onJCvx1d8Sw">
    <img src="docs/demo_video.jpg" width="640" alt="REACHABLE pitch video on YouTube">
  </a>
</p>

<p align="center">
  ▶ <a href="https://youtu.be/onJCvx1d8Sw">Watch the REACHABLE pitch video on YouTube</a> · <a href="https://youtu.be/onJCvx1d8Sw">在 YouTube 观看项目视频</a>
</p>

---

## Architecture | 架构

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

## Getting Started | 快速开始

```bash
pip install -r requirements.txt      # pygame 2.6.1, pyserial 3.5
python main.py
```

Edit the constants at the top of `main.py`:

| Constant | Default | Meaning |
|----------|---------|---------|
| `PREFERRED_SERIAL_PORT` | `"/dev/ttyACM0"` | Port used directly in headless mode, e.g. `COM4` on Windows. Falls back to auto-detection if missing |
| `BAUD_RATE` | `2000000` | Must match the firmware's USART2 |
| `HEADLESS` | `True` | `True`: no window, console port menu with a 5 s timeout. `False`: pygame window with port picker and live visualisation |
| `OUTPUT_MODE` | `1` | `1`: normal output. `0`: print raw button IDs to build a new mapping |

On Linux, add your user to the `dialout` group for serial access. Xbox wireless controllers need
the `xpadneo` driver for the Linux mapping below. Exit with `ESC`. On Windows, gamepad button 8
also exits; it is disabled on Linux.

---

## Communication Protocol | 通信协议

```
| SOF 0xAA | len = 14 | ID 0xFF | CRC16(header) | payload (14 B) | CRC16(frame) |   → 21 bytes
```

The CRC16 is table-driven, with init `0xFFFF`, appended little-endian. The first CRC covers the
3-byte header and the second covers header + CRC + payload. It is ported from the firmware's `CRC.cpp`.

Payload (`struct.pack("<hHhHHHBB", ...)`, matches `Protocol::PC_Msg` in the firmware):

| Field | Type | Encoding |
|-------|------|----------|
| Left stick angle | int16 | deg × 10 (0–3600, counter-clockwise from +x), −1 when centred |
| Left stick radius | uint16 | 0–1000 |
| Right stick angle | int16 | deg × 10, −1 when centred |
| Right stick radius | uint16 | 0–1000 |
| LT / RT | uint16 | 0–1000 |
| `button_status` | uint8 | bit 0 LB · 1 RB · 2 X · 3 A · 4 B · 5 Y · 6 ML (View) · 7 MR (Menu) |
| `dpad_status` | uint8 | bit 0 Up · 1 Down · 2 Left · 3 Right |

Stick deadzone is 0.15. Triggers are normalised from pygame's −1…1 range to 0…1000.

### Gamepad mapping | 手柄映射

| Logical | Windows button / axis | Linux (xpadneo) button / axis |
|---------|----------------------|-------------------------------|
| A · B · X · Y | 0 · 1 · 2 · 3 | 0 · 1 · 2 · 3 |
| LB · RB | 4 · 5 | 4 · 5 |
| ML (View) · MR (Menu) | 6 · 7 | 6 · 7 |
| Left stick X / Y | axis 0 / 1 | axis 0 / 1 |
| Right stick X / Y | axis 2 / 3 | axis 3 / 4 |
| LT · RT | axis 4 · 5 | axis 2 · 5 |

What each input does on the wheelchair (modes, ride-height presets, speed tiers, climbing trigger)
is documented in the firmware READMEs.

### Firmware compatibility | 固件兼容性

| Host version | Payload | Firmware |
|--------------|---------|----------|
| `80bce10` and later (current) | 14 bytes (adds `dpad_status`) | Circle_Leg_V2 |
| `cb1623c` … `7adb072` | 13 bytes | Circle_Leg_V1 |

For the half-size prototype: `git checkout 7adb072`.

---

## Repository Structure | 目录结构

```
Circle_Leg_Host_V1.0/
├── main.py                  # The bridge: port selection, gamepad loop, framing, reconnect, UI
├── requirements.txt         # pygame, pyserial
├── test/                    # Gamepad / serial diagnostics used during bring-up
│   ├── check_joystick.py    # List connected controllers
│   ├── check_joystick_v2.py # Windowed joystick diagnosis tool
│   ├── test_gamepad.py      # Menu-driven gamepad tests (buttons, sticks, triggers, all-in-one)
│   └── test2.py             # Early UART packing prototype (fixed port)
└── LICENSE
```

---

## Team | 团队

REACHABLE (QuadCirc), HKUST FYP SL05a-25: LIU Hualin (embedded control lead), FANG Ruoyun
(perception & HMI), WU Ziyao (mechanical architecture & communication), XU Jusen (mechanical lead).
See the commit history for individual contributions.

## License

[MIT](LICENSE)
