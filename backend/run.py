"""
项目入口文件 - 启动 FastAPI 应用服务器

这个文件是整个后端应用的启动入口，直接运行它就能启动 Web 服务。
"""

import uvicorn  # ASGI 服务器，用于运行 FastAPI 应用

if __name__ == "__main__":
    # 启动 Uvicorn 服务器
    # "app.main:app" 表示从 app/main.py 文件中导入名为 app 的 FastAPI 实例
    # host="0.0.0.0" 表示监听所有网络接口（局域网内其他设备也能访问）
    # port=8000 表示在本机的 8000 端口提供服务
    # reload=True 表示代码修改后自动重启服务器（开发时很方便）
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
