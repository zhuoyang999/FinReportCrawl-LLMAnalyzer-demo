#!/usr/bin/env python3
"""
PDF解析调试脚本
"""

from data_processor.pdf_parser import FinancialReportParser
import os
import re

def debug_pdf_parsing():
    parser = FinancialReportParser()
    pdf_path = 'data/reports/000009/2023/annual/000009_中国宝安_2022年年度报告_1216413578.pdf'
    
    print('=== PDF解析调试 ===')
    print(f'PDF路径: {pdf_path}')
    print(f'文件存在: {os.path.exists(pdf_path)}')
    print(f'文件名: {os.path.basename(pdf_path)}')
    
    # 提取文本
    print('\n=== 文本提取 ===')
    text_content = parser.extract_text_from_pdf(pdf_path)
    print(f'文本长度: {len(text_content)}')
    print(f'文本前1000字符:')
    print(text_content[:1000])
    print('...')
    
    # 测试公司信息解析
    print('\n=== 公司信息解析 ===')
    company_name, stock_code = parser.parse_company_info(pdf_path, text_content)
    print(f'解析结果:')
    print(f'  公司名称: "{company_name}"')
    print(f'  股票代码: "{stock_code}"')
    
    # 测试路径解析
    print('\n=== 路径解析测试 ===')
    path_parts = pdf_path.split(os.sep)
    print(f'路径分割: {path_parts}')
    for i, part in enumerate(path_parts):
        is_stock_code = bool(re.match(r'^\d{6}$', part))
        print(f'  [{i}] "{part}" - 是否6位数字: {is_stock_code}')
    
    # 测试文件名解析
    print('\n=== 文件名解析测试 ===')
    filename = os.path.basename(pdf_path)
    print(f'文件名: {filename}')
    name_match = re.search(r'\d{6}_([^_]+)_', filename)
    if name_match:
        print(f'从文件名提取的公司名称: "{name_match.group(1)}"')
    else:
        print('文件名解析失败')
    
    # 测试文本中的公司名称模式
    print('\n=== 文本中公司名称搜索 ===')
    company_patterns = [
        r'公司名称[：:\s]*([^\n\r]+)',
        r'公司全称[：:\s]*([^\n\r]+)',
        r'([^，,。.\n\r]+)股份有限公司',
        r'([^，,。.\n\r]+)有限公司'
    ]
    
    for i, pattern in enumerate(company_patterns):
        matches = re.findall(pattern, text_content, re.IGNORECASE)
        print(f'  模式[{i}]: {pattern}')
        if matches:
            print(f'    匹配结果: {matches[:5]}')  # 只显示前5个匹配
        else:
            print(f'    无匹配')

if __name__ == "__main__":
    debug_pdf_parsing()