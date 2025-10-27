#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from data_processor.pdf_parser import FinancialReportParser

def test_pdf_parsing():
    """测试PDF解析的详细结果"""
    
    # 测试文件路径
    pdf_path = "data/reports/000001/2023/annual/000001_平安银行_2022年年度报告_1216072952.pdf"
    
    print("=" * 60)
    print("PDF解析详细测试")
    print("=" * 60)
    print(f"📄 测试文件: {pdf_path}")
    
    if not os.path.exists(pdf_path):
        print(f"❌ 文件不存在: {pdf_path}")
        return
    
    # 创建解析器
    parser = FinancialReportParser()
    
    try:
        # 1. 提取文本
        print("\n🔍 第1步：提取PDF文本")
        text = parser.extract_text_from_pdf(pdf_path)
        print(f"✅ 文本提取成功，长度: {len(text):,} 字符")
        
        # 2. 解析公司信息
        print("\n🏢 第2步：解析公司信息")
        company_name, stock_code = parser.parse_company_info(pdf_path, text)
        print(f"公司名称: {company_name}")
        print(f"股票代码: {stock_code}")
        
        # 3. 解析报告日期
        print("\n📅 第3步：解析报告日期")
        report_date = parser.parse_report_date(pdf_path, text)
        print(f"报告日期: {report_date}")
        
        # 4. 提取财务数据
        print("\n💰 第4步：提取财务数据")
        financial_data = parser.extract_financial_data(text)
        print(f"营业收入: {financial_data.get('revenue', 'N/A')}")
        print(f"净利润: {financial_data.get('net_profit', 'N/A')}")
        print(f"每股收益: {financial_data.get('eps', 'N/A')}")
        
        # 5. 完整解析
        print("\n📊 第5步：完整解析结果")
        result = parser.parse_single_pdf(pdf_path)
        print("完整解析结果:")
        if result:
            for key, value in result.items():
                print(f"  {key}: {value}")
        else:
            print("  解析失败，返回None")
            
    except Exception as e:
        print(f"❌ 解析失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_pdf_parsing()