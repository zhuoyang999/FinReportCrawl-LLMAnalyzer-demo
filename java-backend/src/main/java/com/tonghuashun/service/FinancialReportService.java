package com.tonghuashun.service;

import com.tonghuashun.dto.FinancialReportDTO;
import com.tonghuashun.dto.CrawlRequestDTO;
import com.tonghuashun.dto.QueryRequestDTO;
import com.tonghuashun.common.PageResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * 财务报告业务服务类
 * 提供财务报告相关的业务逻辑处理
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class FinancialReportService {
    
    private final PythonServiceClient pythonServiceClient;
    
    /**
     * 爬取财务报告
     * 该方法会调用Python服务进行PDF爬取，并自动触发后续的PDF处理流程
     * 
     * @param request 爬取请求参数
     * @return 爬取结果，包含成功状态和相关信息
     */
    public Map<String, Object> crawlFinancialReport(CrawlRequestDTO request) {
        log.info("开始爬取财务报告，股票代码: {}, 年份: {}, 报告类型: {}", 
                request.getStockCode(), request.getYear(), request.getReportType());
        
        try {
            // 验证请求参数
            validateCrawlRequest(request);
            
            // 调用Python服务进行爬取
            // Python服务会在爬取成功后自动触发PDF处理和数据库存储
            Map<String, Object> crawlResult = pythonServiceClient.crawlReport(request);
            
            // 构建响应结果
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "财务报告爬取成功，正在后台处理PDF文件");
            result.put("stockCode", request.getStockCode());
            result.put("year", request.getYear());
            result.put("reportType", request.getReportType());
            result.put("crawlDetails", crawlResult);
            
            log.info("财务报告爬取成功，股票代码: {}, 年份: {}, 报告类型: {}", 
                    request.getStockCode(), request.getYear(), request.getReportType());
            
            return result;
            
        } catch (Exception e) {
            log.error("财务报告爬取失败，股票代码: {}, 年份: {}, 报告类型: {}, 错误: {}", 
                    request.getStockCode(), request.getYear(), request.getReportType(), e.getMessage());
            
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("message", "财务报告爬取失败: " + e.getMessage());
            errorResult.put("stockCode", request.getStockCode());
            errorResult.put("year", request.getYear());
            errorResult.put("reportType", request.getReportType());
            
            return errorResult;
        }
    }
    
    /**
     * 手动触发PDF处理
     * 用于重新处理已下载的PDF文件
     * 
     * @param stockCode 股票代码
     * @param year 年份
     * @param reportType 报告类型
     * @return 处理结果
     */
    public Map<String, Object> processPdfs(String stockCode, Integer year, String reportType) {
        log.info("开始手动处理PDF文件，股票代码: {}, 年份: {}, 报告类型: {}", 
                stockCode, year, reportType);
        
        try {
            // 调用Python服务进行PDF处理
            Map<String, Object> processResult = pythonServiceClient.processPdfs(stockCode, year, reportType);
            
            // 构建响应结果
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "PDF处理任务已启动");
            result.put("stockCode", stockCode);
            result.put("year", year);
            result.put("reportType", reportType);
            result.put("processDetails", processResult);
            
            log.info("PDF处理任务启动成功，股票代码: {}, 年份: {}, 报告类型: {}", 
                    stockCode, year, reportType);
            
            return result;
            
        } catch (Exception e) {
            log.error("PDF处理任务启动失败，股票代码: {}, 年份: {}, 报告类型: {}, 错误: {}", 
                    stockCode, year, reportType, e.getMessage());
            
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("message", "PDF处理任务启动失败: " + e.getMessage());
            errorResult.put("stockCode", stockCode);
            errorResult.put("year", year);
            errorResult.put("reportType", reportType);
            
            return errorResult;
        }
    }
    
    /**
     * 查询财务报告
     * 支持多种查询条件和分页
     * 
     * @param request 查询请求参数
     * @return 分页查询结果
     */
    public PageResponse<FinancialReportDTO> queryFinancialReports(QueryRequestDTO request) {
        log.info("开始查询财务报告，股票代码: {}, 公司名称: {}, 页码: {}, 每页大小: {}", 
                request.getStockCode(), request.getCompanyName(), request.getPage(), request.getSize());
        
        try {
            // 验证查询参数
            validateQueryRequest(request);
            
            // 调用Python服务进行查询
            PageResponse<FinancialReportDTO> result = pythonServiceClient.queryReports(request);
            
            log.info("财务报告查询成功，返回 {} 条记录，总计 {} 条", 
                    result.getItems().size(), result.getTotal());
            
            return result;
            
        } catch (Exception e) {
            log.error("财务报告查询失败，错误: {}", e.getMessage());
            throw new RuntimeException("财务报告查询失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取系统统计信息
     * 包括报告总数、热门股票等统计数据
     * 
     * @return 统计信息
     */
    public Map<String, Object> getSystemStats() {
        log.info("开始获取系统统计信息");
        
        try {
            Map<String, Object> stats = pythonServiceClient.getStats();
            
            // 可以在这里添加额外的业务逻辑，比如数据转换、缓存等
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("data", stats);
            result.put("timestamp", System.currentTimeMillis());
            
            log.info("系统统计信息获取成功");
            return result;
            
        } catch (Exception e) {
            log.error("系统统计信息获取失败，错误: {}", e.getMessage());
            
            Map<String, Object> errorResult = new HashMap<>();
            errorResult.put("success", false);
            errorResult.put("message", "统计信息获取失败: " + e.getMessage());
            errorResult.put("timestamp", System.currentTimeMillis());
            
            return errorResult;
        }
    }
    
    /**
     * 获取系统健康状态
     * 检查各个组件的运行状态
     * 
     * @return 健康状态信息
     */
    public Map<String, Object> getSystemHealth() {
        log.debug("开始检查系统健康状态");
        
        try {
            Map<String, Object> pythonHealth = pythonServiceClient.getHealthStatus();
            
            Map<String, Object> result = new HashMap<>();
            result.put("status", "UP");
            result.put("components", Map.of(
                    "java-backend", Map.of("status", "UP"),
                    "python-service", pythonHealth
            ));
            result.put("timestamp", System.currentTimeMillis());
            
            log.debug("系统健康状态检查完成");
            return result;
            
        } catch (Exception e) {
            log.warn("系统健康状态检查异常，错误: {}", e.getMessage());
            
            Map<String, Object> result = new HashMap<>();
            result.put("status", "DOWN");
            result.put("error", e.getMessage());
            result.put("timestamp", System.currentTimeMillis());
            
            return result;
        }
    }
    
    /**
     * 验证爬取请求参数
     * 
     * @param request 爬取请求
     */
    private void validateCrawlRequest(CrawlRequestDTO request) {
        if (request.getStockCode() == null || request.getStockCode().trim().isEmpty()) {
            throw new IllegalArgumentException("股票代码不能为空");
        }
        
        if (request.getYear() == null || request.getYear() < 2000 || request.getYear() > 2030) {
            throw new IllegalArgumentException("年份必须在2000-2030之间");
        }
        
        if (request.getReportType() == null || request.getReportType().trim().isEmpty()) {
            throw new IllegalArgumentException("报告类型不能为空");
        }
        
        // 验证报告类型是否有效
        String reportType = request.getReportType().toLowerCase();
        if (!reportType.equals("annual") && !reportType.equals("interim") && !reportType.equals("quarterly")) {
            throw new IllegalArgumentException("报告类型必须是 annual、interim 或 quarterly");
        }
    }
    
    /**
     * 验证查询请求参数
     * 
     * @param request 查询请求
     */
    private void validateQueryRequest(QueryRequestDTO request) {
        if (request.getPage() == null || request.getPage() < 1) {
            request.setPage(1);
        }
        
        if (request.getSize() == null || request.getSize() < 1) {
            request.setSize(10);
        } else if (request.getSize() > 100) {
            request.setSize(100);
        }
        
        // 验证年份范围
        if (request.getStartYear() != null && request.getEndYear() != null) {
            if (request.getStartYear() > request.getEndYear()) {
                throw new IllegalArgumentException("开始年份不能大于结束年份");
            }
        }
    }
}