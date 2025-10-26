#!/usr/bin/env python3
"""
批量处理PDF文件测试脚本
"""

from data_processor.pdf_parser import FinancialReportParser
from data_processor.database_manager import DatabaseManager
import os
import pandas as pd

def main():
    print('=== 批量处理PDF文件测试 ===')

    # 初始化
    parser = FinancialReportParser()
    db_manager = DatabaseManager()

    # 查找所有PDF文件
    reports_dir = 'data/reports'
    pdf_files = []

    for root, dirs, files in os.walk(reports_dir):
        for file in files:
            if file.endswith('.pdf'):
                pdf_path = os.path.join(root, file)
                pdf_files.append(pdf_path)

    print(f'找到 {len(pdf_files)} 个PDF文件')

    # 处理前3个PDF文件作为测试
    test_files = pdf_files[:3]
    print(f'测试处理前 {len(test_files)} 个文件:')

    success_count = 0
    for i, pdf_path in enumerate(test_files, 1):
        print(f'\n--- 处理第 {i} 个文件 ---')
        print(f'文件: {os.path.basename(pdf_path)}')
        
        try:
            # 解析PDF
            result = parser.parse_single_pdf(pdf_path)
            print(f'✅ 解析成功: {result["company_name"]} ({result["stock_code"]})')
            
            if result['revenue']:
                print(f'   营业收入: {result["revenue"]:,.0f} 元')
            else:
                print('   营业收入: 未提取')
                
            if result['net_profit']:
                print(f'   净利润: {result["net_profit"]:,.0f} 元')
            else:
                print('   净利润: 未提取')
            
            # 插入数据库
            df = pd.DataFrame([result])
            db_manager.insert_dataframe(df)
            print('✅ 数据库插入成功')
            success_count += 1
            
        except Exception as e:
            print(f'❌ 处理失败: {e}')

    print(f'\n=== 处理结果 ===')
    print(f'成功处理: {success_count}/{len(test_files)} 个文件')

    print('\n=== 最终数据库状态 ===')
    final_data = db_manager.query_data()
    print(f'数据库中共有 {len(final_data)} 条记录')

    if len(final_data) > 0:
        print('所有记录概览:')
        for idx, row in final_data.iterrows():
            print(f'  {idx+1}. {row["company_name"]} ({row["stock_code"]}) - {row["report_date"]}')

if __name__ == '__main__':
    main()