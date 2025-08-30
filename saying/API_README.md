# API对接配置说明

## 配置步骤

### 1. 配置文件更新

在 `config.json` 中添加以下字段：

```json
{
    "api_port": 8000,
    "zitat_key": "your-secret-key-here"
}
```

- `api_port`: 外部API服务器的端口号
- `zitat_key`: 用于API认证的密钥

### 2. 后端API请求

当用户在前端添加句子时，系统会：

1. 前端通过EEL调用后端函数`add_sentence_via_api`
2. 后端自动读取config.json中的`api_port`和`zitat_key`
3. 后端向`http://127.0.0.1:{api_port}/admin`发送POST请求
4. 请求头包含：`Authorization: Bearer {zitat_key}`
5. 请求体格式：
   ```json
   {
     "action": "add_hitokoto",
     "hitokoto": "句子内容",
     "from": "来源",
     "type": "类型",
     "from_who": "作者"
   }
   ```

**返回格式**：
```json
{
    "success": true,
    "uid": "句子唯一标识符"
}
```

### 3. 启动应用

运行以下命令启动应用：

```bash
python panel.py
```

### 4. 测试

1. 访问 http://127.0.0.1:1146
2. 登录后添加句子
3. 系统会自动调用外部API并保存返回的UID