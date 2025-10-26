package com.tonghuashun.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.servers.Server;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

/**
 * Swagger API文档配置类
 * 配置API文档的基本信息和展示方式
 * 
 * @author Java后端架构师
 * @version 1.0.0
 */
@Configuration
public class SwaggerConfig {
    
    /**
     * 配置OpenAPI文档信息
     * 
     * @return OpenAPI配置
     */
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(apiInfo())
                .servers(List.of(
                        new Server()
                                .url("http://localhost:8080/api")
                                .description("本地开发环境"),
                        new Server()
                                .url("http://127.0.0.1:8080/api")
                                .description("本地开发环境（IP访问）")
                ));
    }
    
    /**
     * 配置API基本信息
     * 
     * @return API信息
     */
    private Info apiInfo() {
        return new Info()
                .title("同花顺财务报告系统 API")
                .description("提供财务报告爬取、处理和查询功能的RESTful API接口文档")
                .version("1.0.0")
                .contact(new Contact()
                        .name("Java后端架构师")
                        .email("architect@tonghuashun.com")
                        .url("https://www.tonghuashun.com"))
                .license(new License()
                        .name("MIT License")
                        .url("https://opensource.org/licenses/MIT"));
    }
}