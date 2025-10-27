"""
MySQL 数据库管理模块
功能：管理数据库连接、创建表结构、数据存储
作者：Python 后端工程师
"""

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text, Column, String, Float, DateTime, Integer, ForeignKey, Enum, BigInteger, UniqueConstraint, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from typing import Optional, List, Dict
import os
import sys

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# 导入统一的数据库配置
from config.database import DatabaseConfig

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
    - 扩展元数据字段：支持PDF爬取和内容提取的完整流程
    """
    __tablename__ = 'financial_reports'
    __table_args__ = (
        UniqueConstraint('stock_code', 'report_year', 'report_type', name='unique_report'),
    )
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    company_name = Column(String(100), nullable=False, comment='公司名称')
    stock_code = Column(String(10), nullable=False, comment='股票代码')
    report_date = Column(String(20), nullable=False, comment='报告日期')
    revenue = Column(Float, nullable=True, comment='营业收入（万元）')
    net_profit = Column(Float, nullable=True, comment='净利润（万元）')
    eps = Column(Float, nullable=True, comment='每股收益（元）')
    crawl_time = Column(String(30), nullable=False, comment='爬取时间')
    
    # 扩展元数据字段
    report_year = Column(Integer, nullable=True, comment='报告年份')
    report_type = Column(Enum('annual', 'semi_annual', 'quarterly'), nullable=True, comment='报告类型')
    report_title = Column(String(200), nullable=True, comment='财报标题')
    pdf_url = Column(String(500), nullable=True, comment='PDF原始下载链接')
    local_path = Column(String(500), nullable=True, comment='PDF本地存储路径')
    file_size = Column(BigInteger, nullable=True, comment='PDF文件大小（字节）')
    crawl_status = Column(Enum('pending', 'success', 'failed'), nullable=True, default='pending', comment='爬取状态')
    crawled_at = Column(DateTime, nullable=True, comment='爬取完成时间')
    created_at = Column(DateTime, nullable=True, server_default=func.now(), comment='记录创建时间')


class ReportContent(Base):
    """
    报告内容表
    存储从PDF中提取的文本内容，按内容类型分类存储
    
    填入时机：PDF文本与表格提取完成后
    填入信息：按PDF内容类型拆分的提取结果
    """
    __tablename__ = 'report_contents'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(Integer, ForeignKey('financial_reports.id'), nullable=False, comment='关联财务报告ID')
    content_type = Column(String(50), nullable=False, comment='内容类型(overview/balance_sheet/income_statement/cash_flow/notes)')
    extracted_text = Column(String(10000), nullable=True, comment='提取的文本内容')
    page_count = Column(Integer, nullable=True, comment='内容所在页码')
    extraction_method = Column(String(50), nullable=False, comment='提取方法(pdfplumber/OCR)')
    confidence_score = Column(Float, nullable=True, comment='提取置信度(0-1)')
    created_at = Column(DateTime, nullable=True, server_default=func.now(), comment='记录创建时间')


class FinancialMetric(Base):
    """
    财务指标表
    存储从PDF中解析出的结构化财务指标数据
    
    填入时机：从PDF提取的表格/文本中解析出结构化财务指标后
    填入信息：关键财务指标的量化数据
    """
    __tablename__ = 'financial_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True, comment='主键ID')
    report_id = Column(Integer, ForeignKey('financial_reports.id'), nullable=False, comment='关联财务报告ID')
    metric_name = Column(String(100), nullable=False, comment='指标名称(如归母净利润/ROE/资产负债率)')
    metric_value = Column(Float, nullable=True, comment='指标数值')
    metric_unit = Column(String(20), nullable=True, comment='指标单位(万元/%)')
    calculation_method = Column(String(200), nullable=True, comment='计算方法')
    period_type = Column(String(20), nullable=True, comment='周期类型(HY/FY/Q1/Q2/Q3/Q4)')
    created_at = Column(DateTime, nullable=True, server_default=func.now(), comment='记录创建时间')


class DatabaseManager:
    """
    数据库管理器
    
    主要功能：
    1. 管理数据库连接
    2. 自动创建数据库和表
    3. 数据存储和查询
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置对象，如果为None则使用默认配置
        """
        self.config = config or DatabaseConfig()
        
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
            # 连接到MySQL服务器（不指定数据库）
            temp_config = self.config.get_pymysql_config()
            temp_config.pop('database', None)  # 移除数据库名
            
            connection = pymysql.connect(**temp_config)
            
            with connection.cursor() as cursor:
                # 检查数据库是否存在
                database_name = self.config.get_database_name()
                cursor.execute(f"SHOW DATABASES LIKE '{database_name}'")
                result = cursor.fetchone()
                
                if not result:
                    # 创建数据库
                    cursor.execute(f"CREATE DATABASE {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                    logger.info(f"数据库 '{database_name}' 创建成功")
                else:
                    logger.info(f"数据库 '{database_name}' 已存在")
            
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
            self.engine = create_engine(
                self.config.get_connection_string(),
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
                # 显示三个表的结构信息
                tables = [
                    (FinancialReport, "财务报告元数据表"),
                    (ReportContent, "报告内容表"),
                    (FinancialMetric, "财务指标表")
                ]
                
                for table_class, table_desc in tables:
                    try:
                        result = connection.execute(text(f"DESCRIBE {table_class.__tablename__}"))
                        columns = result.fetchall()
                        
                        logger.info(f"表 '{table_class.__tablename__}' ({table_desc}) 结构：")
                        for column in columns:
                            logger.info(f"  {column[0]} - {column[1]} - {column[2]} - {column[3]} - {column[4]} - {column[5]}")
                        logger.info("")  # 空行分隔
                    except Exception as table_error:
                        logger.warning(f"显示表 '{table_class.__tablename__}' 结构失败：{str(table_error)}")
                    
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
            
            # 处理空值和数据类型
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
            
            # 检查重复数据并过滤
            df_to_insert = self._filter_duplicate_records(df_to_insert)
            
            if df_to_insert.empty:
                logger.info("所有记录都已存在，跳过插入")
                return True
            
            # 插入数据到数据库
            rows_inserted = df_to_insert.to_sql(
                name=FinancialReport.__tablename__,
                con=self.engine,
                if_exists='append',  # 追加数据
                index=False,
                method='multi'  # 批量插入
            )
            
            logger.info(f"成功插入 {rows_inserted} 条新记录到数据库")
            return True
            
        except Exception as e:
            logger.error(f"插入数据失败：{str(e)}")
            return False
    
    def _filter_duplicate_records(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        过滤重复记录
        
        @param df: 待插入的DataFrame
        @return: 过滤后的DataFrame
        """
        try:
            # 获取现有记录
            existing_query = f"""
            SELECT company_name, stock_code, report_date 
            FROM {FinancialReport.__tablename__}
            """
            existing_df = pd.read_sql(existing_query, self.engine)
            
            if existing_df.empty:
                return df
            
            # 创建唯一标识符进行比较
            df['unique_key'] = df['company_name'] + '_' + df['stock_code'] + '_' + df['report_date']
            existing_df['unique_key'] = existing_df['company_name'] + '_' + existing_df['stock_code'] + '_' + existing_df['report_date']
            
            # 过滤掉已存在的记录
            filtered_df = df[~df['unique_key'].isin(existing_df['unique_key'])].copy()
            filtered_df = filtered_df.drop('unique_key', axis=1)
            
            if len(df) > len(filtered_df):
                logger.info(f"过滤掉 {len(df) - len(filtered_df)} 条重复记录")
            
            return filtered_df
            
        except Exception as e:
            logger.warning(f"重复检查失败，将插入所有记录：{str(e)}")
            return df
    
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
    
    def insert_report_content(self, report_id: int, content_type: str, 
                             extracted_text: str, page_count: int = None,
                             extraction_method: str = "pdfplumber", 
                             confidence_score: float = None) -> bool:
        """
        插入报告内容数据
        
        @param report_id: 关联的财务报告ID
        @param content_type: 内容类型
        @param extracted_text: 提取的文本内容
        @param page_count: 页码
        @param extraction_method: 提取方法
        @param confidence_score: 置信度
        @return: 插入是否成功
        """
        try:
            with self.session_factory() as session:
                content = ReportContent(
                    report_id=report_id,
                    content_type=content_type,
                    extracted_text=extracted_text,
                    page_count=page_count,
                    extraction_method=extraction_method,
                    confidence_score=confidence_score
                )
                session.add(content)
                session.commit()
                logger.info(f"成功插入报告内容：report_id={report_id}, type={content_type}")
                return True
                
        except Exception as e:
            logger.error(f"插入报告内容失败：{str(e)}")
            return False
    
    def insert_financial_metric(self, report_id: int, metric_name: str,
                               metric_value: float = None, metric_unit: str = None,
                               calculation_method: str = None, 
                               period_type: str = None) -> bool:
        """
        插入财务指标数据
        
        @param report_id: 关联的财务报告ID
        @param metric_name: 指标名称
        @param metric_value: 指标数值
        @param metric_unit: 指标单位
        @param calculation_method: 计算方法
        @param period_type: 周期类型
        @return: 插入是否成功
        """
        try:
            with self.session_factory() as session:
                metric = FinancialMetric(
                    report_id=report_id,
                    metric_name=metric_name,
                    metric_value=metric_value,
                    metric_unit=metric_unit,
                    calculation_method=calculation_method,
                    period_type=period_type
                )
                session.add(metric)
                session.commit()
                logger.info(f"成功插入财务指标：report_id={report_id}, metric={metric_name}")
                return True
                
        except Exception as e:
            logger.error(f"插入财务指标失败：{str(e)}")
            return False
    
    def query_report_contents(self, report_id: int = None, 
                             content_type: str = None) -> pd.DataFrame:
        """
        查询报告内容
        
        @param report_id: 报告ID（可选）
        @param content_type: 内容类型（可选）
        @return: 查询结果 DataFrame
        """
        try:
            query = f"SELECT * FROM {ReportContent.__tablename__} WHERE 1=1"
            params = {}
            
            if report_id:
                query += " AND report_id = %(report_id)s"
                params['report_id'] = report_id
                
            if content_type:
                query += " AND content_type = %(content_type)s"
                params['content_type'] = content_type
            
            query += " ORDER BY created_at DESC"
            
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            logger.error(f"查询报告内容失败：{str(e)}")
            return pd.DataFrame()
    
    def query_financial_metrics(self, report_id: int = None,
                               metric_name: str = None) -> pd.DataFrame:
        """
        查询财务指标
        
        @param report_id: 报告ID（可选）
        @param metric_name: 指标名称（可选）
        @return: 查询结果 DataFrame
        """
        try:
            query = f"SELECT * FROM {FinancialMetric.__tablename__} WHERE 1=1"
            params = {}
            
            if report_id:
                query += " AND report_id = %(report_id)s"
                params['report_id'] = report_id
                
            if metric_name:
                query += " AND metric_name LIKE %(metric_name)s"
                params['metric_name'] = f"%{metric_name}%"
            
            query += " ORDER BY created_at DESC"
            
            return pd.read_sql(query, self.engine, params=params)
            
        except Exception as e:
            logger.error(f"查询财务指标失败：{str(e)}")
            return pd.DataFrame()


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