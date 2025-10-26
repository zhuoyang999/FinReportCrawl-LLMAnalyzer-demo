"""
MySQL 数据库管理模块
功能：管理数据库连接、创建表结构、数据存储
作者：Python 后端工程师
"""

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text, Column, String, Float, DateTime, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from typing import Optional, List, Dict

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建基类
Base = declarative_base()


class FinancialReport(Base):
    """
    财务报告数据表模型
    
    表结构：
    - id: 主键，自增
    - company_name: 公司名称
    - stock_code: 股票代码
    - report_date: 报告日期
    - revenue: 营收（万元）
    - net_profit: 净利润（万元）
    - eps: 每股收益（元）
    - crawl_time: 爬取时间
    """
    __tablename__ = 'financial_reports'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    company_name = Column(String(100), nullable=False, comment='公司名称')
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    report_date = Column(String(20), nullable=False, comment='报告日期')
    revenue = Column(Float, nullable=True, comment='营业收入（万元）')
    net_profit = Column(Float, nullable=True, comment='净利润（万元）')
    eps = Column(Float, nullable=True, comment='每股收益（元）')
    crawl_time = Column(String(30), nullable=False, comment='爬取时间')


class DatabaseManager:
    """
    数据库管理器
    
    主要功能：
    1. 管理数据库连接
    2. 自动创建数据库和表
    3. 数据存储和查询
    """
    
    def __init__(self, 
                 host: str = 'localhost',
                 port: int = 3306,
                 username: str = 'root',
                 password: str = '123456',
                 database: str = 'oytonghuashun'):
        """
        初始化数据库管理器
        
        @param host: 数据库主机地址
        @param port: 数据库端口
        @param username: 数据库用户名
        @param password: 数据库密码
        @param database: 数据库名称
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.database = database
        
        # 数据库连接引擎
        self.engine = None
        self.session_factory = None
        
        # 初始化数据库连接
        self._initialize_database()
    
    def _create_database_if_not_exists(self):
        """
        如果数据库不存在则创建数据库
        """
        try:
            # 连接到 MySQL 服务器（不指定数据库）
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.username,
                password=self.password,
                charset='utf8mb4'
            )
            
            with connection.cursor() as cursor:
                # 检查数据库是否存在
                cursor.execute(f"SHOW DATABASES LIKE '{self.database}'")
                result = cursor.fetchone()
                
                if not result:
                    # 创建数据库
                    cursor.execute(f"CREATE DATABASE {self.database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"数据库 '{self.database}' 创建成功")
                else:
                    logger.info(f"数据库 '{self.database}' 已存在")
            
            connection.close()
            
        except Exception as e:
            logger.error(f"创建数据库失败：{str(e)}")
            raise
    
    def _initialize_database(self):
        """
        初始化数据库连接和表结构
        """
        try:
            # 创建数据库（如果不存在）
            self._create_database_if_not_exists()
            
            # 创建数据库连接引擎
            connection_string = f"mysql+pymysql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"
            self.engine = create_engine(
                connection_string,
                echo=False,  # 设置为 True 可以看到 SQL 语句
                pool_recycle=3600,  # 连接池回收时间
                pool_pre_ping=True  # 连接前检查连接是否有效
            )
            
            # 创建会话工厂
            self.session_factory = sessionmaker(bind=self.engine)
            
            # 创建表结构
            self._create_tables()
            
            logger.info("数据库初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败：{str(e)}")
            raise
    
    def _create_tables(self):
        """
        创建数据表
        """
        try:
            # 创建所有表
            Base.metadata.create_all(self.engine)
            logger.info("数据表创建成功")
            
            # 显示表结构信息
            self._show_table_info()
            
        except Exception as e:
            logger.error(f"创建数据表失败：{str(e)}")
            raise
    
    def _show_table_info(self):
        """
        显示表结构信息
        """
        try:
            with self.engine.connect() as connection:
                # 查询表结构
                result = connection.execute(text(f"DESCRIBE {FinancialReport.__tablename__}"))
                columns = result.fetchall()
                
                logger.info(f"表 '{FinancialReport.__tablename__}' 结构：")
                for column in columns:
                    logger.info(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]} - {column[5]}")
                    
        except Exception as e:
            logger.warning(f"显示表结构信息失败：{str(e)}")
    
    def insert_dataframe(self, df: pd.DataFrame) -> bool:
        """
        将 DataFrame 数据插入到数据库
        
        @param df: 包含财务数据的 DataFrame
        @return: 插入是否成功
        """
        try:
            if df.empty:
                logger.warning("DataFrame 为空，跳过插入")
                return False
            
            # 确保 DataFrame 包含必要的列
            required_columns = ['company_name', 'stock_code', 'report_date', 'crawl_time']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"DataFrame 缺少必要列：{missing_columns}")
                return False
            
            # 数据预处理
            df_clean = df.copy()
            
            # 处理空值
            df_clean['revenue'] = pd.to_numeric(df_clean.get('revenue', None), errors='coerce')
            df_clean['net_profit'] = pd.to_numeric(df_clean.get('net_profit', None), errors='coerce')
            df_clean['eps'] = pd.to_numeric(df_clean.get('eps', None), errors='coerce')
            
            # 确保字符串列不为空
            df_clean['company_name'] = df_clean['company_name'].fillna('未知公司')
            df_clean['stock_code'] = df_clean['stock_code'].fillna('000000')
            df_clean['report_date'] = df_clean['report_date'].fillna('1900-01-01')
            df_clean['crawl_time'] = df_clean['crawl_time'].fillna(datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            # 选择需要的列
            columns_to_insert = ['company_name', 'stock_code', 'report_date', 'revenue', 'net_profit', 'eps', 'crawl_time']
            df_to_insert = df_clean[columns_to_insert]
            
            # 插入数据到数据库
            rows_inserted = df_to_insert.to_sql(
                name=FinancialReport.__tablename__,
                con=self.engine,
                if_exists='append',  # 追加数据
                index=False,
                method='multi'  # 批量插入
            )
            
            logger.info(f"成功插入 {rows_inserted} 条记录到数据库")
            return True
            
        except Exception as e:
            logger.error(f"插入数据失败：{str(e)}")
            return False
    
    def query_data(self, 
                   stock_code: Optional[str] = None,
                   company_name: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   limit: int = 100) -> pd.DataFrame:
        """
        查询财务数据
        
        @param stock_code: 股票代码（可选）
        @param company_name: 公司名称（可选）
        @param start_date: 开始日期（可选）
        @param end_date: 结束日期（可选）
        @param limit: 返回记录数限制
        @return: 查询结果 DataFrame
        """
        try:
            # 构建查询条件
            conditions = []
            params = {}
            
            if stock_code:
                conditions.append("stock_code = :stock_code")
                params['stock_code'] = stock_code
            
            if company_name:
                conditions.append("company_name LIKE :company_name")
                params['company_name'] = f"%{company_name}%"
            
            if start_date:
                conditions.append("report_date >= :start_date")
                params['start_date'] = start_date
            
            if end_date:
                conditions.append("report_date <= :end_date")
                params['end_date'] = end_date
            
            # 构建 SQL 查询
            base_query = f"SELECT * FROM {FinancialReport.__tablename__}"
            if conditions:
                base_query += " WHERE " + " AND ".join(conditions)
            base_query += " ORDER BY report_date DESC, crawl_time DESC"
            base_query += f" LIMIT {limit}"
            
            # 执行查询
            df = pd.read_sql(
                sql=text(base_query),
                con=self.engine,
                params=params
            )
            
            logger.info(f"查询到 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"查询数据失败：{str(e)}")
            return pd.DataFrame()
    
    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        @return: 统计信息字典
        """
        try:
            with self.engine.connect() as connection:
                # 总记录数
                total_count = connection.execute(
                    text(f"SELECT COUNT(*) FROM {FinancialReport.__tablename__}")
                ).scalar()
                
                # 公司数量
                company_count = connection.execute(
                    text(f"SELECT COUNT(DISTINCT stock_code) FROM {FinancialReport.__tablename__}")
                ).scalar()
                
                # 最新报告日期
                latest_date = connection.execute(
                    text(f"SELECT MAX(report_date) FROM {FinancialReport.__tablename__}")
                ).scalar()
                
                # 最早报告日期
                earliest_date = connection.execute(
                    text(f"SELECT MIN(report_date) FROM {FinancialReport.__tablename__}")
                ).scalar()
                
                stats = {
                    'total_records': total_count,
                    'total_companies': company_count,
                    'latest_report_date': latest_date,
                    'earliest_report_date': earliest_date
                }
                
                logger.info(f"数据库统计信息：{stats}")
                return stats
                
        except Exception as e:
            logger.error(f"获取统计信息失败：{str(e)}")
            return {}
    
    def close(self):
        """
        关闭数据库连接
        """
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")


def main():
    """
    主函数：演示数据库管理功能
    """
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    # 创建测试数据
    test_data = {
        'company_name': ['测试公司A', '测试公司B'],
        'stock_code': ['000001', '000002'],
        'report_date': ['2023-12-31', '2023-12-31'],
        'revenue': [1000000.0, 2000000.0],
        'net_profit': [100000.0, 200000.0],
        'eps': [1.5, 2.0],
        'crawl_time': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")] * 2
    }
    
    test_df = pd.DataFrame(test_data)
    
    # 插入测试数据
    success = db_manager.insert_dataframe(test_df)
    if success:
        print("测试数据插入成功")
        
        # 查询数据
        result_df = db_manager.query_data(limit=10)
        print("查询结果：")
        print(result_df)
        
        # 获取统计信息
        stats = db_manager.get_statistics()
        print("统计信息：")
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # 关闭连接
    db_manager.close()


if __name__ == "__main__":
    main()