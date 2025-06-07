#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import socket
import uvicorn
from web_app import app

def find_free_port(start_port=8080):
    """利用可能なポートを見つける"""
    for port in range(start_port, start_port + 100):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('127.0.0.1', port))
                return port
        except OSError:
            continue
    return None

if __name__ == "__main__":
    port = find_free_port()
    if port:
        print("🌐 Webサーバーを起動しています...")
        print("📍 アクセスURL:")
        print(f"   http://localhost:{port}")
        print(f"   http://127.0.0.1:{port}")
        print("🔄 サーバーを停止するには Ctrl+C を押してください")
        uvicorn.run(app, host="127.0.0.1", port=port)
    else:
        print("❌ 利用可能なポートが見つかりません")