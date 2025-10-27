#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库管理器模块
负责数据库连接、表创建、数据插入和查询等操作
"""

import pandas as pd
import pymysql
from sqlalchemy import create_engine, text, Column, String, Float, DateTime, Integer, ForeignKey, Enum, BigInteger, Date, UniqueConstraint, and_, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import logging
from typing import Optional, List, Dict, Any
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# 导入统一的数据库配置
from config.database import DatabaseConfig

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建基类
Base = declarative_base()


class FinancialReport(Base):
    """
    财务报告数据模型
    存储公司财务报告的基本信息和关键指标
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
    
    # 扩展字段
    report_year = Column(Integer, nullable=True, comment='报告年份')
    report_type = Column(Enum('annual', 'semi_annual', 'quarterly'), nullable=True, comment='报告类型')
    report_title = Column(String(200), nullable=True, comment='财报标题')
    pdf_url = Column(String(500), nullable=True, comment='PDF原始下载链接')
    local_path = Column(String(500), nullable=True, comment='PDF本地存储路径')
    file_size = Column(BigInteger, nullable=True, comment='PDF文件大小（字节）')
    crawl_status = Column(Enum('pending', 'success', 'failed'), nullable=True, comment='爬取状态')
    crawled_at = Column(DateTime, nullable=True, comment='爬取完成时间')
    created_at = Column(DateTime, nullable=True, server_default=func.now(), comment='记录创建时间')


class ReportContent(Base):
    """报告内容表"""
    __tablename__ = 'report_contents'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('financial_reports.id'), nullable=False)
    content_type = Column(String(50), nullable=False, comment='内容类型')
    extraction_method = Column(String(50), nullable=False, comment='提取方法')
    extracted_text = Column(String(10000), nullable=True, comment='提取的文本')
    created_at = Column(DateTime, nullable=True, server_default=func.now())


class FinancialMetric(Base):
    """财务指标表"""
    __tablename__ = 'financial_metrics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('financial_reports.id'), nullable=False)
    metric_name = Column(String(100), nullable=False, comment='指标名称')
    metric_value = Column(Float, nullable=True, comment='指标值')
    metric_unit = Column(String(20), nullable=True, comment='指标单位')
    period_type = Column(String(20), nullable=True, comment='期间类型')


