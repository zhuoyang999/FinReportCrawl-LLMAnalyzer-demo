package com.tonghuashun.dto;

import lombok.Data;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;

/**
 * 爬取请求数据传输对象
 * 用于接收前端爬取请求参数
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Data
public class CrawlRequestDTO {
    
    /**
     * 股票代码（必填）
     */
    @NotBlank(message = "股票代码不能为空")
    private String stockCode;
    
    /**
     * 年份（必填，范围：2000-2030）
     */
    @NotNull(message = "年份不能为空")
    @Min(value = 2000, message = "年份不能小于2000")
    @Max(value = 2030, message = "年份不能大于2030")
    private Integer year;
    
    /**
     * 报告类型（必填）
     * 可选值：annual（年报）、interim（中报）、quarterly（季报）
     */
    @NotBlank(message = "报告类型不能为空")
    private String reportType;
}