from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Literal, List, Dict, Any
import os
import logging
import pandas as pd
from datetime import datetime
import shutil

from crawler.financial_report_crawler import FinancialReportCrawler
from data_processor.pdf_parser import FinancialReportParser
from data_processor.database_manager import DatabaseManager
from data_processor.knowledge_base_manager import KnowledgeBaseManager

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

# 全局任务状态管理器
import uuid
from threading import Lock

class TaskManager:
    def __init__(self):
        self.tasks = {}
        self.lock = Lock()
    
    def create_task(self, task_type: str, params: dict) -> str:
        task_id = str(uuid.uuid4())
        with self.lock:
            self.tasks[task_id] = {
                "id": task_id,
                "type": task_type,
                "status": "pending",
                "progress": 0,
                "message": "任务已创建",
                "params": params,
                "result": None,
                "error": None,
                "created_at": datetime.now()
            }
        return task_id
    
    def update_task(self, task_id: str, status: str = None, progress: int = None, 
                   message: str = None, result: dict = None, error: str = None):
        with self.lock:
            if task_id in self.tasks:
                if status is not None:
                    self.tasks[task_id]["status"] = status
                if progress is not None:
                    self.tasks[task_id]["progress"] = progress
                if message is not None:
                    self.tasks[task_id]["message"] = message
                if result is not None:
                    self.tasks[task_id]["result"] = result
                if error is not None:
                    self.tasks[task_id]["error"] = error
    
    def get_task(self, task_id: str) -> dict:
        with self.lock:
            return self.tasks.get(task_id, None)

task_manager = TaskManager()

# ==================== 根路径路由 ====================

@app.get("/")
async def root():
    """根路径，返回API基本信息"""
    return {
        "message": "Financial Report Crawler & Processor API",
        "version": "0.2.0",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "stats": "/api/stats",
            "crawl": "/api/crawl",
            "process": "/api/process-pdfs",
            "reports": "/api/financial-reports",
            "smart_upload": "/api/smart/upload",
            "smart_analyze": "/api/smart/analyze",
            "smart_chat": "/api/smart/chat"
        }
    }

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

class AnalyzeRequest(BaseModel):
    file_path: str = Field(..., description="需要分析的文件的路径")

class ChatRequest(BaseModel):
    report_id: str = Field(..., description="报告的唯一ID")
    query: str = Field(..., description="用户提出的问题")

class AnalyzePdfRequest(BaseModel):
    stock_code: str = Field(..., description="股票代码")
    year: int = Field(..., description="报告年份")
    report_type: str = Field(..., description="报告类型")

class AnalyzePdfByPathRequest(BaseModel):
    file_path: str = Field(..., description="PDF文件路径")
    stock_code: str = Field(..., description="股票代码")
    company_name: str = Field(..., description="公司名称")
    year: str = Field(..., description="报告年份")
    report_type: str = Field(..., description="报告类型")

class AnalyzePdfResponse(BaseModel):
    task_id: str = Field(..., description="任务ID")
    status: str = Field(..., description="任务状态")
    message: str = Field(..., description="状态消息")

class AnalysisResultResponse(BaseModel):
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: int  # 0-100
    message: str
    text_results: Optional[List[Dict[str, Any]]] = None  # 按页分组的文本结果
    table_results: Optional[List[Dict[str, Any]]] = None  # 表格结果
    error: Optional[str] = None

# ==================== 核心业务逻辑 ====================

def generate_summary_from_text(text: str) -> Dict[str, Any]:
    """
    (模拟) 使用AI模型从文本生成摘要和关键见解。
    在真实场景中，这里会调用一个复杂的LLM来完成。
    """
    # 模拟耗时
    import time
    time.sleep(2)

    # 模拟提取关键信息
    summary = "该公司报告期内营业收入实现稳健增长，但净利润受成本上升影响略有下滑。未来需关注其成本控制能力和新业务拓展情况。"
    highlights = [
        "营业收入同比增长15%，达到100亿元。",
        "研发投入增加20%，主要用于AI技术研究。",
        "市场竞争加剧，导致销售费用率上升2个百分点。",
        "公司计划在下半年推出两款新产品，有望成为新的增长点。"
    ]
    risks = [
        "原材料价格波动风险。",
        "核心技术人员流失风险。",
        "国际贸易摩擦带来的不确定性。"
    ]

    return {
        "summary": summary,
        "highlights": highlights,
        "risks": risks
    }


