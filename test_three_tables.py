#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试三表数据库结构
验证 financial_reports、report_contents、financial_metrics 三个表的创建和数据操作
"""

import sys
import os
from datetime import datetime

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_processor.database_manager import DatabaseManager

def test_three_tables():
    """测试三表数据库结构"""
    print("=" * 60)
    print("测试三表数据库结构")
    print("=" * 60)
    
    try:
        # 初始化数据库管理器
        print("1. 初始化数据库管理器...")
        db_manager = DatabaseManager()
        print("✓ 数据库管理器初始化成功")
        
        # 测试插入财务报告元数据
        print("\n2. 测试插入财务报告元数据...")
        test_report_data = {
            'company_name': ['测试银行'],
            'stock_code': ['000001'],
            'report_date': ['2023-12-31'],
            'report_year': [2023],
            'report_type': ['年报'],
            'report_title': ['测试银行2023年年度报告'],
            'revenue': [1000000.0],
            'net_profit': [100000.0],
            'eps': [1.5],
            'pdf_url': ['http://example.com/test.pdf'],
            'local_path': ['/data/reports/test.pdf'],
            'file_size': [1024000],
            'crawl_status': ['success'],
            'crawled_at': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
            'crawl_time': [datetime.now().strftime("%Y-%m-%d %H:%M:%S")]
        }
        
        import pandas as pd
        test_df = pd.DataFrame(test_report_data)
        success = db_manager.insert_dataframe(test_df)
        
        if success:
            print("✓ 财务报告元数据插入成功")
            
            # 获取刚插入的报告ID
            recent_reports = db_manager.query_data(limit=1)
            if not recent_reports.empty:
                report_id = recent_reports.iloc[0]['id']
                print(f"✓ 获取报告ID: {report_id}")
                
                # 测试插入报告内容
                print("\n3. 测试插入报告内容...")
                content_success = db_manager.insert_report_content(
                    report_id=report_id,
                    content_type="overview",
                    extracted_text="这是测试银行2023年年度报告的概述部分...",
                    page_count=1,
                    extraction_method="pdfplumber",
                    confidence_score=0.95
                )
                
                if content_success:
                    print("✓ 报告内容插入成功")
                    
                    # 查询报告内容
                    contents = db_manager.query_report_contents(report_id=report_id)
                    print(f"✓ 查询到 {len(contents)} 条报告内容记录")
                    if not contents.empty:
                        print(f"  - 内容类型: {contents.iloc[0]['content_type']}")
                        print(f"  - 提取方法: {contents.iloc[0]['extraction_method']}")
                        print(f"  - 置信度: {contents.iloc[0]['confidence_score']}")
                
                # 测试插入财务指标
                print("\n4. 测试插入财务指标...")
                metrics_data = [
                    ("营业收入", 1000000.0, "万元", None, "FY"),
                    ("净利润", 100000.0, "万元", None, "FY"),
                    ("每股收益", 1.5, "元", "净利润/总股本", "FY"),
                    ("ROE", 15.5, "%", "净利润/平均净资产×100%", "FY")
                ]
                
                for metric_name, value, unit, method, period in metrics_data:
                    metric_success = db_manager.insert_financial_metric(
                        report_id=report_id,
                        metric_name=metric_name,
                        metric_value=value,
                        metric_unit=unit,
                        calculation_method=method,
                        period_type=period
                    )
                    if metric_success:
                        print(f"✓ 财务指标插入成功: {metric_name}")
                
                # 查询财务指标
                print("\n5. 查询财务指标...")
                metrics = db_manager.query_financial_metrics(report_id=report_id)
                print(f"✓ 查询到 {len(metrics)} 条财务指标记录")
                if not metrics.empty:
                    for _, metric in metrics.iterrows():
                        print(f"  - {metric['metric_name']}: {metric['metric_value']} {metric['metric_unit'] or ''}")
                
                # 测试统计信息
                print("\n6. 获取数据库统计信息...")
                stats = db_manager.get_statistics()
                print("✓ 数据库统计信息:")
                for key, value in stats.items():
                    print(f"  - {key}: {value}")
                
        else:
            print("✗ 财务报告元数据插入失败")
            
    except Exception as e:
        print(f"✗ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
    
    finally:
        # 关闭数据库连接
        try:
            db_manager.close()
            print("\n✓ 数据库连接已关闭")
        except:
            pass
    
    print("\n" + "=" * 60)
    print("三表数据库结构测试完成")
    print("=" * 60)

if __name__ == "__main__":
    test_three_tables()