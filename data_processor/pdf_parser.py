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
        # 关键财务指标的正则表达式模式 - 改进版
        self.patterns = {
            'revenue': [
                # 营业收入相关模式，考虑表格格式和单位
                r'营业收入[：:\s]*([0-9,]+\.?[0-9]*)[万元]*',
                r'主营业务收入[：:\s]*([0-9,]+\.?[0-9]*)[万元]*',
                r'营业总收入[：:\s]*([0-9,]+\.?[0-9]*)[万元]*',
                r'一、营业收入[：:\s]*([0-9,]+\.?[0-9]*)',
                r'营业收入\s+([0-9,]+\.?[0-9]*)',
                # 表格中的营业收入
                r'营业收入\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+营业收入'
            ],
            'net_profit': [
                # 净利润相关模式
                r'净利润[：:\s]*([0-9,]+\.?[0-9]*)[万元]*',
                r'归属于母公司所有者的净利润[：:\s]*([0-9,]+\.?[0-9]*)[万元]*',
                r'归属于上市公司股东的净利润[：:\s]*([0-9,]+\.?[0-9]*)[万元]*',
                r'三、净利润[：:\s]*([0-9,]+\.?[0-9]*)',
                r'净利润\s+([0-9,]+\.?[0-9]*)',
                # 表格中的净利润
                r'净利润\s+(\d{1,3}(?:,\d{3})*(?:\.\d+)?)',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d+)?)\s+净利润'
            ],
            'eps': [
                # 每股收益相关模式
                r'基本每股收益[：:\s]*([0-9,]+\.?[0-9]*)[元]*',
                r'每股收益[：:\s]*([0-9,]+\.?[0-9]*)[元]*',
                r'基本每股收益\(元/股\)[：:\s]*([0-9,]+\.?[0-9]*)',
                r'基本每股收益\s+([0-9,]+\.?[0-9]*)',
                r'每股收益\s+(\d+\.?\d*)',
                # 表格中的每股收益
                r'基本每股收益\s+(\d+\.?\d*)',
                r'(\d+\.?\d*)\s+基本每股收益'
            ]
        }
        
        # 报告日期的正则表达式模式
        self.date_patterns = [
            r'(\d{4})年(\d{1,2})月(\d{1,2})日',
            r'(\d{4})-(\d{1,2})-(\d{1,2})',
            r'(\d{4})年度报告',
            r'(\d{4})年年度报告',
            r'(\d{4})年第[一二三四]季度报告',
            r'(\d{4})年半年度报告'
        ]
    
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
            values_found = []
            
            for pattern in patterns:
                matches = re.findall(pattern, clean_text, re.IGNORECASE)
                if matches:
                    for match in matches:
                        try:
                            # 清理数字字符串，移除逗号
                            value_str = str(match).replace(',', '').replace('万', '').replace('元', '').strip()
                            if value_str and value_str.replace('.', '').isdigit():
                                value = float(value_str)
                                # 数据合理性检查
                                if self._is_reasonable_value(key, value):
                                    values_found.append(value)
                        except (ValueError, TypeError):
                            continue
            
            # 选择最合理的值
            if values_found:
                # 对于营业收入和净利润，选择较大的值（通常更准确）
                if key in ['revenue', 'net_profit']:
                    # 过滤掉明显过小的值
                    filtered_values = [v for v in values_found if v > 1000]  # 大于1000万
                    if filtered_values:
                        financial_data[key] = max(filtered_values)
                    else:
                        financial_data[key] = max(values_found) if values_found else None
                else:  # eps
                    # 每股收益选择中位数
                    values_found.sort()
                    mid_idx = len(values_found) // 2
                    financial_data[key] = values_found[mid_idx]
                
                logger.info(f"提取到 {key}: {financial_data[key]} (候选值: {values_found})")
        
        return financial_data
    
    def _is_reasonable_value(self, key: str, value: float) -> bool:
        """
        检查财务数据的合理性
        
        @param key: 数据类型
        @param value: 数值
        @return: 是否合理
        """
        if key == 'revenue':
            # 营业收入应该在合理范围内（万元）
            return 0 < value < 100000000  # 0到1万亿万元
        elif key == 'net_profit':
            # 净利润可以为负，但不应该过大
            return -10000000 < value < 10000000  # -1千亿到1千亿万元
        elif key == 'eps':
            # 每股收益通常在合理范围内
            return -100 < value < 1000  # -100到1000元
        return True
    
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
        @return: 报告日期字符串 (YYYY-MM-DD)
        """
        # 首先尝试从文件名中提取年份
        filename = os.path.basename(pdf_path)
        year_from_filename = None
        
        # 从文件名中提取年份
        year_match = re.search(r'(\d{4})年', filename)
        if year_match:
            year_from_filename = year_match.group(1)
        
        # 尝试从文件路径中提取年份
        if not year_from_filename:
            path_year_match = re.search(r'/(\d{4})/', pdf_path.replace('\\', '/'))
            if path_year_match:
                year_from_filename = path_year_match.group(1)
        
        # 从文本中查找具体日期
        for pattern in self.date_patterns:
            matches = re.findall(pattern, text)
            if matches:
                match = matches[0]
                if isinstance(match, tuple):
                    if len(match) >= 3:  # 完整日期
                        year, month, day = match[0], match[1], match[2]
                        try:
                            # 验证日期的合理性
                            date_obj = datetime.strptime(f"{year}-{month.zfill(2)}-{day.zfill(2)}", "%Y-%m-%d")
                            return date_obj.strftime("%Y-%m-%d")
                        except ValueError:
                            continue
                    elif len(match) == 1:  # 只有年份
                        year = match[0]
                        # 如果是年度报告，默认使用12月31日
                        if '年度报告' in text or '年报' in text:
                            return f"{year}-12-31"
                        # 如果是半年度报告，使用6月30日
                        elif '半年度报告' in text or '中报' in text:
                            return f"{year}-06-30"
                        # 季度报告
                        elif '第一季度' in text or '一季报' in text:
                            return f"{year}-03-31"
                        elif '第三季度' in text or '三季报' in text:
                            return f"{year}-09-30"
                        else:
                            return f"{year}-12-31"
                else:  # 单个匹配
                    year = match
                    return f"{year}-12-31"
        
        # 如果从文本中找不到，使用文件名中的年份
        if year_from_filename:
            # 根据文件名判断报告类型
            if '年度报告' in filename or '年报' in filename:
                return f"{year_from_filename}-12-31"
            elif '半年度报告' in filename or '中报' in filename:
                return f"{year_from_filename}-06-30"
            elif '第一季度' in filename or '一季报' in filename:
                return f"{year_from_filename}-03-31"
            elif '第三季度' in filename or '三季报' in filename:
                return f"{year_from_filename}-09-30"
            else:
                return f"{year_from_filename}-12-31"
        
        # 默认返回当前日期
        logger.warning(f"无法解析报告日期，使用当前日期：{pdf_path}")
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