FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖
RUN set -eux; \
    CODENAME="$(. /etc/os-release && echo "$VERSION_CODENAME")"; \
    rm -f /etc/apt/sources.list.d/debian.sources; \
    printf "deb https://mirrors.aliyun.com/debian %s main contrib non-free non-free-firmware\n" "$CODENAME" > /etc/apt/sources.list; \
    printf "deb https://mirrors.aliyun.com/debian %s-updates main contrib non-free non-free-firmware\n" "$CODENAME" >> /etc/apt/sources.list; \
    printf "deb https://mirrors.aliyun.com/debian-security %s-security main contrib non-free non-free-firmware\n" "$CODENAME" >> /etc/apt/sources.list; \
    apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    default-libmysqlclient-dev \
    pkg-config \
    netcat-openbsd \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements-dev.txt ./

# 设置国内 PyPI 镜像并安装 Python 依赖（包含测试所需）
ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

RUN pip install --no-cache-dir -r requirements-dev.txt

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data && chmod 755 /app/data

# 设置启动脚本权限
RUN chmod +x /app/start.sh

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["/app/start.sh"]
