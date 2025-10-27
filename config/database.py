"""
数据库配置文件
统一管理数据库连接参数
"""

import os
from typing import Dict, Any

class DatabaseConfig:
    """数据库配置类"""
    
    # 默认配置
    DEFAULT_CONFIG = {
        'host': 'localhost',
        'port': 3306,
        'username': 'root',
        'password': '123456',
        'database': 'oytonghuashun',
        'charset': 'utf8mb4',
        'collation': 'utf8mb4_unicode_ci'
    }
    
    def __init__(self):
        """初始化配置实例"""
        config = self._load_config()
        self.host = config['host']
        self.port = config['port']
        self.username = config['username']
        self.password = config['password']
        self.database = config['database']
        self.charset = config['charset']
        self.collation = config['collation']
    
    def _load_config(self) -> Dict[str, Any]:
        """
        加载数据库配置
        优先级：环境变量 > 默认配置
        
        @return: 数据库配置字典
        """
        config = self.DEFAULT_CONFIG.copy()
        
        # 从环境变量读取配置（如果存在）
        config['host'] = os.getenv('DB_HOST', config['host'])
        config['port'] = int(os.getenv('DB_PORT', config['port']))
        config['username'] = os.getenv('DB_USERNAME', config['username'])
        config['password'] = os.getenv('DB_PASSWORD', config['password'])
        config['database'] = os.getenv('DB_DATABASE', config['database'])
        config['charset'] = os.getenv('DB_CHARSET', config['charset'])
        
        return config
    
    @classmethod
    def get_config(cls) -> Dict[str, Any]:
        """
        获取数据库配置
        优先级：环境变量 > 默认配置
        
        @return: 数据库配置字典
        """
        config = cls.DEFAULT_CONFIG.copy()
        
        # 从环境变量读取配置（如果存在）
        config['host'] = os.getenv('DB_HOST', config['host'])
        config['port'] = int(os.getenv('DB_PORT', config['port']))
        config['username'] = os.getenv('DB_USERNAME', config['username'])
        config['password'] = os.getenv('DB_PASSWORD', config['password'])
        config['database'] = os.getenv('DB_DATABASE', config['database'])
        config['charset'] = os.getenv('DB_CHARSET', config['charset'])
        
        return config
    
    def get_connection_string(self) -> str:
        """
        获取数据库连接字符串
        
        @return: SQLAlchemy 连接字符串
        """
        return f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset={self.charset}"
    
    @classmethod
    def get_connection_string_static(cls) -> str:
        """
        获取数据库连接字符串（静态方法）
        
        @return: SQLAlchemy 连接字符串
        """
        config = cls.get_config()
        return f"mysql+pymysql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?charset={config['charset']}"
    
    def get_pymysql_config(self) -> Dict[str, Any]:
        """
        获取 PyMySQL 连接配置
        
        @return: PyMySQL 连接配置字典
        """
        return {
            'host': self.host,
            'port': self.port,
            'user': self.username,
            'password': self.password,
            'database': self.database,
            'charset': self.charset
        }
    
    @classmethod
    def get_pymysql_config_static(cls) -> Dict[str, Any]:
        """
        获取 PyMySQL 连接配置（静态方法）
        
        @return: PyMySQL 连接配置字典
        """
        config = cls.get_config()
        return {
            'host': config['host'],
            'port': config['port'],
            'user': config['username'],
            'password': config['password'],
            'database': config['database'],
            'charset': config['charset']
        }
    
    def get_database_name(self) -> str:
        """
        获取数据库名称
        
        @return: 数据库名称
        """
        return self.database
    
    @classmethod
    def get_database_name_static(cls) -> str:
        """
        获取数据库名称（静态方法）
        
        @return: 数据库名称
        """
        return cls.get_config()['database']
    
    def print_config(self) -> None:
        """打印当前配置信息"""
        print("数据库配置信息:")
        print(f"  主机: {self.host}")
        print(f"  端口: {self.port}")
        print(f"  用户名: {self.username}")
        print(f"  密码: {'*' * len(self.password)}")
        print(f"  数据库: {self.database}")
        print(f"  字符集: {self.charset}")


# 兼容性函数（保持向后兼容）
def get_db_config() -> Dict[str, Any]:
    """获取数据库配置（兼容性函数）"""
    return DatabaseConfig.get_config()

def get_connection_string() -> str:
    """获取连接字符串（兼容性函数）"""
    return DatabaseConfig.get_connection_string_static()

def get_pymysql_config() -> Dict[str, Any]:
    """获取PyMySQL配置（兼容性函数）"""
    return DatabaseConfig.get_pymysql_config_static()

def get_database_name() -> str:
    """获取数据库名称（兼容性函数）"""
    return DatabaseConfig.get_database_name_static()