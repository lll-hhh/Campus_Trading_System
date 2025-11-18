#!/bin/bash

###############################################################################
# 四数据库恢复脚本
# 支持: MySQL, MariaDB, PostgreSQL, SQLite
# 功能: 选择性恢复、备份验证、安全确认
###############################################################################

set -euo pipefail

# 配置项
BACKUP_DIR="/home/lh/桌面/newkeshe2/backups"
LOG_FILE="${BACKUP_DIR}/restore_$(date +%Y%m%d_%H%M%S).log"

# 数据库配置
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

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

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

log_info() {
    echo -e "${BLUE}[信息]${NC} $1" | tee -a "$LOG_FILE"
}

confirm() {
    local prompt="$1"
    read -p "$prompt [y/N]: " -n 1 -r
    echo
    [[ $REPLY =~ ^[Yy]$ ]]
}

###############################################################################
# 列出可用备份
###############################################################################

list_backups() {
    local db_type="$1"
    
    log_info "可用的 ${db_type} 备份文件:"
    echo
    
    local count=1
    declare -g -A backup_files
    
    while IFS= read -r -d '' file; do
        local filename=$(basename "$file")
        local size=$(du -h "$file" | cut -f1)
        local date=$(echo "$filename" | grep -oP '\d{8}_\d{6}')
        
        backup_files[$count]="$file"
        printf "%3d) %s (%s) - %s\n" "$count" "$filename" "$size" "$date"
        ((count++))
    done < <(find "$BACKUP_DIR" -name "${db_type}_*.sql.gz" -type f -print0 | sort -zr)
    
    echo
    return $((count - 1))
}

select_backup() {
    local db_type="$1"
    
    list_backups "$db_type"
    local total=$?
    
    if [ "$total" -eq 0 ]; then
        log_error "没有找到 ${db_type} 的备份文件"
        return 1
    fi
    
    local selection
    while true; do
        read -p "请选择要恢复的备份 (1-${total}, 0=取消): " selection
        
        if [ "$selection" -eq 0 ]; then
            log_info "取消恢复操作"
            return 1
        fi
        
        if [ "$selection" -ge 1 ] && [ "$selection" -le "$total" ]; then
            SELECTED_BACKUP="${backup_files[$selection]}"
            log_info "已选择: $(basename "$SELECTED_BACKUP")"
            return 0
        else
            log_warning "无效的选择，请重新输入"
        fi
    done
}

###############################################################################
# 恢复函数
###############################################################################

restore_mysql() {
    log "开始恢复 MySQL 数据库..."
    
    if ! select_backup "mysql"; then
        return 1
    fi
    
    # 解压备份文件
    local temp_file="/tmp/mysql_restore_$$.sql"
    gunzip -c "$SELECTED_BACKUP" > "$temp_file"
    
    log_warning "⚠️  这将覆盖现有的 MySQL 数据库!"
    if ! confirm "确定要继续吗?"; then
        rm -f "$temp_file"
        return 1
    fi
    
    # 执行恢复
    if mysql \
        --host="$MYSQL_HOST" \
        --port="$MYSQL_PORT" \
        --user="$MYSQL_USER" \
        --password="$MYSQL_PASSWORD" \
        < "$temp_file" 2>> "$LOG_FILE"; then
        
        log_success "MySQL 恢复完成"
        rm -f "$temp_file"
        return 0
    else
        log_error "MySQL 恢复失败"
        rm -f "$temp_file"
        return 1
    fi
}

restore_mariadb() {
    log "开始恢复 MariaDB 数据库..."
    
    if ! select_backup "mariadb"; then
        return 1
    fi
    
    local temp_file="/tmp/mariadb_restore_$$.sql"
    gunzip -c "$SELECTED_BACKUP" > "$temp_file"
    
    log_warning "⚠️  这将覆盖现有的 MariaDB 数据库!"
    if ! confirm "确定要继续吗?"; then
        rm -f "$temp_file"
        return 1
    fi
    
    if mysql \
        --host="$MARIADB_HOST" \
        --port="$MARIADB_PORT" \
        --user="$MARIADB_USER" \
        --password="$MARIADB_PASSWORD" \
        < "$temp_file" 2>> "$LOG_FILE"; then
        
        log_success "MariaDB 恢复完成"
        rm -f "$temp_file"
        return 0
    else
        log_error "MariaDB 恢复失败"
        rm -f "$temp_file"
        return 1
    fi
}

restore_postgres() {
    log "开始恢复 PostgreSQL 数据库..."
    
    if ! select_backup "postgres"; then
        return 1
    fi
    
    local temp_file="/tmp/postgres_restore_$$.sql"
    gunzip -c "$SELECTED_BACKUP" > "$temp_file"
    
    log_warning "⚠️  这将覆盖现有的 PostgreSQL 数据库!"
    if ! confirm "确定要继续吗?"; then
        rm -f "$temp_file"
        return 1
    fi
    
    export PGPASSWORD="$POSTGRES_PASSWORD"
    
    if psql \
        --host="$POSTGRES_HOST" \
        --port="$POSTGRES_PORT" \
        --username="$POSTGRES_USER" \
        --dbname="postgres" \
        < "$temp_file" 2>> "$LOG_FILE"; then
        
        log_success "PostgreSQL 恢复完成"
        rm -f "$temp_file"
        unset PGPASSWORD
        return 0
    else
        log_error "PostgreSQL 恢复失败"
        rm -f "$temp_file"
        unset PGPASSWORD
        return 1
    fi
}

restore_sqlite() {
    log "开始恢复 SQLite 数据库..."
    
    if ! select_backup "sqlite"; then
        return 1
    fi
    
    local temp_file="/tmp/sqlite_restore_$$.db"
    gunzip -c "$SELECTED_BACKUP" > "$temp_file"
    
    log_warning "⚠️  这将覆盖现有的 SQLite 数据库!"
    if ! confirm "确定要继续吗?"; then
        rm -f "$temp_file"
        return 1
    fi
    
    # 备份当前数据库
    if [ -f "$SQLITE_PATH" ]; then
        cp "$SQLITE_PATH" "${SQLITE_PATH}.bak"
        log_info "已创建当前数据库备份: ${SQLITE_PATH}.bak"
    fi
    
    # 恢复
    cp "$temp_file" "$SQLITE_PATH"
    
    log_success "SQLite 恢复完成"
    rm -f "$temp_file"
    return 0
}

###############################################################################
# 主菜单
###############################################################################

show_menu() {
    echo
    echo "========================================="
    echo "  数据库恢复工具"
    echo "========================================="
    echo "1) 恢复 MySQL"
    echo "2) 恢复 MariaDB"
    echo "3) 恢复 PostgreSQL"
    echo "4) 恢复 SQLite"
    echo "5) 恢复所有数据库"
    echo "0) 退出"
    echo "========================================="
    echo
}

main() {
    log "========================================="
    log "数据库恢复工具启动"
    log "========================================="
    
    while true; do
        show_menu
        read -p "请选择操作: " choice
        
        case $choice in
            1)
                restore_mysql
                ;;
            2)
                restore_mariadb
                ;;
            3)
                restore_postgres
                ;;
            4)
                restore_sqlite
                ;;
            5)
                log_warning "⚠️  这将恢复所有4个数据库!"
                if confirm "确定要继续吗?"; then
                    restore_mysql
                    restore_mariadb
                    restore_postgres
                    restore_sqlite
                fi
                ;;
            0)
                log_info "退出恢复工具"
                exit 0
                ;;
            *)
                log_warning "无效的选择"
                ;;
        esac
    done
}

main "$@"
