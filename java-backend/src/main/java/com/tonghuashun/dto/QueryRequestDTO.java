package com.tonghuashun.dto;

import lombok.Data;
import jakarta.validation.constraints.Min;
import jakarta.validation.constraints.Max;

/**
 * 查询请求数据传输对象
 * 用于接收前端查询请求参数
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Data
public class QueryRequestDTO {
    
    /**
     * 股票代码（可选）
     */
    private String stockCode;
    
    /**
     * 公司名称（可选，支持模糊查询）
     */
    private String companyName;
    
    /**
     * 报告类型（可选）
     */
    private String reportType;
    
    /**
     * 开始年份（可选）
     */
    private Integer startYear;
    
    /**
     * 结束年份（可选）
     */
    private Integer endYear;
    
    /**
     * 页码（默认为1）
     */
    @Min(value = 1, message = "页码不能小于1")
    private Integer page = 1;
    
    /**
     * 每页大小（默认为10，最大100）
     */
    @Min(value = 1, message = "每页大小不能小于1")
    @Max(value = 100, message = "每页大小不能大于100")
    private Integer size = 10;
}