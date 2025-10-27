package com.tonghuashun.controller;

import com.tonghuashun.common.ApiResponse;
import com.tonghuashun.dto.SmartAnalysisRequestDTO;
import com.tonghuashun.dto.SmartAnalysisResultDTO;
import com.tonghuashun.service.SmartAnalysisService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import java.util.Map;

/**
 * 智能分析控制器
 * 提供PDF上传、智能分析和实时聊天相关的RESTful API接口
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Slf4j
@RestController
@RequestMapping("/smart")
@RequiredArgsConstructor
@Validated
@Tag(name = "智能分析", description = "智能财务报告分析相关接口")
public class SmartAnalysisController {
    
    private final SmartAnalysisService smartAnalysisService;
    
    /**
     * 上传PDF文件
     * 
     * @param file PDF文件
     * @param stockCode 股票代码
     * @param year 年份
     * @param reportType 报告类型
     * @return 上传结果
     */
    @PostMapping("/upload")
    @Operation(summary = "上传PDF文件", description = "上传财务报告PDF文件进行智能分析")
    public ApiResponse<Map<String, Object>> uploadPdf(
            @Parameter(description = "PDF文件", required = true)
            @RequestParam("file") @NotNull(message = "文件不能为空") MultipartFile file,
            
            @Parameter(description = "股票代码", required = true)
            @RequestParam @NotBlank(message = "股票代码不能为空") String stockCode,
            
            @Parameter(description = "年份", required = true)
            @RequestParam @NotNull(message = "年份不能为空") Integer year,
            
            @Parameter(description = "报告类型", required = true)
            @RequestParam @NotBlank(message = "报告类型不能为空") String reportType) {
        
        log.info("接收到PDF上传请求，股票代码: {}, 年份: {}, 报告类型: {}, 文件大小: {} bytes", 
                stockCode, year, reportType, file.getSize());
        
        try {
            Map<String, Object> result = smartAnalysisService.uploadPdf(file, stockCode, year, reportType);
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("PDF上传失败", e);
            return ApiResponse.serverError("PDF上传失败: " + e.getMessage());
        }
    }
    
    /**
     * 智能分析财务报告
     * 
     * @param request 分析请求参数
     * @return 分析结果
     */
    @PostMapping("/analyze")
    @Operation(summary = "智能分析财务报告", description = "对上传的PDF文件进行智能分析，生成结构化报告")
    public ApiResponse<SmartAnalysisResultDTO> analyzeReport(
            @Valid @RequestBody SmartAnalysisRequestDTO request) {
        
        log.info("接收到智能分析请求，文件ID: {}, 分析模式: {}", 
                request.getFileId(), request.getAnalysisMode());
        
        try {
            SmartAnalysisResultDTO result = smartAnalysisService.analyzeReport(request);
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("智能分析失败", e);
            return ApiResponse.serverError("智能分析失败: " + e.getMessage());
        }
    }
    
    /**
     * 实时聊天接口（Server-Sent Events）
     * 
     * @param fileId 文件ID
     * @param question 用户问题
     * @return SSE流
     */
    @GetMapping(value = "/chat", produces = MediaType.TEXT_EVENT_STREAM_VALUE)
    @Operation(summary = "实时聊天", description = "基于分析结果进行实时问答聊天")
    public ResponseEntity<Flux<String>> chat(
            @Parameter(description = "文件ID", required = true)
            @RequestParam @NotBlank(message = "文件ID不能为空") String fileId,
            
            @Parameter(description = "用户问题", required = true)
            @RequestParam @NotBlank(message = "问题不能为空") String question) {
        
        log.info("接收到聊天请求，文件ID: {}, 问题: {}", fileId, question);
        
        try {
            Flux<String> chatStream = smartAnalysisService.chatWithReport(fileId, question);
            return ResponseEntity.ok()
                    .header("Cache-Control", "no-cache")
                    .header("Connection", "keep-alive")
                    .body(chatStream);
        } catch (Exception e) {
            log.error("聊天请求失败", e);
            return ResponseEntity.internalServerError().build();
        }
    }
    
    /**
     * 获取分析历史
     * 
     * @param stockCode 股票代码（可选）
     * @return 分析历史列表
     */
    @GetMapping("/history")
    @Operation(summary = "获取分析历史", description = "获取用户的分析历史记录")
    public ApiResponse<Map<String, Object>> getAnalysisHistory(
            @Parameter(description = "股票代码", required = false)
            @RequestParam(required = false) String stockCode) {
        
        log.info("获取分析历史，股票代码: {}", stockCode);
        
        try {
            Map<String, Object> result = smartAnalysisService.getAnalysisHistory(stockCode);
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("获取分析历史失败", e);
            return ApiResponse.serverError("获取分析历史失败: " + e.getMessage());
        }
    }
    
    /**
     * 删除分析记录
     * 
     * @param fileId 文件ID
     * @return 删除结果
     */
    @DeleteMapping("/analysis/{fileId}")
    @Operation(summary = "删除分析记录", description = "删除指定的分析记录")
    public ApiResponse<Map<String, Object>> deleteAnalysis(
            @Parameter(description = "文件ID", required = true)
            @PathVariable @NotBlank(message = "文件ID不能为空") String fileId) {
        
        log.info("删除分析记录，文件ID: {}", fileId);
        
        try {
            Map<String, Object> result = smartAnalysisService.deleteAnalysis(fileId);
            return ApiResponse.success(result);
        } catch (Exception e) {
            log.error("删除分析记录失败", e);
            return ApiResponse.serverError("删除分析记录失败: " + e.getMessage());
        }
    }
}