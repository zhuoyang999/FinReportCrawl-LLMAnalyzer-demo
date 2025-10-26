"""
PDF 财报解析模块
功能：将爬取的 PDF 财报文件解析为 pandas DataFrame 格式
作者：Python 后端工程师
"""

import os
import re
import pandas as pd
import pdfplumber
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FinancialReportParser:
    """
    财报 PDF 解析器
    
    主要功能：
    1. 解析 PDF 财报文件
    2. 提取关键财务数据
    3. 转换为标准化的 DataFrame 格式
    """
    
    def __init__(self):
        """初始化解析器"""
        # 关键财务指标的正则表达式模式
        self.patterns = {
            'revenue': [
                r'营业收入[：:\s]*([0-9,]+\.?[0-9]*)',
                r'主营业务收入[：:\s]*([0-9,]+\.?[0-9]*)',
                r'营业总收入[：:\s]*([0-9,]+\.?[0-9]*)'
            ],
            'net_profit': [
                r'净利润[：:\s]*([0-9,]+\.?[0-9]*)',
                r'归属于母公司所有者的净利润[：:\s]*([0-9,]+\.?[0-9]*)',
                r'归属于上市公司股东的净利润[：:\s]*([0-9,]+\.?[0-9]*)'
            ],
            'eps': [
                r'基本每股收益[：:\s]*([0-9,]+\.?[0-9]*)',
                r'每股收益[：:\s]*([0-9,]+\.?[0-9]*)',
                r'基本每股收益\(元/股\)[：:\s]*([0-9,]+\.?[0-9]*)'
            ]
        }
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """
        从 PDF 文件中提取文本内容
        
        @param pdf_path: PDF 文件路径
        @return: 提取的文本内容
        """
        try:
            text_content = ""
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_content += page_text + "\n"
            
            logger.info(f"成功提取 PDF 文本，文件：{pdf_path}")
            return text_content
            
        except Exception as e:
            logger.error(f"提取 PDF 文本失败，文件：{pdf_path}，错误：{str(e)}")
            return ""
    
    def extract_tables_from_pdf(self, pdf_path: str) -> List[pd.DataFrame]:
        """
        从 PDF 文件中提取表格数据
        
        @param pdf_path: PDF 文件路径
        @return: 表格数据列表
        """
        tables = []
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages):
                    page_tables = page.extract_tables()
                    if page_tables:
                        for table_num, table in enumerate(page_tables):
                            if table and len(table) > 1:  # 确保表格有数据
                                df = pd.DataFrame(table[1:], columns=table[0])
                                df = df.dropna(how='all')  # 删除全空行
                                if not df.empty:
                                    tables.append(df)
                                    logger.info(f"提取表格：页面 {page_num + 1}，表格 {table_num + 1}")
            
            logger.info(f"成功提取 {len(tables)} 个表格，文件：{pdf_path}")
            return tables
            
        except Exception as e:
            logger.error(f"提取 PDF 表格失败，文件：{pdf_path}，错误：{str(e)}")
            return []
    
    def extract_financial_data(self, text: str) -> Dict[str, Optional[float]]:
        """
        从文本中提取关键财务数据
        
        @param text: PDF 文本内容
        @return: 财务数据字典
        """
        financial_data = {
            'revenue': None,      # 营业收入
            'net_profit': None,   # 净利润
            'eps': None          # 每股收益
        }
        
        # 清理文本，移除多余空格和换行
        clean_text = re.sub(r'\s+', ' ', text)
        
        # 提取各项财务指标
        for key, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    try:
                        # 清理数字字符串，移除逗号
                        value_str = matches[0].replace(',', '')
                        value = float(value_str)
                        financial_data[key] = value
                        logger.info(f"提取到 {key}: {value}")
                        break  # 找到第一个匹配就停止
                    except ValueError:
                        continue
        
        return financial_data
    
    def parse_company_info(self, pdf_path: str, text: str) -> Tuple[str, str]:
        """
        从 PDF 路径和文本中解析公司信息
        
        @param pdf_path: PDF 文件路径
        @param text: PDF 文本内容
        @return: (公司名称, 股票代码)
        """
        # 从文件路径中提取股票代码
        stock_code = ""
        # 使用正确的路径分隔符，同时支持Windows和Unix
        path_parts = pdf_path.replace('\\', '/').split('/')
        for part in path_parts:
            if re.match(r'^\d{6}$', part):  # 6位数字的股票代码
                stock_code = part
                break
        
        # 优先从文件名中提取公司名称（更准确）
        company_name = ""
        filename = os.path.basename(pdf_path)
        name_match = re.search(r'\d{6}_([^_]+)_', filename)
        if name_match:
            company_name = name_match.group(1)
        
        # 如果文件名解析失败，从文本中提取公司名称
        if not company_name:
            company_patterns = [
                r'([^，,。.\n\r\s]{2,20})股份有限公司',  # 匹配"XX股份有限公司"
                r'([^，,。.\n\r\s]{2,20})有限公司',     # 匹配"XX有限公司"
                r'公司全称[：:\s]*([^\n\r]+)',         # 匹配"公司全称：XX"
                r'公司名称[：:\s]*([^\n\r，,。.]+)',    # 匹配"公司名称：XX"（排除表格标题）
            ]
            
            for pattern in company_patterns:
                matches = re.findall(pattern, text, re.IGNORECASE)
                if matches:
                    # 过滤掉明显不是公司名称的匹配结果
                    for match in matches:
                        match = match.strip()
                        # 排除包含"主要业务"、"注册资本"等表格标题的匹配
                        if not any(keyword in match for keyword in ['主要业务', '注册资本', '总资产', '净资产', '营业收入', '营业利润']):
                            company_name = match
                            break
                    if company_name:
                        break
        
        logger.info(f"解析公司信息：{company_name} ({stock_code})")
        return company_name, stock_code
    
    def parse_report_date(self, pdf_path: str, text: str) -> str:
        """
        从 PDF 路径和文本中解析报告日期
        
        @param pdf_path: PDF 文件路径
        @param text: PDF 文本内容
        @return: 报告日期 (YYYY-MM-DD 格式)
        """
        # 从文件路径中提取年份
        year = ""
        path_parts = pdf_path.split(os.sep)
        for part in path_parts:
            if re.match(r'^\d{4}$', part):  # 4位数字的年份
                year = part
                break
        
        # 从文本中提取具体日期
        date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})/(\d{1,2})/(\d{1,2})'
        ]
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                year_found, month, day = matches[0]
                return f"{year_found}-{month.zfill(2)}-{day.zfill(2)}"
        
        # 如果没有找到具体日期，使用年份构造默认日期
        if year:
            # 判断是年报还是半年报
            if '半年' in text or '中报' in text:
                return f"{year}-06-30"  # 半年报默认6月30日
            else:
                return f"{year}-12-31"  # 年报默认12月31日
        
        # 如果都没有找到，返回当前日期
        return datetime.now().strftime("%Y-%m-%d")
    
    def parse_single_pdf(self, pdf_path: str) -> Optional[Dict]:
        """
        解析单个 PDF 文件
        
        @param pdf_path: PDF 文件路径
        @return: 解析结果字典
        """
        if not os.path.exists(pdf_path):
            logger.error(f"PDF 文件不存在：{pdf_path}")
            return None
        
        logger.info(f"开始解析 PDF：{pdf_path}")
        
        # 提取文本内容
        text_content = self.extract_text_from_pdf(pdf_path)
        if not text_content:
            logger.warning(f"无法提取文本内容：{pdf_path}")
            return None
        
        # 解析公司信息
        company_name, stock_code = self.parse_company_info(pdf_path, text_content)
        
        # 解析报告日期
        report_date = self.parse_report_date(pdf_path, text_content)
        
        # 提取财务数据
        financial_data = self.extract_financial_data(text_content)
        
        # 构造结果
        result = {
            'company_name': company_name,           # 公司名称
            'stock_code': stock_code,              # 股票代码
            'report_date': report_date,            # 报告日期
            'revenue': financial_data['revenue'],   # 营收
            'net_profit': financial_data['net_profit'],  # 净利润
            'eps': financial_data['eps'],          # 每股收益
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),  # 爬取时间
            'pdf_path': pdf_path                   # PDF 文件路径
        }
        
        logger.info(f"PDF 解析完成：{company_name} ({stock_code})")
        return result
    
    def parse_directory(self, directory_path: str) -> pd.DataFrame:
        """
        解析目录下的所有 PDF 文件
        
        @param directory_path: 包含 PDF 文件的目录路径
        @return: 包含所有解析结果的 DataFrame
        """
        results = []
        
        if not os.path.exists(directory_path):
            logger.error(f"目录不存在：{directory_path}")
            return pd.DataFrame()
        
        # 递归查找所有 PDF 文件
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_path = os.path.join(root, file)
                    result = self.parse_single_pdf(pdf_path)
                    if result:
                        results.append(result)
        
        if results:
            df = pd.DataFrame(results)
            logger.info(f"成功解析 {len(results)} 个 PDF 文件")
            return df
        else:
            logger.warning("没有成功解析任何 PDF 文件")
            return pd.DataFrame()


def main():
    """
    主函数：演示 PDF 解析功能
    """
    parser = FinancialReportParser()
    
    # 解析 data/reports 目录下的所有 PDF 文件
    reports_dir = "data/reports"
    df = parser.parse_directory(reports_dir)
    
    if not df.empty:
        print("解析结果预览：")
        print(df.head())
        
        # 保存为 CSV 文件
        output_file = "parsed_financial_reports.csv"
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        print(f"结果已保存到：{output_file}")
    else:
        print("没有解析到任何数据")


if __name__ == "__main__":
    main()