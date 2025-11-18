#!/bin/bash

###############################################################################
# 四数据库自动备份脚本
# 支持: MySQL, MariaDB, PostgreSQL, SQLite
# 功能: 自动备份、压缩、保留策略、错误通知
###############################################################################

set -euo pipefail

# 配置项
BACKUP_DIR="/home/lh/桌面/newkeshe2/backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RETENTION_DAYS=30  # 保留30天的备份
LOG_FILE="${BACKUP_DIR}/backup_${TIMESTAMP}.log"

# 数据库配置 (从环境变量或.env文件读取)
MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASSWORD="${MYSQL_PASSWORD:-password}"
MYSQL_DATABASE="${MYSQL_DATABASE:-campuswap}"

MARIADB_HOST="${MARIADB_HOST:-localhost}"
MARIADB_PORT="${MARIADB_PORT:-3307}"
MARIADB_USER="${MARIADB_USER:-root}"
MARIADB_PASSWORD="${MARIADB_PASSWORD:-password}"
MARIADB_DATABASE="${MARIADB_DATABASE:-campuswap}"

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_USER="${POSTGRES_USER:-postgres}"
POSTGRES_PASSWORD="${POSTGRES_PASSWORD:-password}"
POSTGRES_DATABASE="${POSTGRES_DATABASE:-campuswap}"

SQLITE_PATH="${SQLITE_PATH:-/home/lh/桌面/newkeshe2/data/campuswap.db}"

# 邮件通知配置
ADMIN_EMAIL="${ADMIN_EMAIL:-admin@example.com}"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

###############################################################################
# 工具函数
###############################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}[成功]${NC} $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}[错误]${NC} $1" | tee -a "$LOG_FILE"
}

log_warning() {
    echo -e "${YELLOW}[警告]${NC} $1" | tee -a "$LOG_FILE"
}

send_notification() {
    local subject="$1"
    local message="$2"
    
    # 使用mailx或sendmail发送邮件 (需要配置SMTP)
    if command -v mail &> /dev/null; then
        echo "$message" | mail -s "$subject" "$ADMIN_EMAIL"
    fi
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "命令 $1 未找到，请先安装"
        return 1
    fi
    return 0
}

###############################################################################
# 备份函数
###############################################################################

backup_mysql() {
    log "开始备份 MySQL 数据库..."
    
    local backup_file="${BACKUP_DIR}/mysql_${MYSQL_DATABASE}_${TIMESTAMP}.sql"
    
    if ! check_command mysqldump; then
        return 1
    fi
    
    # 执行备份 (包含存储过程、触发器、函数)
    if mysqldump \
        --host="$MYSQL_HOST" \
        --port="$MYSQL_PORT" \
        --user="$MYSQL_USER" \
        --password="$MYSQL_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --add-drop-database \
        --databases "$MYSQL_DATABASE" \
        > "$backup_file" 2>> "$LOG_FILE"; then
        
        # 压缩备份文件
        gzip "$backup_file"
        
        local size=$(du -h "${backup_file}.gz" | cut -f1)
        log_success "MySQL 备份完成: ${backup_file}.gz (${size})"
        
        return 0
    else
        log_error "MySQL 备份失败"
        return 1
    fi
}

backup_mariadb() {
    log "开始备份 MariaDB 数据库..."
    
    local backup_file="${BACKUP_DIR}/mariadb_${MARIADB_DATABASE}_${TIMESTAMP}.sql"
    
    if ! check_command mysqldump; then
        return 1
    fi
    
    if mysqldump \
        --host="$MARIADB_HOST" \
        --port="$MARIADB_PORT" \
        --user="$MARIADB_USER" \
        --password="$MARIADB_PASSWORD" \
        --single-transaction \
        --routines \
        --triggers \
        --events \
        --add-drop-database \
        --databases "$MARIADB_DATABASE" \
        > "$backup_file" 2>> "$LOG_FILE"; then
        
        gzip "$backup_file"
        
        local size=$(du -h "${backup_file}.gz" | cut -f1)
        log_success "MariaDB 备份完成: ${backup_file}.gz (${size})"
        
        return 0
    else
        log_error "MariaDB 备份失败"
        return 1
    fi
}

backup_postgres() {
    log "开始备份 PostgreSQL 数据库..."
    
    local backup_file="${BACKUP_DIR}/postgres_${POSTGRES_DATABASE}_${TIMESTAMP}.sql"
    
    if ! check_command pg_dump; then
        return 1
    fi
    
    # 设置密码环境变量
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    if pg_dump \
        --host="$POSTGRES_HOST" \
        --port="$POSTGRES_PORT" \
        --username="$POSTGRES_USER" \
        --dbname="$POSTGRES_DATABASE" \
        --format=plain \
        --clean \
        --create \
        --if-exists \
        > "$backup_file" 2>> "$LOG_FILE"; then
        
        gzip "$backup_file"
        
        local size=$(du -h "${backup_file}.gz" | cut -f1)
        log_success "PostgreSQL 备份完成: ${backup_file}.gz (${size})"
        
        unset PGPASSWORD
        return 0
    else
        log_error "PostgreSQL 备份失败"
        unset PGPASSWORD
        return 1
    fi
}

