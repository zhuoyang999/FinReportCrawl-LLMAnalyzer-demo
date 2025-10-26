#!/usr/bin/env python3
"""
数据库清理脚本
"""

from data_processor.database_manager import DatabaseManager
from sqlalchemy import text

def main():
    print('=== 清理数据库中的错误数据 ===')
    db_manager = DatabaseManager()

    # 查询所有数据
    all_data = db_manager.query_data()
    print(f'清理前：数据库中有 {len(all_data)} 条记录')

    # 显示所有记录
    print('所有记录:')
    for idx, row in all_data.iterrows():
        print(f'  {row["id"]}. {row["company_name"]} ({row["stock_code"]}) - {row["report_date"]}')

    # 删除错误数据
    try:
        with db_manager.engine.connect() as conn:
            # 删除公司名称包含错误信息的记录
            result1 = conn.execute(text("DELETE FROM financial_reports WHERE company_name LIKE '%主要业务%'"))
            # 删除股票代码为空的记录
            result2 = conn.execute(text("DELETE FROM financial_reports WHERE stock_code = '' OR stock_code IS NULL"))
            conn.commit()
            
        print('✅ 清理完成')
        
        # 查询清理后的数据
        clean_data = db_manager.query_data()
        print(f'清理后：数据库中有 {len(clean_data)} 条记录')
        
        if len(clean_data) > 0:
            print('清理后的记录:')
            for idx, row in clean_data.iterrows():
                revenue_str = f'{row["revenue"]:,.0f}' if row['revenue'] else '未知'
                profit_str = f'{row["net_profit"]:,.0f}' if row['net_profit'] else '未知'
                print(f'  {row["id"]}. {row["company_name"]} ({row["stock_code"]}) - 收入:{revenue_str}元, 利润:{profit_str}元')
        
    except Exception as e:
        print(f'❌ 清理失败: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()