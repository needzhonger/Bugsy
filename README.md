# Bugsy 项目 🐞 - 你的智能代码纠错助手
欢迎来到 Bugsy 项目！这是一个基于 AI 的代码纠错器，致力于帮助同学更好地对编程作业进行debug，或帮助开发者快速发现并修复代码中的错误和潜在问题。无论你是初学者还是经验丰富的程序员，Bugsy 都能成为你可靠的编程搭档，让编程更安心、更高效。

## ✨ 主要特性
* **🔍 智能错误检测**
Bugsy 支持多种编程语言（当前支持 C++，未来计划扩展到 Python、JavaScript 等），自动分析代码中的语法错误、逻辑问题和潜在的反模式。

* **🧠 AI 纠错建议**
基于大模型的自然语言理解能力，Bugsy 能给出具体可行的修改建议，或直接生成修改后的代码片段，帮助用户快速修复问题。

* **💬 交互式修复流程**
错误提示不再是冷冰冰的报错信息——Bugsy 提供类聊天式交互，解释问题原因，提供修改选项，让用户可以像与助教对话一样解决问题。

* **📎 多输入方式支持**
Bugsy 支持三种主要输入方式：

  * 直接复制粘贴题目描述和代码片段

  * 上传题目描述和代码截图

  * 直接上传代码文件（如 .py、.cpp 等）

* **⏱️ 快速响应 & 轻量体验**
通过流式响应机制，Bugsy 在短时间内即可完成分析和建议，提升用户使用体验。

## 📂 项目结构概览
```
Bugsy/
├── core/                         # 核心功能模块
│   ├── AgentCamel.py             # Camel AI 接口
│   ├── AgentSiliconFlow.py       # 硅基流动 AI 接口
│   ├── ChatWindow.py             # 聊天框
│   ├── common.py                 # 环境配置
│   ├── FontSetting.py            # 字体设置
│   ├── MainWindow.py             # 主界面
│   ├── SideBar.py                # 侧边栏
│   ├── Signals.py                # 信号
│   ├── __init__.py               # 初始化文件，表明core是个包
│   └── API_KEY.env               # api密钥
├── Pet/                          # 桌宠模块功能
│   ├── data                      # 用于存放数据
│   ├── res                       # 资源文件
│   ├── __init__.py               # 初始化文件，表明Pet是个包
│   ├── conf.py                   # 定义宠物配置、动作和状态数据的类。
│   ├── module.py                 # 处理宠物的各项功能
│   ├── Pet.py                    # 宠物核心 UI 模块
│   ├── setting.py                # 初始化应用程序所需的全局状态变量
│   └── utils.py                  # 存放常用的工具函数
├── requirements.txt              # 环境要求
├── run_bugsy.py                  # 启动入口
└── README.md                     # 项目说明文件
```

## 🚀 快速开始
1.  **环境配置**：
    *   确保你已安装Python。项目代码中使用了 f-string、类型提示等特性，推荐 **Python 3.10 及以上版本**

    *   安装项目依赖：
        可以选择直接使用项目配备的requirements.txt文件：
        ```bahs
        pip install -r requirements.txt
        ```
        或依次手动安装以下各库：
        *   **PySide6**: 用于构建图形用户界面（GUI）。
            ```bash
            pip install PySide6
            ```

        *   **camel-ai**: 用于调用大模型API，实现智能交互功能。
            ```bash
            pip install git+https://github.com/camel-ai/camel.git@main#egg=camel-ai
            ```
     
        *   **dotenv**: 用于管理和加载项目中的环境变量配置，安全存储敏感信息。
            ```bash
            pip install python-dotenv
            ```
     
        *   **colorama**: 用于在命令行界面输出彩色文本，提升信息的可读性和用户体验。
            ```bash
            pip install colorama
            ```


2.  **启动应用**：

    *   **先在API_KEY.env文件中输入API密钥**
    *   然后运行run_bugsy.py程序
        ```bash
        python run_Main_Window.py
        ```
    *   启动后，桌宠 *Doggy* 将出现在桌面，你可以通过左键点击 *Doggy* 以进入debug界面，也可以右键 *Doggy* 或右键托盘图标打开宠物菜单，点击 **“救救我”** 选项以进入相同的debug界面。
    *   宠物菜单中还有其他功能如 **“切换角色”** ， **“选择动作”** 等
    *   想要退出 Bugsy，只需要右键 *Doggy* 或右键托盘图标， 在宠物菜单中点击 **“退出”** 选项即可


## 🛠️ 技术选型
*   **编程语言**：Python 3.10+
*   **模型支持**：Deepseek R1
*   **分析方式**：
*   **图像处理**：
*   **依赖库**  ：PySide6、camel-ai、dotenv、colorama等

## 📝 注意事项
*   当前版本主要支持 C++ 脚本的错误分析和修复。

*   大模型调用需配置 API Key。

## 🔭 展望未来

#我们计划在未来为 Bugsy 添加更多实用功能：

*   🌐 **Web UI**：构建直观可视化的图形界面

*   🧩 **VS Code 插件**：无缝集成开发环境

*   📊 **错误知识库**：构建常见错误和解决方案数据库

*   💡 **教学模式**：适用于教学场景，解释每次修改的原因与知识点

*   🤖 **本地模型支持**：打造无需联网也能运行的 AI 纠错助手

## 🧑‍💻 开发团队
*   （请在此处填写开发团队或个人信息）

---
