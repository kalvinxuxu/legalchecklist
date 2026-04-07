#!/bin/bash

# 法务 AI SaaS - 数据库备份脚本
# 用法：bash backup-db.sh

set -e

# 配置
PROJECT_DIR="/opt/legal-ai-saas"
BACKUP_DIR="/opt/backups/legal-saas"
MYSQL_CONTAINER="legal-ai-saas-db-1"
MYSQL_USER="root"
MYSQL_PASS=""
DB_NAME="legal_saas"
RETENTION_DAYS=30

# 从 docker-compose.yml 读取密码
if [ -f "$PROJECT_DIR/backend/.env" ]; then
    MYSQL_PASS=$(grep MYSQL_PASSWORD $PROJECT_DIR/backend/.env | cut -d'=' -f2)
fi

# 创建备份目录
mkdir -p $BACKUP_DIR

# 生成备份文件名
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/${DB_NAME}_${DATE}.sql"

echo "开始备份数据库：$DB_NAME"

# 执行备份
docker exec $MYSQL_CONTAINER mysqldump -u$MYSQL_USER -p$MYSQL_PASS $DB_NAME > $BACKUP_FILE

# 压缩
gzip $BACKUP_FILE

echo "备份完成：${BACKUP_FILE}.gz"

# 删除旧备份
echo "清理 ${RETENTION_DAYS} 天前的旧备份..."
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "备份任务完成"
