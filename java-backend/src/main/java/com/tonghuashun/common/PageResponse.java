package com.tonghuashun.common;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;

import java.util.List;

/**
 * 分页响应结果封装类
 * 
 * @param <T> 数据项类型
 * @author Java后端架构师
 * @version 1.0.0
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class PageResponse<T> {
    
    /**
     * 数据列表
     */
    private List<T> items;
    
    /**
     * 当前页码
     */
    private Integer page;
    
    /**
     * 每页大小
     */
    private Integer size;
    
    /**
     * 总记录数
     */
    private Long total;
    
    /**
     * 总页数
     */
    private Integer totalPages;
    
    /**
     * 是否有下一页
     */
    private Boolean hasNext;
    
    /**
     * 是否有上一页
     */
    private Boolean hasPrevious;
    
    /**
     * 创建分页响应
     * 
     * @param items 数据列表
     * @param page 当前页码
     * @param size 每页大小
     * @param total 总记录数
     * @param <T> 数据项类型
     * @return 分页响应
     */
    public static <T> PageResponse<T> of(List<T> items, Integer page, Integer size, Long total) {
        PageResponse<T> response = new PageResponse<>();
        response.setItems(items);
        response.setPage(page);
        response.setSize(size);
        response.setTotal(total);
        
        // 计算总页数
        int totalPages = (int) Math.ceil((double) total / size);
        response.setTotalPages(totalPages);
        
        // 计算是否有上一页和下一页
        response.setHasPrevious(page > 1);
        response.setHasNext(page < totalPages);
        
        return response;
    }
}