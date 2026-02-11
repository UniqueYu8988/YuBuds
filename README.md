# 🎧 YuBuds - 小米智能音频眼镜 PC 端电量管家

![YuBuds Preview](screenshots/preview.png)

![YuBuds Logic](https://img.shields.io/badge/Status-Stable-success?style=for-the-badge&logo=googleshell&logoColor=white)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-blue?style=for-the-badge&logo=python&logoColor=white)
![Windows Only](https://img.shields.io/badge/Platform-Windows-0078D6?style=for-the-badge&logo=windows&logoColor=white)

**YuBuds** 是一款专为 **小米智能音频眼镜 (Mijia Smart Audio Glasses)** 开发的 Windows 桌面增强工具。它优雅地解决了 PC 端无法直观查看眼镜电量的痛点，提供实时电量监控与便捷的系统控制入口。

---

## ✨ 核心特性

- **💎 极致视觉**：胶囊型半透明玻璃拟态 (Glassmorphism) UI，完美融合现代桌面审美。
- **🔋 实时补给**：通过 Windows 蓝牙深度容器扫描策略，精准获取电量百分比，实时同步。
- **⚡ 快捷控制**：点点鼠标即可快速跳转蓝牙管理与麦克风设置，不再迷失在控制面板中。
- **🧠 位置记忆**：支持随处拖拽，并能记住你上次放置的位置，下次启动依然在“老地方”。
- **🚀 隐身启动**：内置 VBS 启动脚本，实现无黑框后台运行，默认支持开机自启。

---

## 🛠️ 技术原理

YuBuds 并不只是一个简单的界面，它背后有着精妙的设计：

1.  **异步通信 (`asyncio`)**：采用非阻塞式蓝牙扫描逻辑，确保 UI 界面始终丝滑顺畅，绝不卡顿。
2.  **深度容器关联 (`ContainerId`)**：针对 Windows 蓝牙节点复杂的特点，通过关联物理容器 ID，从逻辑节点中提取隐藏的电池数据。
3.  **跨线程通信 (`pyqtSignal`)**：后台扫描线程与前台 UI 线程完美解耦，数据交互安全稳定。

---

## 📦 快速开始

### 环境依赖

- Windows 10/11
- Python 3.10+
- 依赖库：`PyQt6`, `qtawesome`, `winsdk`

### 安装步骤

1. 克隆本项目：
   ```bash
   git clone https://github.com/YourUsername/YuBuds.git
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 运行程序：
   - **推荐方案**：双击 `启动_YuBuds(无黑框).vbs`（最佳体验，无命令行窗口）。
   - **调试方案**：直接运行 `python main.py`。

---

## 💡 开发背景

> “为了预防需要的时候耳机电量不足，我设计了 YuBuds。它不仅能让我提前关注到电量及时充电，更为小米智能眼镜在 PC 端的日常使用带来了质的飞跃。” —— **Yu**

---

## 📄 开源协议

本项目采用 [MIT License](LICENSE) 许可协议。

---

_Made with ❤️ by Yu._
