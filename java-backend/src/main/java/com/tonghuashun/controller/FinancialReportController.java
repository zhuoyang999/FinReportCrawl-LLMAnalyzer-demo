package com.tonghuashun.controller;

import com.tonghuashun.dto.FinancialReportDTO;
import com.tonghuashun.dto.CrawlRequestDTO;
import com.tonghuashun.dto.QueryRequestDTO;
import com.tonghuashun.common.ApiResponse;
import com.tonghuashun.common.PageResponse;
import com.tonghuashun.service.FinancialReportService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.Map;

/**
 * 财务报告控制器
 * 提供财务报告相关的RESTful API接口
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/financial-reports")
@RequiredArgsConstructor
@Validated
@Tag(name = "财务报告管理", description = "财务报告爬取、处理和查询相关接口")
public class FinancialReportController {
    
    private final FinancialReportService financialReportService;
    
    /**
     * 爬取财务报告
     * 该接口会触发PDF爬取，并自动进行后续的PDF处理和数据库存储
     * 
     * @param request 爬取请求参数
     * @return 爬取结果
     */
    @PostMapping("/crawl")
    @Operation(summary = "爬取财务报告", description = "根据股票代码、年份和报告类型爬取财务报告PDF，并自动处理存储到数据库")
    public ApiResponse<Map<String, Object>> crawlReport(
            @Valid @RequestBody CrawlRequestDTO request) {
        
        log.info("收到爬取请求，股票代码: {}, 年份: {}, 报告类型: {}", 
                request.getStockCode(), request.getYear(), request.getReportType());
        
        try {
            Map<String, Object> result = financialReportService.crawlFinancialReport(request);
            
            if ((Boolean) result.get("success")) {
                return ApiResponse.success("财务报告爬取成功", result);
            } else {
                return ApiResponse.badRequest((String) result.get("message"));
            }
            
        } catch (IllegalArgumentException e) {
            log.warn("爬取请求参数无效: {}", e.getMessage());
            return ApiResponse.badRequest("请求参数无效: " + e.getMessage());
        } catch (Exception e) {
            log.error("爬取财务报告时发生异常", e);
            return ApiResponse.serverError("爬取财务报告失败: " + e.getMessage());
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
    @PostMapping("/process")
    @Operation(summary = "手动处理PDF", description = "手动触发指定股票和年份的PDF文件处理")
    public ApiResponse<Map<String, Object>> processPdfs(
            @Parameter(description = "股票代码", required = true)
            @RequestParam @NotBlank(message = "股票代码不能为空") String stockCode,
            
            @Parameter(description = "年份", required = true)
            @RequestParam @NotNull(message = "年份不能为空") Integer year,
            
            @Parameter(description = "报告类型", required = true)
            @RequestParam @NotBlank(message = "报告类型不能为空") String reportType) {
        
        log.info("收到PDF处理请求，股票代码: {}, 年份: {}, 报告类型: {}", 
                stockCode, year, reportType);
        
        try {
            Map<String, Object> result = financialReportService.processPdfs(stockCode, year, reportType);
            
            if ((Boolean) result.get("success")) {
                return ApiResponse.success("PDF处理任务启动成功", result);
            } else {
                return ApiResponse.badRequest((String) result.get("message"));
            }
            
        } catch (IllegalArgumentException e) {
            log.warn("PDF处理请求参数无效: {}", e.getMessage());
            return ApiResponse.badRequest("请求参数无效: " + e.getMessage());
        } catch (Exception e) {
            log.error("启动PDF处理任务时发生异常", e);
            return ApiResponse.serverError("PDF处理任务启动失败: " + e.getMessage());
        }
    }
    
    /**
     * 查询财务报告
     * 支持多种查询条件和分页
     * 
     * @param request 查询请求参数
     * @return 分页查询结果
     */
    @GetMapping("/query")
    @Operation(summary = "查询财务报告", description = "根据多种条件查询财务报告，支持分页")
    public ApiResponse<PageResponse<FinancialReportDTO>> queryReports(
            @Valid @ModelAttribute QueryRequestDTO request) {
        
        log.info("收到查询请求，股票代码: {}, 公司名称: {}, 页码: {}, 每页大小: {}", 
                request.getStockCode(), request.getCompanyName(), request.getPage(), request.getSize());
        
        try {
            PageResponse<FinancialReportDTO> result = financialReportService.queryFinancialReports(request);
            return ApiResponse.success("查询成功", result);
            
        } catch (IllegalArgumentException e) {
            log.warn("查询请求参数无效: {}", e.getMessage());
            return ApiResponse.badRequest("请求参数无效: " + e.getMessage());
        } catch (Exception e) {
            log.error("查询财务报告时发生异常", e);
            return ApiResponse.serverError("查询财务报告失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取指定股票的财务报告列表
     * 简化版查询接口，只需要股票代码
     * 
     * @param stockCode 股票代码
     * @param page 页码（可选，默认1）
     * @param size 每页大小（可选，默认10）
     * @return 财务报告列表
     */
    @GetMapping("/stock/{stockCode}")
    @Operation(summary = "获取指定股票的财务报告", description = "根据股票代码获取该股票的所有财务报告")
    public ApiResponse<PageResponse<FinancialReportDTO>> getReportsByStock(
            @Parameter(description = "股票代码", required = true)
            @PathVariable @NotBlank(message = "股票代码不能为空") String stockCode,
            
            @Parameter(description = "页码", required = false)
            @RequestParam(defaultValue = "1") Integer page,
            
            @Parameter(description = "每页大小", required = false)
            @RequestParam(defaultValue = "10") Integer size) {
        
        log.info("收到股票报告查询请求，股票代码: {}, 页码: {}, 每页大小: {}", stockCode, page, size);
        
        try {
            QueryRequestDTO request = new QueryRequestDTO();
            request.setStockCode(stockCode);
            request.setPage(page);
            request.setSize(size);
            
            PageResponse<FinancialReportDTO> result = financialReportService.queryFinancialReports(request);
            return ApiResponse.success("查询成功", result);
            
        } catch (Exception e) {
            log.error("查询股票财务报告时发生异常", e);
            return ApiResponse.serverError("查询股票财务报告失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取系统统计信息
     * 包括报告总数、热门股票等统计数据
     * 
     * @return 统计信息
     */
    @GetMapping("/stats")
    @Operation(summary = "获取系统统计信息", description = "获取财务报告系统的统计信息，如报告总数、热门股票等")
    public ApiResponse<Map<String, Object>> getStats() {
        log.info("收到统计信息查询请求");
        
        try {
            Map<String, Object> result = financialReportService.getSystemStats();
            
            if ((Boolean) result.get("success")) {
                return ApiResponse.success("统计信息获取成功", (Map<String, Object>) result.get("data"));
            } else {
                return ApiResponse.serverError((String) result.get("message"));
            }
            
        } catch (Exception e) {
            log.error("获取统计信息时发生异常", e);
            return ApiResponse.serverError("获取统计信息失败: " + e.getMessage());
        }
    }
    
    /**
     * 健康检查接口
     * 检查系统各组件的运行状态
     * 
     * @return 健康状态信息
     */
    @GetMapping("/health")
    @Operation(summary = "健康检查", description = "检查财务报告系统各组件的运行状态")
    public ApiResponse<Map<String, Object>> healthCheck() {
        log.debug("收到健康检查请求");
        
        try {
            Map<String, Object> result = financialReportService.getSystemHealth();
            
            String status = (String) result.get("status");
            if ("UP".equals(status)) {
                return ApiResponse.success("系统运行正常", result);
            } else {
                return ApiResponse.serverError("系统运行异常");
            }
            
        } catch (Exception e) {
            log.error("健康检查时发生异常", e);
            return ApiResponse.serverError("健康检查失败: " + e.getMessage());
        }
    }
}