package com.tonghuashun.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.reactive.function.client.WebClient;

import java.time.Duration;

/**
 * WebClient配置类
 * 配置HTTP客户端用于调用外部服务
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Configuration
public class WebClientConfig {
    
    @Value("${python-service.base-url:http://localhost:8000}")
    private String pythonServiceBaseUrl;
    
    @Value("${ai-service.base-url:http://localhost:8000}")
    private String aiServiceBaseUrl;
    
    /**
     * 配置Python服务WebClient
     * 
     * @return WebClient实例
     */
    @Bean("pythonWebClient")
    public WebClient pythonWebClient() {
        return WebClient.builder()
                .baseUrl(pythonServiceBaseUrl)
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .build();
    }
    
    /**
     * 配置AI服务WebClient
     * 
     * @return WebClient实例
     */
    @Bean("aiWebClient")
    public WebClient aiWebClient() {
        return WebClient.builder()
                .baseUrl(aiServiceBaseUrl)
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .build();
    }
    
    /**
     * 默认WebClient（用于通用HTTP调用）
     * 
     * @return WebClient实例
     */
    @Bean
    public WebClient webClient() {
        return WebClient.builder()
                .codecs(configurer -> configurer.defaultCodecs().maxInMemorySize(10 * 1024 * 1024)) // 10MB
                .build();
    }
}