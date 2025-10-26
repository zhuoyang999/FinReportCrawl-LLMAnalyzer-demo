package com.tonghuashun.dto;

import com.fasterxml.jackson.annotation.JsonFormat;
import com.fasterxml.jackson.annotation.JsonProperty;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 财务报告数据传输对象
 * 用于前后端数据交互
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Data
public class FinancialReportDTO {
    
    /**
     * 报告ID
     */
    private Long id;
    
    /**
     * 股票代码
     */
    @JsonProperty("stock_code")
    private String stockCode;
    
    /**
     * 公司名称
     */
    @JsonProperty("company_name")
    private String companyName;
    
    /**
     * 报告标题
     */
    private String title;
    
    /**
     * 报告类型
     */
    @JsonProperty("report_type")
    private String reportType;
    
    /**
     * 报告年份
     */
    private Integer year;
    
    /**
     * 公告日期
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonProperty("announcement_date")
    private LocalDateTime announcementDate;
    
    /**
     * PDF文件路径
     */
    @JsonProperty("pdf_path")
    private String pdfPath;
    
    /**
     * 处理状态
     */
    @JsonProperty("processing_status")
    private String processingStatus;
    
    /**
     * 创建时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonProperty("created_at")
    private LocalDateTime createdAt;
    
    /**
     * 更新时间
     */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    @JsonProperty("updated_at")
    private LocalDateTime updatedAt;
}