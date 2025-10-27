#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
改进后的PDF处理功能测试脚本
测试内容：
1. PDF内容提取功能
2. 财务数据解析准确性
3. 报告日期解析
4. 数据库存储和重复检查
5. 数据质量验证
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

def test_pdf_extraction():
    """测试PDF内容提取功能"""
    print("=" * 60)
    print("测试 1: PDF内容提取功能")
    print("=" * 60)
    
    parser = FinancialReportParser()
    
    # 测试PDF文件路径
    pdf_directory = "data/financial_reports"
    
    if not os.path.exists(pdf_directory):
        print(f"警告：PDF目录 {pdf_directory} 不存在")
        return None
    
    # 获取PDF文件列表
    pdf_files = [f for f in os.listdir(pdf_directory) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"警告：在 {pdf_directory} 中没有找到PDF文件")
        return None
    
    print(f"找到 {len(pdf_files)} 个PDF文件")
    
    # 测试前3个PDF文件
    test_files = pdf_files[:3]
    results = []
    
    for pdf_file in test_files:
        pdf_path = os.path.join(pdf_directory, pdf_file)
        print(f"\n处理文件: {pdf_file}")
        
        try:
            # 提取文本
            text = parser.extract_text_from_pdf(pdf_path)
            print(f"  文本长度: {len(text)} 字符")
            
            # 解析公司信息
            company_info = parser.parse_company_info(pdf_path, text)
            print(f"  公司信息: {company_info}")
            
            # 解析报告日期
            report_date = parser.parse_report_date(pdf_path, text)
            print(f"  报告日期: {report_date}")
            
            # 提取财务数据
            financial_data = parser.extract_financial_data(text)
            print(f"  财务数据: {financial_data}")
            
            # 收集结果
            result = {
                'file_name': pdf_file,
                'company_name': company_info.get('company_name', '未知'),
                'stock_code': company_info.get('stock_code', '000000'),
                'report_date': report_date,
                'revenue': financial_data.get('revenue'),
                'net_profit': financial_data.get('net_profit'),
                'eps': financial_data.get('eps'),
                'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            results.append(result)
            
        except Exception as e:
            print(f"  错误: {str(e)}")
    
    return results

def test_database_storage(test_data):
    """测试数据库存储功能"""
    print("\n" + "=" * 60)
    print("测试 2: 数据库存储功能")
    print("=" * 60)
    
    if not test_data:
        print("没有测试数据，跳过数据库测试")
        return
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    # 获取插入前的统计信息
    print("\n插入前的数据库统计:")
    stats_before = db_manager.get_statistics()
    for key, value in stats_before.items():
        print(f"  {key}: {value}")
    
    # 转换为DataFrame
    df = pd.DataFrame(test_data)
    print(f"\n准备插入 {len(df)} 条记录")
    print("数据预览:")
    print(df.to_string(index=False))
    
    # 插入数据
    success = db_manager.insert_dataframe(df)
    
    if success:
        print("\n数据插入成功!")
        
        # 获取插入后的统计信息
        print("\n插入后的数据库统计:")
        stats_after = db_manager.get_statistics()
        for key, value in stats_after.items():
            print(f"  {key}: {value}")
        
        # 计算新增记录数
        new_records = stats_after.get('total_records', 0) - stats_before.get('total_records', 0)
        print(f"\n实际新增记录数: {new_records}")
        
        # 查询最新的数据
        print("\n最新的5条记录:")
        latest_data = db_manager.query_data(limit=5)
        if not latest_data.empty:
            print(latest_data.to_string(index=False))
        
    else:
        print("数据插入失败!")
    
    # 关闭数据库连接
    db_manager.close()

def test_duplicate_handling():
    """测试重复数据处理"""
    print("\n" + "=" * 60)
    print("测试 3: 重复数据处理")
    print("=" * 60)
    
    # 创建测试数据（包含重复记录）
    test_data = [
        {
            'company_name': '测试公司A',
            'stock_code': '000001',
            'report_date': '2023-12-31',
            'revenue': 1000000.0,
            'net_profit': 100000.0,
            'eps': 1.5,
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            'company_name': '测试公司A',
            'stock_code': '000001',
            'report_date': '2023-12-31',  # 重复记录
            'revenue': 1000000.0,
            'net_profit': 100000.0,
            'eps': 1.5,
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        },
        {
            'company_name': '测试公司B',
            'stock_code': '000002',
            'report_date': '2023-12-31',
            'revenue': 2000000.0,
            'net_profit': 200000.0,
            'eps': 2.0,
            'crawl_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    ]
    
    df = pd.DataFrame(test_data)
    print(f"准备插入 {len(df)} 条记录（包含重复数据）")
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    # 获取插入前的统计信息
    stats_before = db_manager.get_statistics()
    print(f"插入前总记录数: {stats_before.get('total_records', 0)}")
    
    # 插入数据
    success = db_manager.insert_dataframe(df)
    
    if success:
        # 获取插入后的统计信息
        stats_after = db_manager.get_statistics()
        new_records = stats_after.get('total_records', 0) - stats_before.get('total_records', 0)
        print(f"插入后总记录数: {stats_after.get('total_records', 0)}")
        print(f"实际新增记录数: {new_records}")
        
        if new_records < len(df):
            print("✓ 重复数据检查功能正常工作")
        else:
            print("⚠ 重复数据检查可能存在问题")
    
    # 关闭数据库连接
    db_manager.close()

def test_data_quality():
    """测试数据质量"""
    print("\n" + "=" * 60)
    print("测试 4: 数据质量验证")
    print("=" * 60)
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    # 查询所有数据
    all_data = db_manager.query_data(limit=1000)
    
    if all_data.empty:
        print("数据库中没有数据")
        db_manager.close()
        return
    
    print(f"数据库中共有 {len(all_data)} 条记录")
    
    # 检查数据质量
    print("\n数据质量检查:")
    
    # 1. 检查空值
    null_counts = all_data.isnull().sum()
    print("空值统计:")
    for column, count in null_counts.items():
        if count > 0:
            print(f"  {column}: {count} 个空值")
    
    # 2. 检查财务数据范围
    if 'revenue' in all_data.columns:
        revenue_stats = all_data['revenue'].describe()
        print(f"\n营业收入统计 (万元):")
        print(f"  最小值: {revenue_stats['min']:.2f}")
        print(f"  最大值: {revenue_stats['max']:.2f}")
        print(f"  平均值: {revenue_stats['mean']:.2f}")
        print(f"  中位数: {revenue_stats['50%']:.2f}")
    
    if 'net_profit' in all_data.columns:
        profit_stats = all_data['net_profit'].describe()
        print(f"\n净利润统计 (万元):")
        print(f"  最小值: {profit_stats['min']:.2f}")
        print(f"  最大值: {profit_stats['max']:.2f}")
        print(f"  平均值: {profit_stats['mean']:.2f}")
        print(f"  中位数: {profit_stats['50%']:.2f}")
    
    if 'eps' in all_data.columns:
        eps_stats = all_data['eps'].describe()
        print(f"\n每股收益统计 (元):")
        print(f"  最小值: {eps_stats['min']:.2f}")
        print(f"  最大值: {eps_stats['max']:.2f}")
        print(f"  平均值: {eps_stats['mean']:.2f}")
        print(f"  中位数: {eps_stats['50%']:.2f}")
    
    # 3. 检查报告日期分布
    if 'report_date' in all_data.columns:
        date_counts = all_data['report_date'].value_counts()
        print(f"\n报告日期分布 (前10个):")
        for date, count in date_counts.head(10).items():
            print(f"  {date}: {count} 条记录")
    
    # 4. 检查公司分布
    if 'company_name' in all_data.columns:
        company_counts = all_data['company_name'].value_counts()
        print(f"\n公司分布 (前10个):")
        for company, count in company_counts.head(10).items():
            print(f"  {company}: {count} 条记录")
    
    # 关闭数据库连接
    db_manager.close()

def main():
    """主测试函数"""
    print("开始PDF处理功能综合测试")
    print("测试时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    
    try:
        # 测试1: PDF内容提取
        extraction_results = test_pdf_extraction()
        
        # 测试2: 数据库存储
        if extraction_results:
            test_database_storage(extraction_results)
        
        # 测试3: 重复数据处理
        test_duplicate_handling()
        
        # 测试4: 数据质量验证
        test_data_quality()
        
        print("\n" + "=" * 60)
        print("所有测试完成!")
        print("=" * 60)
        
    except Exception as e:
        logger.error(f"测试过程中发生错误: {str(e)}")
        print(f"测试失败: {str(e)}")

if __name__ == "__main__":
    main()