package com.tonghuashun.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;

/**
 * 智能分析请求DTO
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Data
@Schema(description = "智能分析请求参数")
public class SmartAnalysisRequestDTO {
    
    @Schema(description = "文件ID", required = true, example = "file_123456")
    @NotBlank(message = "文件ID不能为空")
    private String fileId;
    
    @Schema(description = "股票代码", required = true, example = "600519")
    @NotBlank(message = "股票代码不能为空")
    private String stockCode;
    
    @Schema(description = "年份", required = true, example = "2023")
    @NotNull(message = "年份不能为空")
    private Integer year;
    
    @Schema(description = "报告类型", required = true, example = "年报")
    @NotBlank(message = "报告类型不能为空")
    private String reportType;
    
    @Schema(description = "分析模式", required = true, example = "single", 
            allowableValues = {"single", "timeSeries", "peerComparison", "industryAnalysis"})
    @NotBlank(message = "分析模式不能为空")
    private String analysisMode;
    
    @Schema(description = "分析模型", required = true, example = "qwen-max")
    @NotBlank(message = "分析模型不能为空")
    private String model;
    
    @Schema(description = "自定义分析要求", required = false, example = "重点关注盈利能力和现金流")
    private String customRequirements;
}