class DatabaseManager:
    """
    数据库管理器
    负责数据库连接、表创建、数据插入和查询等操作
    """
    
    def __init__(self, config: Optional[DatabaseConfig] = None):
        """
        初始化数据库管理器
        
        Args:
            config: 数据库配置对象，如果为None则使用默认配置
        """
        self.config = config or DatabaseConfig()
        self.engine = None
        self.SessionLocal = None
        
        # 初始化数据库连接
        self._initialize_database()
    
    def _create_database_if_not_exists(self):
        """创建数据库（如果不存在）"""
        try:
            # 连接到MySQL服务器（不指定数据库）
            temp_config = self.config.get_pymysql_config()
            temp_config.pop('database', None)  # 移除数据库名
            
            connection = pymysql.connect(**temp_config)
            cursor = connection.cursor()
            
            # 创建数据库
            database_name = self.config.get_database_name()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{database_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            logger.info(f"数据库 '{database_name}' 已确保存在")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            logger.error(f"创建数据库失败: {e}")
            raise
    
    def _initialize_database(self):
        """初始化数据库连接和表"""
        try:
            # 确保数据库存在
            self._create_database_if_not_exists()
            
            # 创建数据库引擎
            self.engine = create_engine(
                self.config.get_connection_string(),
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600
            )
            
            # 创建会话工厂
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # 创建表
            self._create_tables()
            
            # 显示表信息
            self._show_table_info()
            
            logger.info("数据库初始化成功")
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            raise
    
    def _create_tables(self):
        """创建数据表"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("数据表创建成功")
        except Exception as e:
            logger.error(f"创建数据表失败: {e}")
            raise
    
    def _show_table_info(self):
        """显示表结构信息"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SHOW TABLES"))
                tables = [row[0] for row in result]
                logger.info(f"当前数据库中的表: {tables}")
                
                if 'financial_reports' in tables:
                    result = connection.execute(text("DESCRIBE financial_reports"))
                    columns = result.fetchall()
                    logger.info("financial_reports 表结构:")
                    for column in columns:
                        logger.info(f"  {column}")
                        
        except Exception as e:
            logger.error(f"显示表信息失败: {e}")
    
    def insert_dataframe(self, df: pd.DataFrame) -> bool:
        """
        将DataFrame数据插入到数据库
        
        Args:
            df: 包含财务数据的DataFrame
            
        Returns:
            bool: 插入是否成功
        """
        try:
            # 验证必需的列
            required_columns = ['company_name', 'stock_code', 'report_date']
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                logger.error(f"DataFrame缺少必需的列: {missing_columns}")
                return False
            
            # 使用pandas的to_sql方法插入数据
            df.to_sql(
                name='financial_reports',
                con=self.engine,
                if_exists='append',
                index=False,
                method='multi'
            )
            
            logger.info(f"成功插入 {len(df)} 条记录到数据库")
            return True
            
        except Exception as e:
            logger.error(f"插入数据失败: {e}")
            return False
    
    def query_data(self, 
                   stock_code: Optional[str] = None,
                   company_name: Optional[str] = None,
                   start_date: Optional[str] = None,
                   end_date: Optional[str] = None,
                   limit: int = 100) -> pd.DataFrame:
        """
        查询财务数据
        
        Args:
            stock_code: 股票代码
            company_name: 公司名称
            start_date: 开始日期
            end_date: 结束日期
            limit: 返回记录数限制
            
        Returns:
            pd.DataFrame: 查询结果
        """
        try:
            # 构建查询条件
            conditions = []
            if stock_code:
                conditions.append(f"stock_code = '{stock_code}'")
            if company_name:
                conditions.append(f"company_name LIKE '%{company_name}%'")
            if start_date:
                conditions.append(f"report_date >= '{start_date}'")
            if end_date:
                conditions.append(f"report_date <= '{end_date}'")
            
            # 构建SQL查询
            where_clause = " AND ".join(conditions) if conditions else "1=1"
            query = f"""
                SELECT * FROM financial_reports 
                WHERE {where_clause}
                ORDER BY report_date DESC, company_name
                LIMIT {limit}
            """
            
            # 执行查询
            df = pd.read_sql(query, self.engine)
            logger.info(f"查询返回 {len(df)} 条记录")
            return df
            
        except Exception as e:
            logger.error(f"查询数据失败: {e}")
            return pd.DataFrame()
    
    def get_statistics(self) -> Dict:
        """
        获取数据库统计信息
        
        Returns:
            Dict: 统计信息字典
        """
        try:
            with self.engine.connect() as connection:
                # 总记录数
                result = connection.execute(text("SELECT COUNT(*) FROM financial_reports"))
                total_records = result.scalar()
                
                # 公司数量
                result = connection.execute(text("SELECT COUNT(DISTINCT company_name) FROM financial_reports"))
                total_companies = result.scalar()
                
                # 最新报告日期
                result = connection.execute(text("SELECT MAX(report_date) FROM financial_reports"))
                latest_date = result.scalar()
                
                # 最早报告日期
                result = connection.execute(text("SELECT MIN(report_date) FROM financial_reports"))
                earliest_date = result.scalar()
                
                return {
                    'total_records': total_records,
                    'total_companies': total_companies,
                    'latest_report_date': latest_date,
                    'earliest_report_date': earliest_date,
                    'database_name': self.config.get_database_name()
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def list_reports(
        self,
        stock_code: Optional[str] = None,
        report_year: Optional[int] = None,
        report_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """分页查询扩展后的财报元数据列表"""
        session = self.SessionLocal()
        try:
            query = session.query(FinancialReport)
            conditions = []
            if stock_code:
                conditions.append(FinancialReport.stock_code == stock_code)
            if report_year:
                conditions.append(FinancialReport.report_year == report_year)
            if report_type:
                conditions.append(FinancialReport.report_type == report_type)
            if conditions:
                query = query.filter(and_(*conditions))
            total = query.count()
            records = (
                query.order_by(FinancialReport.report_year.desc(), FinancialReport.report_type.asc())
                .offset((page - 1) * page_size)
                .limit(page_size)
                .all()
            )
            items = [
                {
                    'id': r.id,
                    'stock_code': r.stock_code,
                    'company_name': r.company_name,
                    'report_year': r.report_year,
                    'report_type': r.report_type,
                    'report_date': r.report_date,
                    'local_path': r.local_path,
                    'pdf_url': r.pdf_url,
                    'file_size': r.file_size,
                    'crawled_at': r.crawled_at,
                }
                for r in records
            ]
            return {
                'total': total,
                'page': page,
                'page_size': page_size,
                'items': items,
            }
        finally:
            session.close()

    def get_report_details(self, report_id: int) -> Optional[Dict[str, Any]]:
        """获取单个财报的详情，包括文本内容与指标"""
        session = self.SessionLocal()
        try:
            report = session.query(FinancialReport).get(report_id)
            if not report:
                return None
            contents = (
                session.query(ReportContent)
                .filter(ReportContent.report_id == report_id)
                .order_by(ReportContent.created_at.asc())
                .all()
            )
            metrics = (
                session.query(FinancialMetric)
                .filter(FinancialMetric.report_id == report_id)
                .order_by(FinancialMetric.metric_name.asc())
                .all()
            )
            return {
                'id': report.id,
                'stock_code': report.stock_code,
                'company_name': report.company_name,
                'report_year': report.report_year,
                'report_type': report.report_type,
                'report_date': report.report_date,
                'local_path': report.local_path,
                'pdf_url': report.pdf_url,
                'file_size': report.file_size,
                'crawled_at': report.crawled_at,
                'contents': [
                    {
                        'id': c.id,
                        'content_type': c.content_type,
                        'extraction_method': c.extraction_method,
                        'text_length': len(c.extracted_text or ''),
                        'created_at': c.created_at,
                    }
                    for c in contents
                ],
                'metrics': [
                    {
                        'id': m.id,
                        'metric_name': m.metric_name,
                        'metric_value': m.metric_value,
                        'metric_unit': m.metric_unit,
                        'period_type': m.period_type,
                    }
                    for m in metrics
                ],
            }
        finally:
            session.close()
    
    def close(self):
        """关闭数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")


def main():
    """
    主函数：演示数据库管理功能
    """
    # 创建数据库管理器（使用统一配置）
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