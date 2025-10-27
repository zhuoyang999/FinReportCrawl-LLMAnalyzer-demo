package com.tonghuashun.service;

import com.tonghuashun.dto.FinancialReportDTO;
import com.tonghuashun.dto.CrawlRequestDTO;
import com.tonghuashun.dto.QueryRequestDTO;
import com.tonghuashun.common.PageResponse;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.ParameterizedTypeReference;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import org.springframework.web.reactive.function.client.WebClientResponseException;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * Python FastAPI 服务客户端
 * 负责与 Python 服务进行通信
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class PythonServiceClient {
    
    @Qualifier("pythonWebClient")
    private final WebClient webClient;
    

    
    /**
     * 调用爬取接口
     * 
     * @param request 爬取请求参数
     * @return 爬取结果
     */
    public Map<String, Object> crawlReport(CrawlRequestDTO request) {
        log.info("开始调用Python爬取接口，股票代码: {}, 年份: {}, 报告类型: {}", 
                request.getStockCode(), request.getYear(), request.getReportType());
        
        try {
            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("stock_code", request.getStockCode());
            requestBody.put("year", request.getYear());
            requestBody.put("report_type", request.getReportType());
            
            // 发送请求
            Map<String, Object> response = webClient.post()
                    .uri("/api/crawl")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(30))
                    .block();
            
            log.info("Python爬取接口调用成功，股票代码: {}", request.getStockCode());
            return response;
            
        } catch (WebClientResponseException e) {
            log.error("Python爬取接口调用失败，状态码: {}, 响应体: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new RuntimeException("爬取服务调用失败: " + e.getMessage());
        } catch (Exception e) {
            log.error("Python爬取接口调用异常", e);
            throw new RuntimeException("爬取服务调用异常: " + e.getMessage());
        }
    }
    
    /**
     * 手动触发PDF处理
     * 
     * @param stockCode 股票代码
     * @param year 年份
     * @param reportType 报告类型
     * @return 处理结果
     */
    public Map<String, Object> processPdfs(String stockCode, Integer year, String reportType) {
        log.info("开始调用Python PDF处理接口，股票代码: {}, 年份: {}, 报告类型: {}", 
                stockCode, year, reportType);
        
        try {
            // 构建请求体
            Map<String, Object> requestBody = new HashMap<>();
            requestBody.put("stock_code", stockCode);
            requestBody.put("year", year);
            requestBody.put("report_type", reportType);
            
            // 发送请求
            Map<String, Object> response = webClient.post()
                    .uri("/api/process-pdfs")
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(60))
                    .block();
            
            log.info("Python PDF处理接口调用成功，股票代码: {}", stockCode);
            return response;
            
        } catch (WebClientResponseException e) {
            log.error("Python PDF处理接口调用失败，状态码: {}, 响应体: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new RuntimeException("PDF处理服务调用失败: " + e.getMessage());
        } catch (Exception e) {
            log.error("Python PDF处理接口调用异常", e);
            throw new RuntimeException("PDF处理服务调用异常: " + e.getMessage());
        }
    }
    
    /**
     * 查询财务报告
     * 
     * @param request 查询请求参数
     * @return 查询结果
     */
    public PageResponse<FinancialReportDTO> queryReports(QueryRequestDTO request) {
        log.info("开始调用Python查询接口，股票代码: {}, 公司名称: {}, 页码: {}, 每页大小: {}", 
                request.getStockCode(), request.getCompanyName(), request.getPage(), request.getSize());
        
        try {
            // 构建查询参数
            StringBuilder uriBuilder = new StringBuilder("/api/financial-reports?");
            
            if (request.getStockCode() != null && !request.getStockCode().trim().isEmpty()) {
                uriBuilder.append("stock_code=").append(request.getStockCode()).append("&");
            }
            if (request.getCompanyName() != null && !request.getCompanyName().trim().isEmpty()) {
                uriBuilder.append("company_name=").append(request.getCompanyName()).append("&");
            }
            if (request.getReportType() != null && !request.getReportType().trim().isEmpty()) {
                uriBuilder.append("report_type=").append(request.getReportType()).append("&");
            }
            if (request.getStartYear() != null) {
                uriBuilder.append("start_year=").append(request.getStartYear()).append("&");
            }
            if (request.getEndYear() != null) {
                uriBuilder.append("end_year=").append(request.getEndYear()).append("&");
            }
            
            uriBuilder.append("page=").append(request.getPage());
            uriBuilder.append("&size=").append(request.getSize());
            
            // 发送请求
            Map<String, Object> response = webClient.get()
                    .uri(uriBuilder.toString())
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(30))
                    .block();
            
            // 解析响应
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> items = (List<Map<String, Object>>) response.get("items");
            Integer page = (Integer) response.get("page");
            Integer size = (Integer) response.get("size");
            Long total = ((Number) response.get("total")).longValue();
            
            // 转换为DTO
            List<FinancialReportDTO> reportDTOs = items.stream()
                    .map(this::convertToFinancialReportDTO)
                    .toList();
            
            PageResponse<FinancialReportDTO> pageResponse = PageResponse.of(reportDTOs, page, size, total);
            
            log.info("Python查询接口调用成功，返回 {} 条记录", reportDTOs.size());
            return pageResponse;
            
        } catch (WebClientResponseException e) {
            log.error("Python查询接口调用失败，状态码: {}, 响应体: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new RuntimeException("查询服务调用失败: " + e.getMessage());
        } catch (Exception e) {
            log.error("Python查询接口调用异常", e);
            throw new RuntimeException("查询服务调用异常: " + e.getMessage());
        }
    }
    
    /**
     * 获取服务健康状态
     * 
     * @return 健康状态信息
     */
    public Map<String, Object> getHealthStatus() {
        log.debug("开始检查Python服务健康状态");
        
        try {
            Map<String, Object> response = webClient.get()
                    .uri("/api/health")
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(10))
                    .block();
            
            log.debug("Python服务健康状态检查成功");
            return response;
            
        } catch (Exception e) {
            log.warn("Python服务健康状态检查失败", e);
            Map<String, Object> errorResponse = new HashMap<>();
            errorResponse.put("status", "DOWN");
            errorResponse.put("error", e.getMessage());
            return errorResponse;
        }
    }
    
    /**
     * 获取统计信息
     * 
     * @return 统计信息
     */
    public Map<String, Object> getStats() {
        log.debug("开始获取Python服务统计信息");
        
        try {
            Map<String, Object> response = webClient.get()
                    .uri("/api/stats")
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofSeconds(10))
                    .block();
            
            log.debug("Python服务统计信息获取成功");
            return response;
            
        } catch (Exception e) {
            log.warn("Python服务统计信息获取失败", e);
            throw new RuntimeException("统计信息获取失败: " + e.getMessage());
        }
    }
    
    /**
     * 将Map转换为FinancialReportDTO
     * 
     * @param map 原始数据Map
     * @return FinancialReportDTO对象
     */
    private FinancialReportDTO convertToFinancialReportDTO(Map<String, Object> map) {
        FinancialReportDTO dto = new FinancialReportDTO();
        
        if (map.get("id") != null) {
            dto.setId(((Number) map.get("id")).longValue());
        }
        dto.setStockCode((String) map.get("stock_code"));
        dto.setCompanyName((String) map.get("company_name"));
        dto.setTitle((String) map.get("title"));
        dto.setReportType((String) map.get("report_type"));
        if (map.get("year") != null) {
            dto.setYear(((Number) map.get("year")).intValue());
        }
        dto.setPdfPath((String) map.get("pdf_path"));
        dto.setProcessingStatus((String) map.get("processing_status"));
        
        // 注意：日期字段的转换可能需要根据实际返回格式进行调整
        // 这里假设Python服务返回的是ISO格式的字符串
        
        return dto;
    }

    /**
     * 解析PDF文件
     * 
     * @param filePath PDF文件路径
     * @return 解析结果
     */
    public Map<String, Object> parsePdf(String filePath) {
        log.info("开始解析PDF文件: {}", filePath);
        
        try {
            Map<String, String> requestBody = new HashMap<>();
            requestBody.put("file_path", filePath);
            
            Map<String, Object> response = webClient.post()
                    .uri("/parse-pdf")  // 注意：这个端点没有/api前缀
                    .bodyValue(requestBody)
                    .retrieve()
                    .bodyToMono(new ParameterizedTypeReference<Map<String, Object>>() {})
                    .timeout(Duration.ofMinutes(5)) // PDF解析可能需要更长时间
                    .block();
            
            log.info("PDF解析完成: {}", filePath);
            return response;
            
        } catch (WebClientResponseException e) {
            log.error("PDF解析失败，HTTP状态码: {}, 响应体: {}", e.getStatusCode(), e.getResponseBodyAsString());
            throw new RuntimeException("PDF解析失败: " + e.getMessage(), e);
        } catch (Exception e) {
            log.error("PDF解析过程中发生异常", e);
            throw new RuntimeException("PDF解析失败: " + e.getMessage(), e);
        }
    }
}