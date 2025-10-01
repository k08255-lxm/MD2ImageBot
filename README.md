# MD2ImageBot

[![Build & Publish Docker](https://img.shields.io/github/actions/workflow/status/k08255-lxm/MD2ImageBot/docker.yml?branch=main)](https://github.com/k08255-lxm/MD2ImageBot/actions)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)
![Container](https://img.shields.io/badge/ghcr.io-md2imagebot-blue?logo=github)

一个把 **Markdown** 自动转换为 **图片** 的 Telegram 机器人，支持：

- 发送/回复 Markdown 文本，机器人返回渲染后的 PNG 图片
- 管理员控制：是否公开使用、黑名单/白名单、查看运行状态与统计
- 预留 **HTTP API** 与 **插件机制**，便于未来拓展（如：加入群组/频道后自动转换帖子）
- 一键脚本 `setup.sh`：下载依赖、安装浏览器、生成 `.env`、引导填写信息
- **CI 自动化**：push 即打包 Docker 镜像并发布到 GHCR（`ghcr.io/k08255-lxm/md2imagebot`）

> 渲染实现：Markdown → HTML（本地 CSS）→ 无头 Chromium 截图（Playwright）→ PNG。**不会加载外部资源**，安全可靠。

---

## 目录

- [快速开始（本地）](#快速开始本地)
- [Docker 运行](#docker-运行)
- [使用方法](#使用方法)
- [群组/频道自动转换（插件）](#群组频道自动转换插件)
- [HTTP API](#http-api)
- [配置](#配置)
- [运行状态与数据持久化](#运行状态与数据持久化)
- [开发](#开发)
- [许可](#许可)

---

## 快速开始（本地）

1. 向 **BotFather** 创建机器人，拿到 `BOT_TOKEN`。
2. 克隆本仓库并执行：

```bash
# 1) 下载并解压
owner="k08255-lxm"
repo="MD2ImageBot"
curl -L "https://github.com/$owner/$repo/archive/refs/heads/main.zip" -o main.zip
unzip main.zip
cd "${repo}-main"

# 2) 安装并启动
chmod +x setup.sh
./setup.sh
# 按提示填写 .env 配置

# 完成后执行：
source .venv/bin/activate
python -m src.main
```

> 首次运行会自动安装 Playwright 的 Chromium。

---

## Docker 运行

### 从 GHCR 拉取镜像

```bash
docker pull ghcr.io/k08255-lxm/md2imagebot:latest
```

### 准备环境变量

复制 `.env.example` 为 `.env` 并填写：

```
BOT_TOKEN=123456:ABC...
ADMIN_IDS=1111111,2222222
PUBLIC_ENABLED=true
API_HOST=0.0.0.0
API_PORT=8000
API_TOKEN=change-me
RENDER_WIDTH=1024
```

### 直接运行容器

```bash
mkdir -p storage

docker run -d --name md2imagebot   --env-file .env   -p 8000:8000   -v $(pwd)/storage:/app/storage   ghcr.io/k08255-lxm/md2imagebot:latest
```

> - API: `http://localhost:8000`（`X-API-Key: API_TOKEN`）。
> - 数据持久化：容器内 `/app/storage`，已挂载到本地 `./storage`。

### Docker Compose（可选）

```yaml
services:
  md2imagebot:
    image: ghcr.io/k08255-lxm/md2imagebot:latest
    container_name: md2imagebot
    env_file:
      - .env
    ports:
      - "8000:8000"
    volumes:
      - ./storage:/app/storage
    restart: unless-stopped
```

```bash
docker compose up -d
```

---

## 使用方法

- 在聊天中发送 Markdown 文本（或回复某条 Markdown 文本），机器人会返回渲染后的图片。
- 管理命令（仅管理员可用）：
  - `/public_on` / `/public_off`：打开/关闭公开使用
  - `/status`：查看运行状态与统计
  - `/wl_add 111 222`、`/wl_remove 111 222`：增删白名单
  - `/bl_add 111 222`、`/bl_remove 111 222`：增删黑名单
  - `/wl_list`、`/bl_list`：查看名单
  - `/menu`：按钮菜单（状态查看、公开开关、快捷帮助）

> 关闭公开使用时，仅**管理员与白名单**可用。黑名单**始终**无权使用。

---

## 群组/频道自动转换（插件）

内置插件 **`channel_autoconvert`**：机器人加入频道（并具备读取消息权限）后，会自动将新发的 Markdown 帖子转换为图片并回帖。可在 `storage/state.json` 的 `enabled_plugins` 中开关。

> 让机器人在群组/频道读取消息：在 [@BotFather](https://t.me/BotFather) 关闭 **Privacy Mode**，并授予相应权限。

---

## HTTP API

内置 FastAPI（默认 `http://0.0.0.0:8000`），以 `X-API-Key` 鉴权。详见 **[API.md](API.md)**。

### 快速测试

```bash
curl -X POST "http://localhost:8000/render"   -H "Content-Type: application/json"   -H "X-API-Key: $API_TOKEN"   -d '{"markdown":"# Hello","width":1024}'   --output out.png
```

---

## 配置

读取 `.env`：

- `BOT_TOKEN`：Telegram 机器人 Token
- `ADMIN_IDS`：管理员用户 ID，逗号分隔
- `PUBLIC_ENABLED`：是否公开使用（`true`/`false`）
- `API_HOST` / `API_PORT`：API 监听地址与端口
- `API_TOKEN`：API 密钥（通过 `X-API-Key` 传入）
- `RENDER_WIDTH`：渲染宽度（像素）

---

## 运行状态与数据持久化

- 持久化文件：`storage/state.json`（自动创建）
- 记录内容：开关配置、黑/白名单、统计（总请求、成功/失败、用户维度）、启用的插件
- 运行状态：启动时间、累计统计等

---

## 开发

- 代码结构：
  - `src/renderer.py`：Markdown → HTML → PNG（Playwright）
  - `src/bot.py`：Telegram 机器人（命令、权限、统计、/menu）
  - `src/api_server.py`：FastAPI（`/render`、`/stats`、`/admin/*`）
  - `src/plugins/`：插件（已内置 `channel_autoconvert`）
- 本地调试：`./setup.sh` 一键脚本（含浏览器安装）

---

## 许可

MIT
