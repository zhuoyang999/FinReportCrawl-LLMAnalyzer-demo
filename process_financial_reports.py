#!/usr/bin/env python3
"""
财报数据处理主脚本
功能：将爬取的 PDF 财报解析并存储到 MySQL 数据库
作者：Python 后端工程师

使用方法：
1. 确保 MySQL 服务正在运行
2. 确保已安装所有依赖：pip install -r requirements.txt
3. 运行脚本：python process_financial_reports.py

数据库配置：
- 数据库：oytonghuashun
- 表名：financial_reports
- 用户：root
- 密码：123456
"""

import os
import sys
import argparse
import pandas as pd
from datetime import datetime
import logging

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor.pdf_parser import FinancialReportParser
from data_processor.database_manager import DatabaseManager
from data_processor.knowledge_base_manager import KnowledgeBaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('financial_reports_processing.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FinancialReportProcessor:
    """
    财报数据处理器
    
    主要功能：
    1. 解析 PDF 财报文件
    2. 转换为 pandas DataFrame
    3. 存储到 MySQL 数据库
    4. 提供数据查询和统计功能
    """
    
    def __init__(self, 
                 db_host: str = 'localhost',
                 db_port: int = 3306,
                 db_username: str = 'root',
                 db_password: str = '123456',
                 db_name: str = 'oytonghuashun'):
        """
        初始化财报数据处理器
        
        @param db_host: 数据库主机地址
        @param db_port: 数据库端口
        @param db_username: 数据库用户名
        @param db_password: 数据库密码
        @param db_name: 数据库名称
        """
        logger.info("初始化财报数据处理器...")
        
        # 初始化 PDF 解析器
        self.pdf_parser = FinancialReportParser()
        
        # 初始化知识库管理器
        try:
            self.knowledge_base_manager = KnowledgeBaseManager()
            logger.info("知识库管理器初始化成功")
        except Exception as e:
            logger.error(f"知识库管理器初始化失败：{str(e)}")
            # 即使知识库初始化失败，也允许继续执行，只记录错误
            self.knowledge_base_manager = None

        # 初始化数据库管理器
        try:
            self.db_manager = DatabaseManager(
                host=db_host,
                port=db_port,
                username=db_username,
                password=db_password,
                database=db_name
            )
            logger.info("数据库连接成功")
        except Exception as e:
            logger.error(f"数据库连接失败：{str(e)}")
            raise
    
    def process_pdf_directory(self, pdf_directory: str) -> bool:
        """
        处理指定目录下的所有 PDF 文件
        
        @param pdf_directory: PDF 文件目录路径
        @return: 处理是否成功
        """
        try:
            logger.info(f"开始处理目录：{pdf_directory}")
            
            # 检查目录是否存在
            if not os.path.exists(pdf_directory):
                logger.error(f"目录不存在：{pdf_directory}")
                return False
            
            # 解析 PDF 文件
            logger.info("正在解析 PDF 文件...")
            df = self.pdf_parser.parse_directory(pdf_directory)
            
            if df.empty:
                logger.warning("没有解析到任何数据")
                return False
            
            logger.info(f"成功解析 {len(df)} 条记录")
            
            # 显示解析结果预览
            self._show_dataframe_preview(df)
            
            # 存储到数据库
            logger.info("正在存储数据到数据库...")
            success = self.db_manager.insert_dataframe(df)
            
            if success:
                logger.info("数据存储成功")
                
                # 将处理过的PDF添加到知识库
                if self.knowledge_base_manager:
                    logger.info("正在将PDF内容添加到知识库...")
                    # 我们需要遍历目录下的所有PDF文件
                    for root, _, files in os.walk(pdf_directory):
                        for file in files:
                            if file.lower().endswith('.pdf'):
                                pdf_path = os.path.join(root, file)
                                try:
                                    self.knowledge_base_manager.add_pdf_to_collection(pdf_path, collection_name="financial_reports")
                                except Exception as e:
                                    logger.error(f"无法将 {pdf_path} 添加到知识库: {e}")
                
                # 显示数据库统计信息
                self._show_database_statistics()
                
                return True
            else:
                logger.error("数据存储失败")
                return False
                
        except Exception as e:
            logger.error(f"处理 PDF 目录失败：{str(e)}")
            return False
    
    def process_single_pdf(self, pdf_path: str) -> bool:
        """
        处理单个 PDF 文件
        
        @param pdf_path: PDF 文件路径
        @return: 处理是否成功
        """
        try:
            logger.info(f"开始处理文件：{pdf_path}")
            
            # 解析单个 PDF 文件
            result = self.pdf_parser.parse_single_pdf(pdf_path)
            
            if not result:
                logger.warning("PDF 解析失败")
                return False
            
            # 转换为 DataFrame
            df = pd.DataFrame([result])
            
            # 显示解析结果
            self._show_dataframe_preview(df)
            
            # 存储到数据库
            success = self.db_manager.insert_dataframe(df)
            
            if success:
                logger.info("数据存储成功")
                # 将处理过的PDF添加到知识库
                if self.knowledge_base_manager:
                    logger.info("正在将PDF内容添加到知识库...")
                    try:
                        self.knowledge_base_manager.add_pdf_to_collection(pdf_path, collection_name="financial_reports")
                    except Exception as e:
                        logger.error(f"无法将 {pdf_path} 添加到知识库: {e}")
                return True
            else:
                logger.error("数据存储失败")
                return False
                
        except Exception as e:
            logger.error(f"处理单个 PDF 失败：{str(e)}")
            return False
    
    def query_reports(self, 
                     stock_code: str = None,
                     company_name: str = None,
                     start_date: str = None,
                     end_date: str = None,
                     limit: int = 100) -> pd.DataFrame:
        """
        查询财报数据
        
        @param stock_code: 股票代码（可选）
        @param company_name: 公司名称（可选）
        @param start_date: 开始日期（可选）
        @param end_date: 结束日期（可选）
        @param limit: 返回记录数限制
        @return: 查询结果 DataFrame
        """
        try:
            logger.info("查询财报数据...")
            df = self.db_manager.query_data(
                stock_code=stock_code,
                company_name=company_name,
                start_date=start_date,
                end_date=end_date,
                limit=limit
            )
            
            if not df.empty:
                logger.info(f"查询到 {len(df)} 条记录")
                self._show_dataframe_preview(df)
            else:
                logger.info("没有查询到数据")
            
            return df
            
        except Exception as e:
            logger.error(f"查询数据失败：{str(e)}")
            return pd.DataFrame()
    
    def export_to_csv(self, output_file: str = None, **query_params) -> bool:
        """
        导出数据到 CSV 文件
        
        @param output_file: 输出文件路径
        @param query_params: 查询参数
        @return: 导出是否成功
        """
        try:
            if not output_file:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = f"financial_reports_{timestamp}.csv"
            
            # 查询数据
            df = self.query_reports(**query_params)
            
            if df.empty:
                logger.warning("没有数据可导出")
                return False
            
            # 导出到 CSV
            df.to_csv(output_file, index=False, encoding='utf-8-sig')
            logger.info(f"数据已导出到：{output_file}")
            
            return True
            
        except Exception as e:
            logger.error(f"导出数据失败：{str(e)}")
            return False
    
    def _show_dataframe_preview(self, df: pd.DataFrame, max_rows: int = 5):
        """
        显示 DataFrame 预览
        
        @param df: 要显示的 DataFrame
        @param max_rows: 最大显示行数
        """
        if df.empty:
            logger.info("DataFrame 为空")
            return
        
        logger.info(f"DataFrame 形状：{df.shape}")
        logger.info("数据预览：")
        
        # 显示前几行
        preview_df = df.head(max_rows)
        for index, row in preview_df.iterrows():
            logger.info(f"  行 {index + 1}:")
            for col in df.columns:
                value = row[col]
                if pd.isna(value):
                    value = "N/A"
                logger.info(f"    {col}: {value}")
    
    def _show_database_statistics(self):
        """
        显示数据库统计信息
        """
        try:
            stats = self.db_manager.get_statistics()
            if stats:
                logger.info("数据库统计信息：")
                for key, value in stats.items():
                    logger.info(f"  {key}: {value}")
        except Exception as e:
            logger.warning(f"获取统计信息失败：{str(e)}")
    
    def close(self):
        """
        关闭数据库连接
        """
        if hasattr(self, 'db_manager'):
            self.db_manager.close()


def main():
    """
    主函数：命令行接口
    """
    parser = argparse.ArgumentParser(description='财报数据处理工具')
    parser.add_argument('--pdf-dir', type=str, default='data/reports',
                       help='PDF 文件目录路径（默认：data/reports）')
    parser.add_argument('--pdf-file', type=str,
                       help='单个 PDF 文件路径')
    parser.add_argument('--query', action='store_true',
                       help='查询数据库中的数据')
    parser.add_argument('--export', type=str,
                       help='导出数据到 CSV 文件')
    parser.add_argument('--stock-code', type=str,
                       help='股票代码（用于查询）')
    parser.add_argument('--company-name', type=str,
                       help='公司名称（用于查询）')
    parser.add_argument('--start-date', type=str,
                       help='开始日期（格式：YYYY-MM-DD）')
    parser.add_argument('--end-date', type=str,
                       help='结束日期（格式：YYYY-MM-DD）')
    parser.add_argument('--limit', type=int, default=100,
                       help='查询记录数限制（默认：100）')
    
    args = parser.parse_args()
    
    # 创建处理器
    processor = None
    try:
        processor = FinancialReportProcessor()
        
        if args.pdf_file:
            # 处理单个 PDF 文件
            success = processor.process_single_pdf(args.pdf_file)
            if success:
                print(f"✅ 成功处理文件：{args.pdf_file}")
            else:
                print(f"❌ 处理文件失败：{args.pdf_file}")
                
        elif args.query or args.export:
            # 查询数据
            query_params = {
                'stock_code': args.stock_code,
                'company_name': args.company_name,
                'start_date': args.start_date,
                'end_date': args.end_date,
                'limit': args.limit
            }
            
            if args.export:
                # 导出数据
                success = processor.export_to_csv(args.export, **query_params)
                if success:
                    print(f"✅ 数据已导出到：{args.export}")
                else:
                    print("❌ 数据导出失败")
            else:
                # 仅查询显示
                df = processor.query_reports(**query_params)
                if not df.empty:
                    print("查询结果：")
                    print(df.to_string(index=False))
                else:
                    print("没有查询到数据")
                    
        else:
            # 处理 PDF 目录（默认操作）
            success = processor.process_pdf_directory(args.pdf_dir)
            if success:
                print(f"✅ 成功处理目录：{args.pdf_dir}")
            else:
                print(f"❌ 处理目录失败：{args.pdf_dir}")
    
    except KeyboardInterrupt:
        logger.info("用户中断操作")
        print("\n⚠️  操作已中断")
        
    except Exception as e:
        logger.error(f"程序执行失败：{str(e)}")
        print(f"❌ 程序执行失败：{str(e)}")
        
    finally:
        if processor:
            processor.close()


if __name__ == "__main__":
    print("=" * 60)
    print("📊 财报数据处理工具")
    print("=" * 60)
    print()
    
    # 如果没有命令行参数，显示使用说明并执行默认操作
    if len(sys.argv) == 1:
        print("🔧 使用说明：")
        print("  处理 PDF 目录：python process_financial_reports.py --pdf-dir data/reports")
        print("  处理单个文件：python process_financial_reports.py --pdf-file path/to/file.pdf")
        print("  查询数据：    python process_financial_reports.py --query --stock-code 000001")
        print("  导出数据：    python process_financial_reports.py --export output.csv")
        print()
        print("🚀 正在执行默认操作：处理 data/reports 目录...")
        print()
        
        # 执行默认操作
        processor = None
        try:
            processor = FinancialReportProcessor()
            success = processor.process_pdf_directory('data/reports')
            
            if success:
                print()
                print("✅ 处理完成！您现在可以在 Navicat 中查看数据：")
                print("   - 数据库：oytonghuashun")
                print("   - 表名：financial_reports")
                print("   - 字段：公司名称、股票代码、报告日期、营收、净利润、每股收益、爬取时间")
            else:
                print()
                print("❌ 处理失败，请检查：")
                print("   1. MySQL 服务是否正在运行")
                print("   2. 数据库连接配置是否正确（用户名：root，密码：123456）")
                print("   3. data/reports 目录是否存在 PDF 文件")
                
        except Exception as e:
            print(f"❌ 程序执行失败：{str(e)}")
            print()
            print("🔍 常见问题解决方案：")
            print("   1. 确保 MySQL 服务正在运行")
            print("   2. 确保已安装所有依赖：pip install -r requirements.txt")
            print("   3. 确保数据库用户名和密码正确")
            
        finally:
            if processor:
                processor.close()
    else:
        main()