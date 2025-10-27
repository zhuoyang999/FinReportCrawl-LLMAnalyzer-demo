package com.tonghuashun.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.tonghuashun.dto.SmartAnalysisRequestDTO;
import com.tonghuashun.dto.SmartAnalysisResultDTO;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.reactive.function.client.WebClient;
import reactor.core.publisher.Flux;
import reactor.core.publisher.Mono;

import java.time.Duration;
import java.time.LocalDateTime;
import java.util.*;

/**
 * AI分析服务类
 * 负责与AI模型进行交互，处理财务报告分析和聊天功能
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class AiAnalysisService {
    
    @Qualifier("aiWebClient")
    private final WebClient webClient;
    private final ObjectMapper objectMapper;
    
    @Value("${ai-service.base-url:http://localhost:8000}")
    private String aiServiceBaseUrl;
    
    @Value("${ai-service.timeout:60000}")
    private Long timeout;
    
    /**
     * 智能分析财务报告
     * 
     * @param request 分析请求
     * @param pdfContent PDF解析内容
     * @return 分析结果
     */
    public SmartAnalysisResultDTO analyzeFinancialReport(SmartAnalysisRequestDTO request, Map<String, Object> pdfContent) {
        log.info("开始AI分析，股票代码: {}, 分析模式: {}", request.getStockCode(), request.getAnalysisMode());
        
        try {
            // 构建AI分析请求
            Map<String, Object> aiRequest = buildAnalysisRequest(request, pdfContent);
            
            // 调用AI服务
            Map<String, Object> aiResponse = callAiAnalysisService(aiRequest);
            
            // 构建分析结果
            SmartAnalysisResultDTO result = buildAnalysisResult(request, aiResponse);
            
            log.info("AI分析完成，分析ID: {}", result.getAnalysisId());
            return result;
            
        } catch (Exception e) {
            log.error("AI分析失败", e);
            throw new RuntimeException("AI分析失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 与报告进行实时聊天
     * 
     * @param analysisResult 分析结果作为上下文
     * @param question 用户问题
     * @return SSE流
     */
    public Flux<String> chatWithReport(SmartAnalysisResultDTO analysisResult, String question) {
        log.info("开始AI聊天，分析ID: {}, 问题: {}", analysisResult.getAnalysisId(), question);
        
        try {
            // 构建聊天请求
            Map<String, Object> chatRequest = buildChatRequest(analysisResult, question);
            
            // 调用AI服务进行流式聊天
            return callAiChatService(chatRequest);
            
        } catch (Exception e) {
            log.error("AI聊天失败", e);
            return Flux.error(new RuntimeException("AI聊天失败: " + e.getMessage(), e));
        }
    }
    
    /**
     * 构建AI分析请求
     */
    private Map<String, Object> buildAnalysisRequest(SmartAnalysisRequestDTO request, Map<String, Object> pdfContent) {
        Map<String, Object> aiRequest = new HashMap<>();
        
        // 基本信息
        aiRequest.put("stockCode", request.getStockCode());
        aiRequest.put("year", request.getYear());
        aiRequest.put("reportType", request.getReportType());
        aiRequest.put("analysisMode", request.getAnalysisMode());
        aiRequest.put("model", request.getModel());
        
        // PDF内容
        aiRequest.put("pdfContent", pdfContent);
        
        // 自定义要求
        if (request.getCustomRequirements() != null && !request.getCustomRequirements().trim().isEmpty()) {
            aiRequest.put("customRequirements", request.getCustomRequirements());
        }
        
        // 系统提示词
        aiRequest.put("systemPrompt", buildSystemPrompt(request.getAnalysisMode()));
        
        return aiRequest;
    }
    
    /**
     * 构建系统提示词
     */
    private String buildSystemPrompt(String analysisMode) {
        StringBuilder prompt = new StringBuilder();
        
        prompt.append("你是一位专业的财务分析师，具有丰富的财务报告分析经验。");
        prompt.append("请根据提供的财务报告内容，进行深入的专业分析。");
        
        switch (analysisMode) {
            case "single":
                prompt.append("请进行单一报告分析，重点关注：");
                prompt.append("1. 财务状况分析（资产负债结构、偿债能力）");
                prompt.append("2. 盈利能力分析（营收增长、利润率、ROE等）");
                prompt.append("3. 现金流分析（经营、投资、筹资现金流）");
                prompt.append("4. 风险识别与评估");
                prompt.append("5. 投资建议");
                break;
            case "timeSeries":
                prompt.append("请进行时间序列分析，重点关注：");
                prompt.append("1. 多年财务指标趋势分析");
                prompt.append("2. 增长率变化趋势");
                prompt.append("3. 周期性特征识别");
                prompt.append("4. 未来趋势预测");
                break;
            case "peerComparison":
                prompt.append("请进行同行对比分析，重点关注：");
                prompt.append("1. 与同行业公司的财务指标对比");
                prompt.append("2. 市场地位和竞争优势分析");
                prompt.append("3. 相对估值水平");
                break;
            case "industryAnalysis":
                prompt.append("请进行行业分析，重点关注：");
                prompt.append("1. 行业发展趋势和周期");
                prompt.append("2. 公司在行业中的地位");
                prompt.append("3. 行业风险和机遇");
                break;
        }
        
        prompt.append("请以结构化的JSON格式返回分析结果。");
        
        return prompt.toString();
    }
    
    /**
     * 调用AI分析服务
     */
    private Map<String, Object> callAiAnalysisService(Map<String, Object> request) {
        try {
            // 这里应该调用实际的AI服务，现在返回模拟数据
            return createMockAnalysisResponse(request);
            
        } catch (Exception e) {
            log.error("调用AI分析服务失败", e);
            throw new RuntimeException("调用AI分析服务失败: " + e.getMessage(), e);
        }
    }
    
    /**
     * 构建分析结果
     */
    private SmartAnalysisResultDTO buildAnalysisResult(SmartAnalysisRequestDTO request, Map<String, Object> aiResponse) {
        SmartAnalysisResultDTO result = new SmartAnalysisResultDTO();
        
        // 基本信息
        result.setAnalysisId("analysis_" + System.currentTimeMillis());
        result.setFileId(request.getFileId());
        result.setStockCode(request.getStockCode());
        result.setYear(request.getYear());
        result.setReportType(request.getReportType());
        result.setAnalysisMode(request.getAnalysisMode());
        result.setAnalysisTime(LocalDateTime.now());
        result.setStatus("completed");
        
        // 从AI响应中提取分析结果
        result.setExecutiveSummary((String) aiResponse.get("executiveSummary"));
        result.setFinancialHighlights((List<String>) aiResponse.get("financialHighlights"));
        result.setRiskWarnings((List<String>) aiResponse.get("riskWarnings"));
        result.setInvestmentAdvice((String) aiResponse.get("investmentAdvice"));
        result.setDetailedAnalysis((Map<String, Object>) aiResponse.get("detailedAnalysis"));
        result.setKeyMetrics((Map<String, Object>) aiResponse.get("keyMetrics"));
        result.setConfidenceScore((Double) aiResponse.get("confidenceScore"));
        result.setDataSources((List<String>) aiResponse.get("dataSources"));
        
        // 根据分析模式设置特定结果
        if ("peerComparison".equals(request.getAnalysisMode())) {
            result.setPeerComparison((Map<String, Object>) aiResponse.get("peerComparison"));
        }
        if ("timeSeries".equals(request.getAnalysisMode())) {
            result.setTimeSeriesAnalysis((Map<String, Object>) aiResponse.get("timeSeriesAnalysis"));
        }
        if ("industryAnalysis".equals(request.getAnalysisMode())) {
            result.setIndustryAnalysis((Map<String, Object>) aiResponse.get("industryAnalysis"));
        }
        
        return result;
    }
    
    /**
     * 构建聊天请求
     */
    private Map<String, Object> buildChatRequest(SmartAnalysisResultDTO analysisResult, String question) {
        Map<String, Object> chatRequest = new HashMap<>();
        
        chatRequest.put("analysisId", analysisResult.getAnalysisId());
        chatRequest.put("question", question);
        chatRequest.put("context", analysisResult);
        chatRequest.put("systemPrompt", "你是一位专业的财务分析师，请基于已有的分析结果回答用户问题。");
        
        return chatRequest;
    }
    
    /**
     * 调用AI聊天服务
     */
    private Flux<String> callAiChatService(Map<String, Object> request) {
        try {
            // 这里应该调用实际的AI流式服务，现在返回模拟数据
            return createMockChatResponse(request);
            
        } catch (Exception e) {
            log.error("调用AI聊天服务失败", e);
            return Flux.error(new RuntimeException("调用AI聊天服务失败: " + e.getMessage(), e));
        }
    }
    
    /**
     * 创建模拟分析响应
     */
    private Map<String, Object> createMockAnalysisResponse(Map<String, Object> request) {
        Map<String, Object> response = new HashMap<>();
        
        response.put("executiveSummary", "该公司2023年财务表现良好，营收同比增长15%，净利润增长12%，整体财务状况稳健。");
        
        List<String> highlights = Arrays.asList(
                "营业收入同比增长15%，达到1000亿元",
                "净利润率保持在20%以上的高水平",
                "资产负债率控制在合理范围内",
                "现金流充裕，经营活动现金流净额为正"
        );
        response.put("financialHighlights", highlights);
        
        List<String> risks = Arrays.asList(
                "行业竞争加剧可能影响市场份额",
                "原材料价格波动风险",
                "汇率变动对出口业务的影响"
        );
        response.put("riskWarnings", risks);
        
        response.put("investmentAdvice", "基于当前财务状况和行业前景，建议持有该股票，目标价位上调10%。");
        response.put("confidenceScore", 0.85);
        
        List<String> sources = Arrays.asList("年度报告", "财务报表", "行业数据");
        response.put("dataSources", sources);
        
        // 详细分析
        Map<String, Object> detailed = new HashMap<>();
        detailed.put("profitability", "盈利能力强，ROE达到18%");
        detailed.put("liquidity", "流动性良好，流动比率2.1");
        detailed.put("leverage", "财务杠杆适中，资产负债率45%");
        response.put("detailedAnalysis", detailed);
        
        // 关键指标
        Map<String, Object> metrics = new HashMap<>();
        metrics.put("revenue", 100000000000L);
        metrics.put("netProfit", 20000000000L);
        metrics.put("roe", 0.18);
        metrics.put("roa", 0.12);
        response.put("keyMetrics", metrics);
        
        return response;
    }
    
    /**
     * 创建模拟聊天响应
     */
    private Flux<String> createMockChatResponse(Map<String, Object> request) {
        String question = (String) request.get("question");
        
        List<String> responses = Arrays.asList(
                "data: 根据分析结果，",
                "data: 该公司的财务状况",
                "data: 确实表现良好。",
                "data: 具体来说，",
                "data: 营收增长15%，",
                "data: 净利润增长12%，",
                "data: 这表明公司",
                "data: 具有良好的",
                "data: 盈利能力和",
                "data: 成长性。",
                "data: [DONE]"
        );
        
        return Flux.fromIterable(responses)
                .delayElements(Duration.ofMillis(200))
                .map(response -> response + "\n\n");
    }
}