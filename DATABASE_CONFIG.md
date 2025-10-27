# 数据库配置说明

## 概述

项目已经配置了统一的数据库连接管理系统，支持通过环境变量或默认配置来连接 MySQL 数据库。

## 配置文件

### 主要配置文件
- `config/database.py` - 统一的数据库配置类
- `.env.example` - 环境变量配置模板

### 已更新的文件
- `server/data_processor/database_manager.py` - 服务端数据库管理器
- `data_processor/database_manager.py` - 数据处理器数据库管理器
- `db_migrate.py` - 数据库迁移脚本

## 默认配置

```python
DEFAULT_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'username': 'root',
    'password': '123456',
    'database': 'oytonghuashun',
    'charset': 'utf8mb4',
    'collation': 'utf8mb4_unicode_ci'
}
```

## 环境变量配置

如果需要修改数据库连接参数，可以设置以下环境变量：

- `DB_HOST` - 数据库主机地址
- `DB_PORT` - 数据库端口
- `DB_USERNAME` - 数据库用户名
- `DB_PASSWORD` - 数据库密码
- `DB_DATABASE` - 数据库名称
- `DB_CHARSET` - 字符集

### 使用 .env 文件

1. 复制 `.env.example` 文件为 `.env`
2. 修改其中的配置参数
3. 重启应用程序

## 使用方法

### 在代码中使用

```python
from config.database import DatabaseConfig

# 创建配置实例
config = DatabaseConfig()

# 获取连接字符串
connection_string = config.get_connection_string()

# 获取 PyMySQL 配置
pymysql_config = config.get_pymysql_config()

# 使用数据库管理器
from server.data_processor.database_manager import DatabaseManager
db_manager = DatabaseManager()  # 自动使用统一配置
```

## 验证配置

运行以下命令验证数据库配置是否正确：

```bash
python -c "
from config.database import DatabaseConfig
from server.data_processor.database_manager import DatabaseManager

config = DatabaseConfig()
config.print_config()

db_manager = DatabaseManager()
stats = db_manager.get_statistics()
print('数据库连接成功!')
print('统计信息:', stats)
db_manager.close()
"
```

## 数据库迁移

运行数据库迁移脚本来创建或更新表结构：

```bash
python db_migrate.py
```

## 注意事项

1. 确保 MySQL 服务正在运行
2. 确保数据库用户有足够的权限创建数据库和表
3. 如果修改了环境变量，需要重启应用程序
4. 密码等敏感信息不要提交到版本控制系统

## 故障排除

### 常见问题

1. **连接被拒绝**
   - 检查 MySQL 服务是否启动
   - 检查主机地址和端口是否正确

2. **认证失败**
   - 检查用户名和密码是否正确
   - 检查用户是否有访问权限

3. **数据库不存在**
   - 系统会自动创建数据库，确保用户有创建数据库的权限

4. **字符编码问题**
   - 确保使用 utf8mb4 字符集
   - 检查数据库和表的字符集设置