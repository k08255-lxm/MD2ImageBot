# API 文档

基础地址：`http://{API_HOST}:{API_PORT}`（默认 `0.0.0.0:8000`）  
鉴权方式：在请求头添加 `X-API-Key: <API_TOKEN>`

## 健康检查

`GET /healthz` → 200 OK

## 渲染 Markdown 为图片

`POST /render`

- 请求（JSON）：

```json
{
  "markdown": "# 标题\n**加粗** 与 `代码`",
  "width": 1024
}
```

- 响应：`image/png` 二进制（流式返回）

**curl 示例**：

```bash
curl -X POST "http://localhost:8000/render"   -H "Content-Type: application/json"   -H "X-API-Key: $API_TOKEN"   -d '{"markdown":"# Hello","width":1024}'   --output out.png
```

## 获取统计信息

`GET /stats` → `200 OK`

```json
{
  "uptime_seconds": 12345,
  "stats": {
    "total_requests": 10,
    "render_success": 9,
    "render_failed": 1,
    "per_user": {
      "12345678": {"requests": 3, "render_success": 3}
    }
  },
  "config": {
    "public_enabled": true,
    "whitelist": [111, 222],
    "blacklist": []
  }
}
```

（需要 `X-API-Key`）

## 配置开关：公开使用

`POST /admin/config/public`

- 请求：`{"enabled": true}`
- 响应：`{"public_enabled": true}`

## 管理黑/白名单

- `POST /admin/whitelist`  请求：`{"add":[111,222],"remove":[333]}`
- `POST /admin/blacklist`  请求：`{"add":[444],"remove":[555]}`

> 以上管理员接口均需 `X-API-Key`，且服务端会同时校验调用方是否为管理员（通过 `ADMIN_IDS`）。
