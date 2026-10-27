"""
服务启动脚本
-----------
使用方法:
    python run.py              # 默认启动
    python run.py --port 8080  # 指定端口
    python run.py --reload     # 开发模式（热重载）
"""

# ===== 修复 Intel SVML DLL 缺失问题 =====
import os, sys
os.environ["NPY_DISABLE_SVML"] = "1"

# 添加 Intel SVML DLL 路径（Miniconda 环境）
_svml_dirs = [
    os.path.join(sys.prefix, "Library", "bin"),
    os.path.join(sys.base_prefix, "Library", "bin") if hasattr(sys, "base_prefix") else "",
]
for _d in _svml_dirs:
    if _d and os.path.isdir(_d):
        os.add_dll_directory(_d)
        # 也加到 PATH
        os.environ["PATH"] = _d + os.pathsep + os.environ.get("PATH", "")

import argparse
import uvicorn
from app.config import API_HOST, API_PORT


def main():
    parser = argparse.ArgumentParser(description="中文语音情感识别系统 - 后端服务")
    parser.add_argument(
        "--host", type=str, default=API_HOST, help="绑定地址 (默认: 0.0.0.0)"
    )
    parser.add_argument(
        "--port", type=int, default=API_PORT, help="绑定端口 (默认: 8000)"
    )
    parser.add_argument(
        "--reload", action="store_true", help="开发模式热重载"
    )
    parser.add_argument(
        "--workers", type=int, default=1, help="工作进程数 (默认: 1)"
    )
    args = parser.parse_args()

    print("=" * 60)
    print("  中文语音情感识别系统")
    print("=" * 60)
    print(f"  后端地址: http://{args.host}:{args.port}")
    print(f"  API 文档: http://{args.host}:{args.port}/docs")
    print(f"  健康检查: http://{args.host}:{args.port}/api/health")
    print("=" * 60)

    uvicorn.run(
        "app.main:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        workers=args.workers if not args.reload else 1,
        log_level="info",
    )


if __name__ == "__main__":
    main()
