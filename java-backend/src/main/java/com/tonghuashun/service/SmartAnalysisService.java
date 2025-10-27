package com.tonghuashun.service;

import com.tonghuashun.dto.SmartAnalysisRequestDTO;
import com.tonghuashun.dto.SmartAnalysisResultDTO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import reactor.core.publisher.Flux;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.StandardCopyOption;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * 智能分析业务服务类
 * 提供智能分析相关的业务逻辑处理
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class SmartAnalysisService {
    
    private final PythonServiceClient pythonServiceClient;
    private final AiAnalysisService aiAnalysisService;
    
    // 文件上传目录
    private static final String UPLOAD_DIR = "uploads";
    
    /**
     * 上传PDF文件
     * 
     * @param file PDF文件
     * @param stockCode 股票代码
     * @param year 年份
     * @param reportType 报告类型
     * @return 上传结果
     */
    public Map<String, Object> uploadPdf(MultipartFile file, String stockCode, Integer year, String reportType) {
        log.info("开始处理PDF上传，股票代码: {}, 年份: {}, 报告类型: {}", stockCode, year, reportType);
        
        try {
            // 验证文件
            validatePdfFile(file);
            
            // 生成文件ID和文件名
            String fileId = generateFileId(stockCode, year, reportType);
            String fileName = generateFileName(stockCode, year, reportType, file.getOriginalFilename());
            
            // 确保上传目录存在
            Path uploadPath = Paths.get(UPLOAD_DIR);
            if (!Files.exists(uploadPath)) {
                Files.createDirectories(uploadPath);
            }
            
            // 保存文件
            Path filePath = uploadPath.resolve(fileName);
            Files.copy(file.getInputStream(), filePath, StandardCopyOption.REPLACE_EXISTING);
            
            log.info("PDF文件上传成功，文件ID: {}, 文件路径: {}", fileId, filePath);
            
            // 构建响应结果
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("fileId", fileId);
            result.put("fileName", fileName);
            result.put("filePath", filePath.toString());
            result.put("fileSize", file.getSize());
            result.put("uploadTime", LocalDateTime.now());
            result.put("message", "PDF文件上传成功");
            
            return result;
            
        } catch (Exception e) {
            log.error("PDF文件上传失败", e);
            throw new RuntimeException("PDF文件上传失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 智能分析财务报告
     * 
     * @param request 分析请求参数
     * @return 分析结果
     */
    public SmartAnalysisResultDTO analyzeReport(SmartAnalysisRequestDTO request) {
        log.info("开始智能分析，文件ID: {}, 分析模式: {}", request.getFileId(), request.getAnalysisMode());
        
        try {
            // 1. 获取文件路径
            String filePath = getFilePathByFileId(request.getFileId());
            
            // 2. 调用Python服务解析PDF
            Map<String, Object> pdfContent = pythonServiceClient.parsePdf(filePath);
            
            // 3. 调用AI服务进行智能分析
            SmartAnalysisResultDTO result = aiAnalysisService.analyzeFinancialReport(request, pdfContent);
            
            // 4. 保存分析结果（这里可以添加数据库存储逻辑）
            saveAnalysisResult(result);
            
            log.info("智能分析完成，分析ID: {}", result.getAnalysisId());
            return result;
            
        } catch (Exception e) {
            log.error("智能分析失败", e);
            throw new RuntimeException("智能分析失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 与报告进行实时聊天
     * 
     * @param fileId 文件ID
     * @param question 用户问题
     * @return SSE流
     */
    public Flux<String> chatWithReport(String fileId, String question) {
        log.info("开始聊天会话，文件ID: {}, 问题: {}", fileId, question);
        
        try {
            // 获取分析结果作为上下文
            SmartAnalysisResultDTO analysisResult = getAnalysisResultByFileId(fileId);
            
            // 调用AI服务进行流式聊天
            return aiAnalysisService.chatWithReport(analysisResult, question);
            
        } catch (Exception e) {
            log.error("聊天会话失败", e);
            return Flux.error(new RuntimeException("聊天会话失败: " + e.getMessage(), e));
        }
    }
    
    /**
     * 获取分析历史
     * 
     * @param stockCode 股票代码（可选）
     * @return 分析历史列表
     */
    public Map<String, Object> getAnalysisHistory(String stockCode) {
        log.info("获取分析历史，股票代码: {}", stockCode);
        
        try {
            // 这里应该从数据库查询，现在返回模拟数据
            List<Map<String, Object>> historyList = new ArrayList<>();
            
            // 模拟数据
            Map<String, Object> history1 = new HashMap<>();
            history1.put("analysisId", "analysis_001");
            history1.put("fileId", "file_001");
            history1.put("stockCode", "600519");
            history1.put("stockName", "贵州茅台");
            history1.put("year", 2023);
            history1.put("reportType", "年报");
            history1.put("analysisMode", "single");
            history1.put("analysisTime", LocalDateTime.now().minusDays(1));
            history1.put("status", "completed");
            
            historyList.add(history1);
            
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("total", historyList.size());
            result.put("data", historyList);
            
            return result;
            
        } catch (Exception e) {
            log.error("获取分析历史失败", e);
            throw new RuntimeException("获取分析历史失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 删除分析记录
     * 
     * @param fileId 文件ID
     * @return 删除结果
     */
    public Map<String, Object> deleteAnalysis(String fileId) {
        log.info("删除分析记录，文件ID: {}", fileId);
        
        try {
            // 这里应该删除数据库记录和文件，现在只是模拟
            Map<String, Object> result = new HashMap<>();
            result.put("success", true);
            result.put("message", "分析记录删除成功");
            
            return result;
            
        } catch (Exception e) {
            log.error("删除分析记录失败", e);
            throw new RuntimeException("删除分析记录失败: " + e.getMessage(), e);
        }
    }
    
    // 私有辅助方法
    
    private void validatePdfFile(MultipartFile file) {
        if (file.isEmpty()) {
            throw new IllegalArgumentException("文件不能为空");
        }
        
        if (file.getSize() > 50 * 1024 * 1024) { // 50MB限制
            throw new IllegalArgumentException("文件大小不能超过50MB");
        }
        
        String contentType = file.getContentType();
        if (!"application/pdf".equals(contentType)) {
            throw new IllegalArgumentException("只支持PDF文件格式");
        }
    }
    
    private String generateFileId(String stockCode, Integer year, String reportType) {
        return String.format("file_%s_%d_%s_%d", 
                stockCode, year, reportType, System.currentTimeMillis());
    }
    
    private String generateFileName(String stockCode, Integer year, String reportType, String originalFileName) {
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyyMMdd_HHmmss"));
        String extension = originalFileName.substring(originalFileName.lastIndexOf("."));
        return String.format("%s_%s_%d_%s%s", stockCode, reportType, year, timestamp, extension);
    }
    
    private String getFilePathByFileId(String fileId) {
        // 解析文件ID获取文件信息
        // 文件ID格式: file_stockCode_year_reportType_timestamp
        try {
            String[] parts = fileId.split("_");
            if (parts.length >= 5) {
                String stockCode = parts[1];
                String year = parts[2];
                String reportType = parts[3];
                String timestamp = parts[4];
                
                // 构建文件名模式并查找匹配的文件
                String filePattern = stockCode + "_" + reportType + "_" + year;
                Path uploadPath = Paths.get(UPLOAD_DIR).toAbsolutePath();
                
                if (Files.exists(uploadPath)) {
                    try {
                        // 在匹配的文件中选择最合适的一个：
                        // 1) 以模式开头；2) 扩展名为.pdf；3) 文件大小最大（排除空/占位文件）
                        Optional<Path> bestFile = Files.list(uploadPath)
                                .filter(path -> {
                                    String name = path.getFileName().toString();
                                    return name.startsWith(filePattern) && name.toLowerCase().endsWith(".pdf");
                                })
                                .max((p1, p2) -> {
                                    try {
                                        long s1 = Files.size(p1);
                                        long s2 = Files.size(p2);
                                        return Long.compare(s1, s2);
                                    } catch (IOException ioe) {
                                        // 若获取大小失败，则保持原顺序
                                        return 0;
                                    }
                                });

                        if (bestFile.isPresent()) {
                            Path chosen = bestFile.get().toAbsolutePath();
                            try {
                                long size = Files.size(chosen);
                                log.info("选择到最佳匹配文件: {}, 大小: {} 字节", chosen, size);
                            } catch (IOException ignore) {
                                log.info("选择到最佳匹配文件: {}", chosen);
                            }
                            return chosen.toString();
                        } else {
                            log.warn("未找到匹配文件，模式: {}，目录: {}", filePattern, uploadPath);
                        }
                    } catch (IOException e) {
                        log.error("查找文件失败: {}", e.getMessage());
                    }
                } else {
                    log.warn("上传目录不存在: {}", uploadPath);
                }
            }
        } catch (Exception e) {
            log.error("解析文件ID失败: {}, 错误: {}", fileId, e.getMessage());
        }
        
        // 如果解析失败，返回默认路径的绝对路径
        Path defaultPath = Paths.get(UPLOAD_DIR, "sample.pdf").toAbsolutePath();
        log.warn("使用默认文件路径: {}", defaultPath.toString());
        return defaultPath.toString();
    }
    
    private void saveAnalysisResult(SmartAnalysisResultDTO result) {
        // 这里应该保存到数据库
        log.info("保存分析结果，分析ID: {}", result.getAnalysisId());
    }
    
    private SmartAnalysisResultDTO getAnalysisResultByFileId(String fileId) {
        // 这里应该从数据库查询分析结果，现在返回模拟数据
        SmartAnalysisResultDTO result = new SmartAnalysisResultDTO();
        result.setAnalysisId("analysis_" + fileId);
        result.setFileId(fileId);
        result.setStockCode("600519");
        result.setStockName("贵州茅台");
        result.setYear(2023);
        result.setReportType("年报");
        result.setAnalysisMode("single");
        result.setAnalysisTime(LocalDateTime.now());
        result.setExecutiveSummary("这是一个模拟的执行摘要");
        result.setStatus("completed");
        
        return result;
    }
}