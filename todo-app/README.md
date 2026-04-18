# 个人效率小工具 - Electron & Vue 版本

## 项目结构

```
todo-app/
├── electron/           # Electron 主进程代码
│   ├── main.js        # 主进程入口
│   └── preload.js     # 预加载脚本
├── src/               # Vue 前端代码
│   ├── App.vue        # 主组件
│   └── main.js        # Vue 入口
├── public/            # 静态资源
├── index.html         # HTML 模板
├── package.json       # 项目配置
└── vite.config.js     # Vite 配置
```

## 功能特性

1. **IP 地址显示** - 显示本机所有 IPv4 地址，支持一键复制
2. **待办事项** - 添加、删除、完成待办，数据本地存储
3. **备忘录** - 文本备忘录，自动保存
4. **快捷启动** - 添加和管理常用程序快捷方式
5. **Git 日志查询** - 查询指定作者在时间范围内的提交文件

## 安装依赖

```bash
cd todo-app
npm install
```

## 开发模式

```bash
# 仅运行 Vue 前端（浏览器）
npm run dev

# 运行 Electron 桌面应用（需要先安装依赖）
npm run electron:dev
```

## 构建可执行文件

### 构建 Windows EXE

```bash
npm run electron:build:win
```

构建完成后，可执行文件位于 `dist-electron/` 目录。

### 构建当前平台

```bash
npm run electron:build
```

## 注意事项

1. 由于磁盘空间限制，当前环境可能无法完成完整构建
2. 建议在本地有足够空间的机器上运行构建命令
3. Windows 构建需要 Wine 或直接在 Windows 系统上执行

## 技术栈

- **前端**: Vue 3 + Vite
- **桌面框架**: Electron
- **打包工具**: electron-builder
- **样式**: 原生 CSS (渐变背景、卡片式设计)