backup_sqlite() {
    log "开始备份 SQLite 数据库..."
    
    if [ ! -f "$SQLITE_PATH" ]; then
        log_warning "SQLite 数据库文件不存在: $SQLITE_PATH"
        return 1
    fi
    
    local backup_file="${BACKUP_DIR}/sqlite_campuswap_${TIMESTAMP}.db"
    
    # 使用 SQLite 的在线备份 API
    if check_command sqlite3; then
        sqlite3 "$SQLITE_PATH" ".backup '$backup_file'" 2>> "$LOG_FILE"
        
        # 压缩备份文件
        gzip "$backup_file"
        
        local size=$(du -h "${backup_file}.gz" | cut -f1)
        log_success "SQLite 备份完成: ${backup_file}.gz (${size})"
        
        return 0
    else
        # 回退到简单复制
        cp "$SQLITE_PATH" "$backup_file"
        gzip "$backup_file"
        
        log_success "SQLite 备份完成 (使用复制方式)"
        return 0
    fi
}

###############################################################################
# 备份验证
###############################################################################

verify_backup() {
    local backup_file="$1"
    
    log "验证备份文件: $backup_file"
    
    # 检查文件是否存在且大小大于0
    if [ ! -f "$backup_file" ]; then
        log_error "备份文件不存在: $backup_file"
        return 1
    fi
    
    local size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file" 2>/dev/null)
    if [ "$size" -eq 0 ]; then
        log_error "备份文件为空: $backup_file"
        return 1
    fi
    
    # 验证 gzip 文件完整性
    if [[ "$backup_file" == *.gz ]]; then
        if gzip -t "$backup_file" 2>> "$LOG_FILE"; then
            log_success "备份文件完整性验证通过"
            return 0
        else
            log_error "备份文件损坏"
            return 1
        fi
    fi
    
    return 0
}

###############################################################################
# 清理旧备份
###############################################################################

cleanup_old_backups() {
    log "清理 ${RETENTION_DAYS} 天前的旧备份..."
    
    local count=0
    while IFS= read -r -d '' file; do
        rm -f "$file"
        ((count++))
        log "删除旧备份: $(basename "$file")"
    done < <(find "$BACKUP_DIR" -name "*.gz" -type f -mtime "+${RETENTION_DAYS}" -print0 2>/dev/null)
    
    if [ "$count" -gt 0 ]; then
        log_success "清理了 $count 个旧备份文件"
    else
        log "没有需要清理的旧备份"
    fi
}

###############################################################################
# 主函数
###############################################################################

main() {
    log "========================================="
    log "开始四数据库自动备份"
    log "========================================="
    
    # 创建备份目录
    mkdir -p "$BACKUP_DIR"
    
    local success_count=0
    local fail_count=0
    
    # 备份 MySQL
    if backup_mysql; then
        ((success_count++))
    else
        ((fail_count++))
    fi
    
    # 备份 MariaDB
    if backup_mariadb; then
        ((success_count++))
    else
        ((fail_count++))
    fi
    
    # 备份 PostgreSQL
    if backup_postgres; then
        ((success_count++))
    else
        ((fail_count++))
    fi
    
    # 备份 SQLite
    if backup_sqlite; then
        ((success_count++))
    else
        ((fail_count++))
    fi
    
    # 验证所有备份
    log "========================================="
    log "验证备份文件..."
    log "========================================="
    
    for backup in "${BACKUP_DIR}"/*_${TIMESTAMP}.*.gz; do
        if [ -f "$backup" ]; then
            verify_backup "$backup"
        fi
    done
    
    # 清理旧备份
    cleanup_old_backups
    
    # 统计结果
    log "========================================="
    log "备份完成统计:"
    log "  成功: ${success_count}"
    log "  失败: ${fail_count}"
    log "========================================="
    
    # 发送通知
    if [ "$fail_count" -gt 0 ]; then
        send_notification \
            "⚠️ 数据库备份部分失败" \
            "成功: ${success_count}, 失败: ${fail_count}。详情查看: $LOG_FILE"
        exit 1
    else
        send_notification \
            "✅ 数据库备份成功" \
            "所有 4 个数据库已成功备份。详情查看: $LOG_FILE"
        exit 0
    fi
}

# 运行主函数
main "$@"
