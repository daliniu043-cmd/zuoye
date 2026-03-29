#!/bin/bash
# 游戏销售数据可视化分析系统 - 启动脚本

echo "=========================================="
echo " 游戏销售数据可视化分析系统"
echo "=========================================="

# 安装依赖
echo "[1/3] 检查依赖..."
pip install -q django numpy openpyxl 2>/dev/null

# 数据库迁移
echo "[2/3] 数据库迁移..."
python3 manage.py migrate --run-syncdb 2>&1 | tail -1

# 启动服务
echo "[3/3] 启动服务..."
echo ""
echo "  访问地址: http://0.0.0.0:8000"
echo "  管理后台: http://0.0.0.0:8000/admin/"
echo "  管理员账号: admin / admin123"
echo ""
echo "=========================================="

python3 manage.py runserver 0.0.0.0:8000
