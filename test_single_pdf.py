#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
单个PDF文件处理测试脚本
测试文件：000001_平安银行_2022年年度报告_1216072952.pdf
"""

import os
import sys
import pandas as pd
from datetime import datetime
import logging

# 添加项目根目录到路径
sys.path.append(os.path.dirname(__file__))

from data_processor.pdf_parser import FinancialReportParser
from data_processor.database_manager import DatabaseManager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_single_pdf():
    """测试单个PDF文件的处理"""
    print("=" * 80)
    print("单个PDF文件处理测试")
    print("=" * 80)
    
    # 指定测试文件
    pdf_path = "data/reports/000001/2023/annual/000001_平安银行_2022年年度报告_1216072952.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"❌ 错误：文件不存在 - {pdf_path}")
        return
    
    print(f"📄 测试文件: {pdf_path}")
    print(f"📁 文件大小: {os.path.getsize(pdf_path) / 1024 / 1024:.2f} MB")
    
    # 创建PDF解析器
    parser = FinancialReportParser()
    
    print("\n" + "=" * 50)
    print("第1步：提取PDF文本内容")
    print("=" * 50)
    
    try:
        # 提取文本
        text = parser.extract_text_from_pdf(pdf_path)
        print(f"✅ 文本提取成功")
        print(f"📊 文本长度: {len(text):,} 字符")
        print(f"📝 文本预览 (前500字符):")
        print("-" * 50)
        print(text[:500])
        print("-" * 50)
        
    except Exception as e:
        print(f"❌ 文本提取失败: {str(e)}")
        return
    
    print("\n" + "=" * 50)
    print("第2步：解析公司信息")
    print("=" * 50)
    
    try:
        # 解析公司信息
        company_info = parser.parse_company_info(pdf_path, text)
        print(f"✅ 公司信息解析成功")
        print(f"🏢 公司名称: {company_info.get('company_name', '未知')}")
        print(f"📈 股票代码: {company_info.get('stock_code', '未知')}")
        
    except Exception as e:
        print(f"❌ 公司信息解析失败: {str(e)}")
        company_info = {'company_name': '未知', 'stock_code': '000000'}
    
    print("\n" + "=" * 50)
    print("第3步：解析报告日期")
    print("=" * 50)
    
    try:
        # 解析报告日期
        report_date = parser.parse_report_date(pdf_path, text)
        print(f"✅ 报告日期解析成功")
        print(f"📅 报告日期: {report_date}")
        
    except Exception as e:
        print(f"❌ 报告日期解析失败: {str(e)}")
        report_date = "2022-01-01"
    
    print("\n" + "=" * 50)
    print("第4步：提取财务数据")
    print("=" * 50)
    
    try:
        # 提取财务数据
        financial_data = parser.extract_financial_data(text)
        print(f"✅ 财务数据提取成功")
        print(f"💰 营业收入: {financial_data.get('revenue', 'N/A')} 万元")
        print(f"💵 净利润: {financial_data.get('net_profit', 'N/A')} 万元")
        print(f"📊 每股收益: {financial_data.get('eps', 'N/A')} 元")
        
    except Exception as e:
        print(f"❌ 财务数据提取失败: {str(e)}")
        financial_data = {'revenue': None, 'net_profit': None, 'eps': None}
    
    print("\n" + "=" * 50)
    print("第5步：数据库存储测试")
    print("=" * 50)
    
    try:
        # 准备数据
        data = {
            'company_name': company_info.get('company_name', '未知'),
            'stock_code': company_info.get('stock_code', '000000'),
            'report_date': report_date,
            'revenue': financial_data.get('revenue'),
            'net_profit': financial_data.get('net_profit'),
            'eps': financial_data.get('eps'),
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        
        print("📋 准备存储的数据:")
        for key, value in data.items():
            print(f"   {key}: {value}")
        
        # 创建DataFrame
        df = pd.DataFrame([data])
        
        # 创建数据库管理器
        db_manager = DatabaseManager()
        
        # 获取插入前的统计信息
        stats_before = db_manager.get_statistics()
        print(f"\n📊 插入前数据库记录数: {stats_before.get('total_records', 0)}")
        
        # 插入数据
        success = db_manager.insert_dataframe(df)
        
        if success:
            print("✅ 数据库存储成功")
            
            # 获取插入后的统计信息
            stats_after = db_manager.get_statistics()
            new_records = stats_after.get('total_records', 0) - stats_before.get('total_records', 0)
            print(f"📊 插入后数据库记录数: {stats_after.get('total_records', 0)}")
            print(f"📈 新增记录数: {new_records}")
            
            if new_records == 0:
                print("ℹ️  该记录已存在，重复检查功能正常工作")
            
            # 查询验证
            print("\n🔍 查询验证 - 最新的3条记录:")
            latest_data = db_manager.query_data(limit=3)
            if not latest_data.empty:
                for idx, row in latest_data.iterrows():
                    print(f"   {idx+1}. {row['company_name']} ({row['stock_code']}) - {row['report_date']}")
            
        else:
            print("❌ 数据库存储失败")
        
        # 关闭数据库连接
        db_manager.close()
        
    except Exception as e:
        print(f"❌ 数据库操作失败: {str(e)}")
    
    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)

def main():
    """主函数"""
    print("开始单个PDF文件处理测试")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        test_single_pdf()
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        print(f"❌ 测试失败: {str(e)}")

if __name__ == "__main__":
    main()