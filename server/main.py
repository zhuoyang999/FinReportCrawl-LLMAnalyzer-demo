from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
import os
import logging
import pandas as pd
from datetime import datetime

from crawler.financial_report_crawler import FinancialReportCrawler
from data_processor.pdf_parser import FinancialReportParser
from data_processor.database_manager import DatabaseManager

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Financial Report Crawler & Processor API", version="0.2.0")

# 开发阶段允许前端（Vite 默认 5173）跨域访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局数据库管理器实例
db_manager = DatabaseManager()

# ==================== 请求/响应模型 ====================

class CrawlRequest(BaseModel):
    code: str = Field(..., description="股票代码，如 000001 或 600519")
    year: int = Field(..., description="报告年份，如 2023")
    type: Literal["annual", "semi"] = Field(..., description="报告类型：annual 年报、semi 中报")
    orgid: Optional[str] = Field(None, description="可选：指定 orgId 以绕过索引")
    column: Optional[Literal["szse", "sse"]] = Field(None, description="可选：指定交易所列，默认按代码推断")
    out: Optional[str] = Field(None, description="可选：自定义下载根目录")

class ProcessRequest(BaseModel):
    directory_path: Optional[str] = Field(None, description="要处理的PDF目录路径，默认处理data/reports下的所有文件")
    stock_code: Optional[str] = Field(None, description="可选：仅处理指定股票代码的PDF")
    auto_process: bool = Field(True, description="是否在爬取成功后自动处理PDF")

class FinancialReportResponse(BaseModel):
    id: int
    company_name: str
    stock_code: str
    report_date: Optional[str]
    revenue: Optional[float]
    net_profit: Optional[float]
    earnings_per_share: Optional[float]
    crawl_time: str

class QueryRequest(BaseModel):
    stock_code: Optional[str] = Field(None, description="股票代码过滤")
    company_name: Optional[str] = Field(None, description="公司名称过滤")
    start_date: Optional[str] = Field(None, description="开始日期 YYYY-MM-DD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYY-MM-DD")
    page: int = Field(1, description="页码，从1开始")
    page_size: int = Field(20, description="每页数量，最大100")

# ==================== 核心业务逻辑 ====================

def process_pdfs_in_background(directory_path: str, stock_code: Optional[str] = None):
    """
    后台任务：处理PDF文件并存储到数据库
    """
    try:
        logger.info(f"开始处理PDF文件，目录: {directory_path}")
        parser = FinancialReportParser()
        
        # 获取所有PDF文件
        pdf_files = []
        if os.path.isfile(directory_path) and directory_path.endswith('.pdf'):
            pdf_files = [directory_path]
        else:
            for root, dirs, files in os.walk(directory_path):
                for file in files:
                    if file.endswith('.pdf'):
                        file_path = os.path.join(root, file)
                        # 如果指定了股票代码，只处理匹配的文件
                        if stock_code is None or stock_code in file:
                            pdf_files.append(file_path)
        
        logger.info(f"找到 {len(pdf_files)} 个PDF文件待处理")
        
        # 处理每个PDF文件
        processed_count = 0
        for pdf_file in pdf_files:
            try:
                logger.info(f"正在处理: {pdf_file}")
                parsed_data = parser.parse_single_pdf(pdf_file)
                
                if parsed_data:
                    df = pd.DataFrame([parsed_data]) # 将字典转换为DataFrame
                    # 存储到数据库
                    db_manager.insert_dataframe(df)
                    processed_count += 1
                    logger.info(f"成功处理并存储: {pdf_file}")
                else:
                    logger.warning(f"PDF解析结果为空: {pdf_file}")
                    
            except Exception as e:
                logger.error(f"处理PDF文件失败 {pdf_file}: {str(e)}")
                continue
        
        logger.info(f"PDF处理完成，成功处理 {processed_count}/{len(pdf_files)} 个文件")
        
    except Exception as e:
        logger.error(f"后台PDF处理任务失败: {str(e)}")

# ==================== API 接口 ====================

