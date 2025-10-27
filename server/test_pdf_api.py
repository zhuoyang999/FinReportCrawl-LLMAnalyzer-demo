#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import requests
import json

def test_pdf_parsing():
    """测试PDF解析API"""
    
    # 正确的文件路径
    file_path = "e:/learn/大四作业/同花顺/前端页面/java-backend/uploads/000001_annual_2020_20251027_155306.pdf"
    
    # 准备请求数据
    data = {
        "file_path": file_path
    }
    
    print(f"测试文件路径: {file_path}")
    print(f"请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
    
    try:
        # 发送POST请求
        response = requests.post(
            "http://localhost:8000/parse-pdf",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ PDF解析成功!")
            print(f"公司名称: {result['data']['company_name']}")
            print(f"股票代码: {result['data']['stock_code']}")
            print(f"报告日期: {result['data']['report_date']}")
            print(f"文本长度: {result['data']['text_length']}")
        else:
            print(f"❌ PDF解析失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 请求失败: {str(e)}")

if __name__ == "__main__":
    test_pdf_parsing()