def generate_answer_from_context(context: str, query: str) -> str:
    """
    (模拟) 根据上下文和问题生成答案。
    """
    # 模拟AI思考
    import time
    time.sleep(1)
    
    if "收入" in query:
        return f"根据文档内容，关于您提到的'{query}'，报告指出营业收入实现了稳健增长。具体细节请参考报告原文。上下文摘要：{context[:100]}..."
    elif "利润" in query:
        return f"关于'{query}'，报告提到净利润受成本上升影响略有下滑。建议您关注成本控制部分。上下文摘要：{context[:100]}..."
    else:
        return f"已收到您的问题'{query}'。这是一个模拟回复。在实际应用中，我会基于文档'{context[:100]}...'来提供更详细的解答。"


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
                    df = pd.DataFrame([parsed_data])
                    db_manager.insert_dataframe(df)
                    # 新增：写入扩展结构
                    try:
                        # 公司信息 upsert
                        company_name = parsed_data.get('company_name') or ''
                        code = parsed_data.get('stock_code') or ''
                        db_manager.upsert_company(stock_code=code, company_name=company_name)
                        # 推断年份与报告类型
                        report_date = parsed_data.get('report_date') or ''
                        year = None
                        try:
                            if report_date and len(report_date) >= 4:
                                year = int(report_date[:4])
                        except Exception:
                            year = None
                        if not year:
                            parts = os.path.normpath(pdf_file).split(os.sep)
                            # 目录规范：.../<code>/<year>/<type>/xxx.pdf
                            for p in parts:
                                if p.isdigit() and len(p) == 4:
                                    try:
                                        year = int(p)
                                        break
                                    except Exception:
                                        pass
                        report_type = 'annual'
                        # 从路径推断类型
                        if 'semi' in pdf_file.lower() or '半年' in pdf_file:
                            report_type = 'semi_annual'
                        elif any(x in pdf_file.lower() for x in ['q1','一季','季度1']):
                            report_type = 'quarterly'
                        elif any(x in pdf_file.lower() for x in ['q2','二季','季度2']):
                            report_type = 'quarterly'
                        elif any(x in pdf_file.lower() for x in ['q3','三季','季度3']):
                            report_type = 'quarterly'
                        elif any(x in pdf_file.lower() for x in ['q4','四季','季度4']):
                            report_type = 'quarterly'
                        # 文件元数据
                        file_size = None
                        try:
                            if os.path.exists(pdf_file):
                                file_size = os.path.getsize(pdf_file)
                        except Exception:
                            pass
                        report = db_manager.upsert_financial_report(
                            stock_code=code,
                            report_year=year or 0,
                            report_type=report_type,
                            company_name=company_name,
                            local_path=pdf_file,
                            file_size=file_size,
                            crawl_status='success',
                            crawled_at=datetime.now()
                        )
                        # 文本内容
                        try:
                            full_text = parser.extract_text_from_pdf(pdf_file)
                        except Exception:
                            full_text = None
                        if report and full_text:
                            db_manager.add_report_content(
                                report_id=report.id,
                                content_type='overview',
                                extracted_text=full_text,
                                extraction_method='PyMuPDF'
                            )
                        # 指标
                        db_manager.add_financial_metric(
                            report_id=report.id,
                            metric_name='营业收入',
                            metric_value=parsed_data.get('revenue'),
                            metric_unit='万元',
                            period_type='FY'
                        )
                        db_manager.add_financial_metric(
                            report_id=report.id,
                            metric_name='净利润',
                            metric_value=parsed_data.get('net_profit'),
                            metric_unit='万元',
                            period_type='FY'
                        )
                        db_manager.add_financial_metric(
                            report_id=report.id,
                            metric_name='每股收益',
                            metric_value=parsed_data.get('eps'),
                            metric_unit='元/股',
                            period_type='FY'
                        )
                    except Exception as e2:
                        logger.warning(f"扩展写入失败，但不影响旧流程: {e2}")
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