@app.post("/api/crawl")
async def crawl_financial_report(req: CrawlRequest, background_tasks: BackgroundTasks):
    """
    爬取财务报告PDF文件
    """
    try:
        crawler = FinancialReportCrawler(download_root=req.out)
        result = await crawler.crawl_report(
            stock_code=req.code,
            year=req.year,
            report_type=req.type,
            org_id=req.orgid,
            column=req.column,
        )
        
        # 如果爬取成功且有文件下载，自动触发PDF处理
        if result.get("downloaded", 0) > 0:
            save_dir = result.get("save_dir")
            if save_dir and os.path.exists(save_dir):
                logger.info(f"爬取成功，将自动处理PDF文件: {save_dir}")
                # 添加后台任务处理PDF
                background_tasks.add_task(
                    process_pdfs_in_background, 
                    save_dir, 
                    req.code
                )
                result["auto_processing"] = True
                result["message"] = "PDF文件正在后台处理中，稍后可查询数据库获取解析结果"
        
        return result
        
    except Exception as e:
        logger.error(f"爬取失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"爬取失败: {str(e)}")

@app.post("/api/process-pdfs")
async def process_pdfs(req: ProcessRequest, background_tasks: BackgroundTasks):
    """
    手动触发PDF处理任务
    """
    try:
        # 确定处理目录
        if req.directory_path:
            process_dir = req.directory_path
        else:
            process_dir = "data/reports"
        
        if not os.path.exists(process_dir):
            raise HTTPException(status_code=404, detail=f"目录不存在: {process_dir}")
        
        # 添加后台任务
        background_tasks.add_task(
            process_pdfs_in_background, 
            process_dir, 
            req.stock_code
        )
        
        return {
            "message": "PDF处理任务已启动",
            "directory": process_dir,
            "stock_code": req.stock_code,
            "status": "processing"
        }
        
    except Exception as e:
        logger.error(f"启动PDF处理任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动处理任务失败: {str(e)}")

@app.get("/api/financial-reports", response_model=Dict[str, Any])
async def get_financial_reports(
    stock_code: Optional[str] = None,
    company_name: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """
    查询财务报告数据
    """
    try:
        # 验证分页参数
        if page < 1:
            page = 1
        if page_size < 1 or page_size > 100:
            page_size = 20
        
        # 构建查询条件
        conditions = []
        params = []
        
        if stock_code:
            conditions.append("stock_code = %s")
            params.append(stock_code)
        
        if company_name:
            conditions.append("company_name LIKE %s")
            params.append(f"%{company_name}%")
        
        if start_date:
            conditions.append("report_date >= %s")
            params.append(start_date)
        
        if end_date:
            conditions.append("report_date <= %s")
            params.append(end_date)
        
        # 构建WHERE子句
        where_clause = ""
        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)
        
        # 使用 DatabaseManager 的 query_data 方法
        df = db_manager.query_data(
            stock_code=stock_code,
            company_name=company_name,
            start_date=start_date,
            end_date=end_date,
            limit=page_size * 10  # 获取更多数据用于分页
        )
        
        # 计算分页
        total_count = len(df)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_df = df.iloc[start_idx:end_idx]
        
        # 格式化结果
        reports = []
        for _, row in page_df.iterrows():
            reports.append({
                "id": int(row.get('id', 0)),
                "company_name": str(row.get('company_name', '')),
                "stock_code": str(row.get('stock_code', '')),
                "report_date": str(row.get('report_date', '')),
                "revenue": float(row.get('revenue', 0)) if pd.notna(row.get('revenue')) else None,
                "net_profit": float(row.get('net_profit', 0)) if pd.notna(row.get('net_profit')) else None,
                "earnings_per_share": float(row.get('eps', 0)) if pd.notna(row.get('eps')) else None,
                "crawl_time": str(row.get('crawl_time', ''))
            })
        
        return {
            "data": reports,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total_count,
                "total_pages": (total_count + page_size - 1) // page_size
            }
        }
        
    except Exception as e:
        logger.error(f"查询财务报告数据失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"查询数据失败: {str(e)}")

@app.get("/api/health")
async def health_check():
    """
    健康检查接口
    """
    try:
        # 检查数据库连接
        stats = db_manager.get_statistics()
        return {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "database": "connected",
            "stats": stats
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "database": "disconnected",
            "error": str(e)
        }

@app.get("/api/stats")
async def get_statistics():
    """
    获取数据统计信息
    """
    try:
        # 使用 DatabaseManager 的统计方法
        stats = db_manager.get_statistics()
        
        # 获取最近的报告数据
        recent_df = db_manager.query_data(limit=5)
        recent_reports = []
        
        for _, row in recent_df.iterrows():
            recent_reports.append({
                "company_name": str(row.get('company_name', '')),
                "stock_code": str(row.get('stock_code', '')),
                "report_date": str(row.get('report_date', '')),
                "crawl_time": str(row.get('crawl_time', ''))
            })
        
        return {
            "total_reports": stats.get('total_records', 0),
            "total_companies": stats.get('total_companies', 0),
            "latest_report_date": stats.get('latest_report_date', ''),
            "earliest_report_date": stats.get('earliest_report_date', ''),
            "recent_reports": recent_reports
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")