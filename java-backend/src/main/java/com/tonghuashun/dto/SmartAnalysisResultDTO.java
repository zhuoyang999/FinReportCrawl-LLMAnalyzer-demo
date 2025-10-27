package com.tonghuashun.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

/**
 * 智能分析结果DTO
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Data
@Schema(description = "智能分析结果")
public class SmartAnalysisResultDTO {
    
    @Schema(description = "分析ID", example = "analysis_123456")
    private String analysisId;
    
    @Schema(description = "文件ID", example = "file_123456")
    private String fileId;
    
    @Schema(description = "股票代码", example = "600519")
    private String stockCode;
    
    @Schema(description = "股票名称", example = "贵州茅台")
    private String stockName;
    
    @Schema(description = "年份", example = "2023")
    private Integer year;
    
    @Schema(description = "报告类型", example = "年报")
    private String reportType;
    
    @Schema(description = "分析模式", example = "single")
    private String analysisMode;
    
    @Schema(description = "分析时间")
    private LocalDateTime analysisTime;
    
    @Schema(description = "执行摘要")
    private String executiveSummary;
    
    @Schema(description = "财务亮点")
    private List<String> financialHighlights;
    
    @Schema(description = "风险提示")
    private List<String> riskWarnings;
    
    @Schema(description = "投资建议")
    private String investmentAdvice;
    
    @Schema(description = "详细分析结果")
    private Map<String, Object> detailedAnalysis;
    
    @Schema(description = "关键财务指标")
    private Map<String, Object> keyMetrics;
    
    @Schema(description = "同行对比数据")
    private Map<String, Object> peerComparison;
    
    @Schema(description = "时间序列分析")
    private Map<String, Object> timeSeriesAnalysis;
    
    @Schema(description = "行业分析")
    private Map<String, Object> industryAnalysis;
    
    @Schema(description = "分析状态", example = "completed")
    private String status;
    
    @Schema(description = "置信度评分", example = "0.95")
    private Double confidenceScore;
    
    @Schema(description = "数据来源")
    private List<String> dataSources;
}