def analyze_pdf_in_background(task_id: str, stock_code: str, year: int, report_type: str):
    """
    后台任务：分析指定的PDF文件
    """
    try:
        task_manager.update_task(task_id, status="processing", progress=10, message="正在查找PDF文件...")
        
        # 查找对应的PDF文件
        pdf_path = None
        data_dir = "data/reports"
        
        # 构建可能的路径，按优先级排序
        possible_paths = [
            f"{data_dir}/{stock_code}/{year}/{report_type}",  # 最具体的路径
            f"{data_dir}/{stock_code}/{year}",                # 年份目录
            f"{data_dir}/{stock_code}"                        # 股票代码目录
        ]
        
        for base_path in possible_paths:
            if os.path.exists(base_path):
                # 递归搜索所有子目录
                for root, dirs, files in os.walk(base_path):
                    for file in files:
                        if file.endswith('.pdf'):
                            # 检查文件名是否包含股票代码
                            if stock_code in file:
                                # 对于年份，检查文件名或者路径
                                year_str = str(year)
                                prev_year_str = str(year - 1)  # 年度报告可能在下一年发布
                                
                                # 检查年份匹配：当前年份或前一年（用于年度报告）
                                year_match = (year_str in file or year_str in root or 
                                            (report_type == "annual" and (prev_year_str in file or prev_year_str in root)))
                                
                                if year_match:
                                    pdf_path = os.path.join(root, file)
                                    break
                    if pdf_path:
                        break
            if pdf_path:
                break
        
        if not pdf_path:
            task_manager.update_task(task_id, status="failed", progress=0, 
                                   error=f"未找到股票代码 {stock_code} 年份 {year} 的PDF文件")
            return
        
        task_manager.update_task(task_id, progress=30, message=f"找到PDF文件: {os.path.basename(pdf_path)}")
        
        # 初始化PDF解析器
        parser = FinancialReportParser()
        
        # 提取文本内容（按页分组）
        task_manager.update_task(task_id, progress=50, message="正在提取PDF文本内容...")
        
        import fitz  # PyMuPDF
        doc = fitz.open(pdf_path)
        text_results = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # 高亮关键财务术语
            highlighted_text = highlight_financial_terms(text)
            
            text_results.append({
                "page": page_num + 1,
                "text": text,
                "highlighted_text": highlighted_text
            })
            
            # 更新进度
            progress = 50 + int((page_num + 1) / len(doc) * 30)
            task_manager.update_task(task_id, progress=progress, 
                                   message=f"正在处理第 {page_num + 1}/{len(doc)} 页...")
        
        doc.close()
        
        # 提取表格数据
        task_manager.update_task(task_id, progress=85, message="正在提取表格数据...")
        
        table_results = []
        try:
            # 使用现有的解析器提取结构化数据
            parsed_data = parser.parse_single_pdf(pdf_path)
            if parsed_data:
                # 构建表格结果
                financial_table = {
                    "title": "主要财务指标",
                    "headers": ["指标名称", "数值", "单位"],
                    "rows": [
                        ["营业收入", parsed_data.get('revenue', 'N/A'), "万元"],
                        ["净利润", parsed_data.get('net_profit', 'N/A'), "万元"],
                        ["每股收益", parsed_data.get('eps', 'N/A'), "元/股"],
                        ["总资产", parsed_data.get('total_assets', 'N/A'), "万元"],
                        ["净资产", parsed_data.get('net_assets', 'N/A'), "万元"]
                    ]
                }
                table_results.append(financial_table)
        except Exception as e:
            logger.warning(f"表格提取失败: {str(e)}")
        
        # 完成任务
        result = {
            "text_results": text_results,
            "table_results": table_results,
            "pdf_path": pdf_path,
            "total_pages": len(text_results)
        }
        
        task_manager.update_task(task_id, status="completed", progress=100, 
                               message="PDF分析完成", result=result)
        
        logger.info(f"PDF分析任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"PDF分析任务失败 {task_id}: {str(e)}")
        task_manager.update_task(task_id, status="failed", progress=0, 
                               error=f"分析失败: {str(e)}")


def analyze_pdf_by_path_in_background(task_id: str, file_path: str, stock_code: str, company_name: str, year: str, report_type: str):
    """
    后台任务：通过文件路径直接分析PDF文件
    """
    try:
        task_manager.update_task(task_id, status="processing", progress=10, message="正在验证PDF文件...")
        
        # 验证文件是否存在
        if not os.path.exists(file_path):
            task_manager.update_task(task_id, status="failed", progress=0, 
                                   error=f"PDF文件不存在: {file_path}")
            return
        
        task_manager.update_task(task_id, progress=30, message=f"开始分析PDF文件: {os.path.basename(file_path)}")
        
        # 初始化PDF解析器
        parser = FinancialReportParser()
        
        # 提取文本内容（按页分组）
        task_manager.update_task(task_id, progress=50, message="正在提取PDF文本内容...")
        
        import fitz  # PyMuPDF
        doc = fitz.open(file_path)
        text_results = []
        
        for page_num in range(len(doc)):
            page = doc.load_page(page_num)
            text = page.get_text()
            
            # 高亮关键财务术语
            highlighted_text = highlight_financial_terms(text)
            
            text_results.append({
                "page": page_num + 1,
                "text": text,
                "highlighted_text": highlighted_text
            })
            
            # 更新进度
            progress = 50 + int((page_num + 1) / len(doc) * 30)
            task_manager.update_task(task_id, progress=progress, 
                                   message=f"正在处理第 {page_num + 1}/{len(doc)} 页...")
        
        doc.close()
        
        # 提取表格数据
        task_manager.update_task(task_id, progress=85, message="正在提取表格数据...")
        
        table_results = []
        try:
            # 使用现有的解析器提取结构化数据
            parsed_data = parser.parse_single_pdf(file_path)
            if parsed_data:
                # 构建表格结果
                financial_table = {
                    "title": "主要财务指标",
                    "headers": ["指标名称", "数值", "单位"],
                    "rows": [
                        ["营业收入", parsed_data.get('revenue', 'N/A'), "万元"],
                        ["净利润", parsed_data.get('net_profit', 'N/A'), "万元"],
                        ["每股收益", parsed_data.get('eps', 'N/A'), "元/股"],
                        ["总资产", parsed_data.get('total_assets', 'N/A'), "万元"],
                        ["净资产", parsed_data.get('net_assets', 'N/A'), "万元"]
                    ]
                }
                table_results.append(financial_table)
        except Exception as e:
            logger.warning(f"表格提取失败: {str(e)}")
        
        # 完成任务
        result = {
            "text_results": text_results,
            "table_results": table_results,
            "pdf_path": file_path,
            "total_pages": len(text_results),
            "stock_code": stock_code,
            "company_name": company_name,
            "year": year,
            "report_type": report_type
        }
        
        task_manager.update_task(task_id, status="completed", progress=100, 
                               message="PDF分析完成", result=result)
        
        logger.info(f"PDF分析任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"PDF分析任务失败 {task_id}: {str(e)}")
        task_manager.update_task(task_id, status="failed", progress=0, 
                               error=f"分析失败: {str(e)}")


def highlight_financial_terms(text: str) -> str:
    """
    高亮财务关键词
    """
    financial_terms = [
        "归母净利润", "ROE", "ROA", "营业收入", "净利润", "总资产", "净资产", 
        "资产负债率", "流动比率", "速动比率", "每股收益", "每股净资产",
        "毛利率", "净利率", "资产周转率", "权益乘数", "现金流量", "经营活动现金流"
    ]
    
    highlighted = text
    for term in financial_terms:
        if term in highlighted:
            highlighted = highlighted.replace(term, f"<mark class='financial-term'>{term}</mark>")
    
    return highlighted

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

@app.post("/api/analyze-pdf", response_model=AnalyzePdfResponse)
async def analyze_pdf(req: AnalyzePdfRequest, background_tasks: BackgroundTasks):
    """
    分析指定的PDF文件
    """
    try:
        # 创建分析任务
        task_id = task_manager.create_task("pdf_analysis", {
            "stock_code": req.stock_code,
            "year": req.year,
            "report_type": req.report_type
        })
        
        # 启动后台分析任务
        background_tasks.add_task(
            analyze_pdf_in_background,
            task_id,
            req.stock_code,
            req.year,
            req.report_type
        )
        
        return AnalyzePdfResponse(
            task_id=task_id,
            status="pending",
            message="PDF分析任务已启动"
        )
        
    except Exception as e:
        logger.error(f"启动PDF分析任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动分析任务失败: {str(e)}")

@app.post("/api/analyze-pdf-by-path", response_model=AnalyzePdfResponse)
async def analyze_pdf_by_path(req: AnalyzePdfByPathRequest, background_tasks: BackgroundTasks):
    """
    通过文件路径直接分析PDF文件
    """
    try:
        # 创建分析任务
        task_id = task_manager.create_task("pdf_analysis_by_path", {
            "file_path": req.file_path,
            "stock_code": req.stock_code,
            "company_name": req.company_name,
            "year": req.year,
            "report_type": req.report_type
        })
        
        # 启动后台分析任务
        background_tasks.add_task(
            analyze_pdf_by_path_in_background,
            task_id,
            req.file_path,
            req.stock_code,
            req.company_name,
            req.year,
            req.report_type
        )
        
        return AnalyzePdfResponse(
            task_id=task_id,
            status="pending",
            message="PDF分析任务已启动"
        )
        
    except Exception as e:
        logger.error(f"启动PDF分析任务失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"启动分析任务失败: {str(e)}")

@app.get("/api/analyze-pdf/{task_id}", response_model=AnalysisResultResponse)
async def get_analysis_result(task_id: str):
    """
    获取PDF分析结果
    """
    try:
        task = task_manager.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="任务不存在")
        
        response = AnalysisResultResponse(
            task_id=task_id,
            status=task["status"],
            progress=task["progress"],
            message=task["message"],
            error=task.get("error")
        )
        
        # 如果任务完成，返回结果
        if task["status"] == "completed" and task.get("result"):
            result = task["result"]
            response.text_results = result.get("text_results")
            response.table_results = result.get("table_results")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取分析结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail=f"获取结果失败: {str(e)}")

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

@app.post("/api/smart/upload")
async def smart_upload(file: UploadFile = File(...)):
    upload_dir = "uploads"
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
    
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    return {"filename": file.filename, "path": file_path}

@app.post("/api/smart/analyze")
async def smart_analyze(req: AnalyzeRequest):
    """
    分析上传的PDF文件，提取文本，生成摘要，并为该文档创建独立的知识库。
    """
    file_path = req.file_path
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件不存在")

    try:
        # 1. 解析PDF提取基本信息和全文
        parser = FinancialReportParser()
        report_data = parser.parse_single_pdf(file_path)
        full_text = parser.extract_text_from_pdf(file_path)

        if not report_data or not full_text:
            raise HTTPException(status_code=500, detail="PDF解析失败，无法提取有效内容")

        # 2. (模拟) 调用AI生成摘要
        analysis_result = generate_summary_from_text(full_text)

        # 3. 为该文档创建知识库
        # 使用文件名和时间戳生成唯一的 report_id
        report_id = f"report_{os.path.basename(file_path)}_{int(datetime.now().timestamp())}"
        kb_manager = KnowledgeBaseManager(collection_name=report_id)
        kb_manager.add_pdf_to_collection(file_path)
        logger.info(f"成功为文档 '{file_path}' 创建知识库，ID: {report_id}")

        # 4. 整合最终结果
        final_result = {
            "report_id": report_id,
            "report_info": {
                "company_name": report_data.get("company_name", "未知公司"),
                "stock_code": report_data.get("stock_code", "未知代码"),
                "report_date": report_data.get("report_date", "未知日期"),
            },
            "analysis": analysis_result,
            "raw_text_preview": full_text[:2000] + "..." # 返回部分原文预览
        }

        return final_result

    except Exception as e:
        logger.error(f"智能分析失败: {file_path}, 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"智能分析过程中发生错误: {str(e)}")


@app.post("/api/smart/chat")
async def smart_chat(req: ChatRequest):
    """
    根据指定报告ID（知识库）和用户问题进行问答。
    """
    try:
        # 1. 初始化对应知识库的管理器
        kb_manager = KnowledgeBaseManager(collection_name=req.report_id)
        
        # 2. 在知识库中查询相关上下文
        # 注意：这里的 k 值可以调整，以获取更多或更少的上下文片段
        search_results = kb_manager.query_collection(req.query, k=3)
        
        if not search_results or not search_results['documents']:
            return {"answer": "抱歉，在当前报告中没有找到与您问题直接相关的信息。"}

        # 3. 整合上下文
        context = "\n".join(search_results['documents'][0])

        # 4. (模拟) 调用AI生成答案
        answer = generate_answer_from_context(context, req.query)
        
        return {"answer": answer}

    except Exception as e:
        logger.error(f"智能问答失败: report_id={req.report_id}, query='{req.query}', 错误: {str(e)}")
        # 在生产环境中，可能需要更详细的错误判断，例如判断集合是否存在
        if "does not exist" in str(e):
            raise HTTPException(status_code=404, detail=f"报告ID '{req.report_id}' 不存在或尚未处理完成。")
        raise HTTPException(status_code=500, detail=f"智能问答过程中发生错误: {str(e)}")


@app.get("/api/reports")
def list_reports_api(
    stock_code: Optional[str] = Query(None),
    report_year: Optional[int] = Query(None),
    report_type: Optional[str] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    """按股票代码/年份/类型分页查询财报元数据（新结构）。"""
    try:
        result = db_manager.list_reports(
            stock_code=stock_code,
            report_year=report_year,
            report_type=report_type,
            page=page,
            page_size=page_size,
        )
        return {"success": True, **result}
    except Exception as e:
        logger.error(f"列表查询失败: {e}")
        return {"success": False, "error": str(e)}

@app.get("/api/reports/{report_id}")
def get_report_details_api(report_id: int):
    """获取单个财报详情，包括文本内容与指标（新结构）。"""
    try:
        details = db_manager.get_report_details(report_id)
        if not details:
            return {"success": False, "error": "report not found"}
        return {"success": True, "data": details}
    except Exception as e:
        logger.error(f"详情查询失败: {e}")
        return {"success": False, "error": str(e)}


@app.get("/api/pdf-files")
def get_pdf_files():
    """获取已爬取的 PDF 文件列表"""
    try:
        pdf_files = []
        reports_dir = "data/reports"
        
        if not os.path.exists(reports_dir):
            return {"success": True, "data": []}
        
        # 遍历所有股票代码目录
        for stock_code in os.listdir(reports_dir):
            stock_path = os.path.join(reports_dir, stock_code)
            if not os.path.isdir(stock_path):
                continue
                
            # 遍历年份目录
            for year in os.listdir(stock_path):
                year_path = os.path.join(stock_path, year)
                if not os.path.isdir(year_path):
                    continue
                    
                # 遍历报告类型目录
                for report_type in os.listdir(year_path):
                    report_path = os.path.join(year_path, report_type)
                    if not os.path.isdir(report_path):
                        continue
                        
                    # 查找 PDF 文件
                    for file_name in os.listdir(report_path):
                        if file_name.endswith('.pdf'):
                            file_path = os.path.join(report_path, file_name)
                            file_size = os.path.getsize(file_path)
                            file_mtime = os.path.getmtime(file_path)
                            
                            # 解析文件名获取公司名称
                            parts = file_name.split('_')
                            company_name = parts[1] if len(parts) > 1 else "未知公司"
                            
                            pdf_files.append({
                                "id": f"{stock_code}_{year}_{report_type}_{file_name}",
                                "stock_code": stock_code,
                                "company_name": company_name,
                                "year": year,
                                "report_type": report_type,
                                "file_name": file_name,
                                "file_path": file_path,
                                "file_size": file_size,
                                "modified_time": datetime.fromtimestamp(file_mtime).isoformat(),
                                "relative_path": f"{stock_code}/{year}/{report_type}/{file_name}"
                            })
        
        # 按修改时间倒序排列
        pdf_files.sort(key=lambda x: x["modified_time"], reverse=True)
        
        return {"success": True, "data": pdf_files}
        
    except Exception as e:
        logger.error(f"获取 PDF 文件列表失败: {e}")
        return {"success": False, "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)