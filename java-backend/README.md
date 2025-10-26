# 同花顺财务报告系统 - Java后端服务

## 项目简介

本项目是同花顺财务报告系统的Java后端服务，基于Spring Boot 3.2.0开发，提供财务报告爬取、处理和查询的RESTful API接口。

## 技术栈

- **Java**: 17
- **Spring Boot**: 3.2.0
- **Spring Web**: RESTful API开发
- **Spring WebFlux**: 异步HTTP客户端
- **Spring Validation**: 参数校验
- **Spring Actuator**: 健康检查和监控
- **Lombok**: 减少样板代码
- **Swagger/OpenAPI**: API文档
- **Maven**: 项目构建和依赖管理

## 项目结构

```
java-backend/
├── src/main/java/com/tonghuashun/
│   ├── FinancialReportApplication.java     # 主应用类
│   ├── controller/                         # 控制器层
│   │   └── FinancialReportController.java  # 财务报告控制器
│   ├── service/                           # 服务层
│   │   ├── FinancialReportService.java    # 财务报告业务服务
│   │   └── PythonServiceClient.java       # Python服务客户端
│   ├── dto/                               # 数据传输对象
│   │   ├── CrawlRequestDTO.java           # 爬取请求DTO
│   │   ├── QueryRequestDTO.java           # 查询请求DTO
│   │   └── FinancialReportDTO.java        # 财务报告DTO
│   ├── common/                            # 通用类
│   │   ├── ApiResponse.java               # 统一响应封装
│   │   └── PageResponse.java              # 分页响应封装
│   └── config/                            # 配置类
│       ├── CorsConfig.java                # CORS配置
│       ├── SwaggerConfig.java             # Swagger配置
│       └── GlobalExceptionHandler.java    # 全局异常处理
├── src/main/resources/
│   └── application.yml                     # 应用配置
├── pom.xml                                # Maven配置
├── start.bat                              # 启动脚本
└── README.md                              # 项目说明
```

## 核心功能

### 1. 财务报告爬取
- **接口**: `POST /api/financial-reports/crawl`
- **功能**: 根据股票代码、年份和报告类型爬取财务报告PDF
- **特点**: 爬取成功后自动触发PDF处理和数据库存储

### 2. PDF处理
- **接口**: `POST /api/financial-reports/process`
- **功能**: 手动触发指定股票和年份的PDF文件处理
- **用途**: 重新处理已下载的PDF文件

### 3. 财务报告查询
- **接口**: `GET /api/financial-reports/query`
- **功能**: 多条件查询财务报告，支持分页
- **条件**: 股票代码、公司名称、报告类型、年份范围等

### 4. 股票报告查询
- **接口**: `GET /api/financial-reports/stock/{stockCode}`
- **功能**: 获取指定股票的所有财务报告
- **特点**: 简化版查询接口

### 5. 系统统计
- **接口**: `GET /api/financial-reports/stats`
- **功能**: 获取系统统计信息（报告总数、热门股票等）

### 6. 健康检查
- **接口**: `GET /api/financial-reports/health`
- **功能**: 检查系统各组件的运行状态

## 系统架构

```
前端应用 (Vue.js)
    ↓
Java后端服务 (Spring Boot) - 端口: 8080
    ↓
Python数据处理服务 (FastAPI) - 端口: 8001
    ↓
MySQL数据库
```

### 架构特点

1. **微服务架构**: Java后端作为业务逻辑层，Python服务专注于数据处理
2. **异步处理**: PDF爬取和处理采用异步方式，提高用户体验
3. **统一响应**: 所有API接口返回统一格式的响应结果
4. **完善的错误处理**: 全局异常处理，提供友好的错误信息
5. **API文档**: 集成Swagger，提供完整的API文档

## 环境要求

- **Java**: 17或更高版本
- **Maven**: 3.6或更高版本
- **Python服务**: 需要先启动Python FastAPI服务（端口8001）

## 快速启动

### 1. 环境检查
确保已安装Java 17和Maven，并且Python FastAPI服务正在运行。

### 2. 启动服务
```bash
# 方式1：使用启动脚本（Windows）
start.bat

# 方式2：使用Maven命令
mvn spring-boot:run

# 方式3：编译后运行
mvn clean package
java -jar target/financial-report-backend-1.0.0.jar
```

### 3. 访问服务
- **API基础地址**: http://localhost:8080/api
- **API文档**: http://localhost:8080/api/swagger-ui.html
- **健康检查**: http://localhost:8080/api/financial-reports/health

## 配置说明

### application.yml 主要配置

```yaml
server:
  port: 8080                    # 服务端口
  servlet:
    context-path: /api          # API路径前缀

python-service:
  base-url: http://localhost:8001  # Python服务地址
  timeout: 30000                   # 请求超时时间

spring:
  web:
    cors:
      allowed-origins:          # 允许的跨域源
        - "http://localhost:5173"
        - "http://127.0.0.1:5173"
```

## API接口示例

### 爬取财务报告
```bash
curl -X POST "http://localhost:8080/api/financial-reports/crawl" \
  -H "Content-Type: application/json" \
  -d '{
    "stockCode": "000001",
    "year": 2023,
    "reportType": "annual"
  }'
```

### 查询财务报告
```bash
curl -X GET "http://localhost:8080/api/financial-reports/query?stockCode=000001&page=1&size=10"
```

### 获取统计信息
```bash
curl -X GET "http://localhost:8080/api/financial-reports/stats"
```

## 开发说明

### 添加新接口
1. 在 `FinancialReportController` 中添加新的接口方法
2. 在 `FinancialReportService` 中实现业务逻辑
3. 如需调用Python服务，在 `PythonServiceClient` 中添加相应方法

### 数据传输对象
- 请求DTO：用于接收前端请求参数，包含校验注解
- 响应DTO：用于返回数据给前端，包含JSON序列化配置

### 异常处理
所有异常都会被 `GlobalExceptionHandler` 捕获并返回统一格式的错误响应。

## 注意事项

1. **依赖服务**: 确保Python FastAPI服务正常运行
2. **端口冲突**: 默认使用8080端口，如有冲突请修改配置
3. **跨域配置**: 已配置常用的前端开发端口，如需其他端口请修改CORS配置
4. **日志级别**: 开发环境建议使用DEBUG级别，生产环境使用INFO级别

## 故障排除

### 常见问题

1. **启动失败**: 检查Java版本和Maven配置
2. **连接Python服务失败**: 确认Python服务地址和端口
3. **跨域问题**: 检查CORS配置中的允许源地址
4. **API调用失败**: 查看日志文件，检查参数格式和服务状态

### 日志查看
应用日志会输出到控制台，包含详细的请求和错误信息。

## 联系方式

如有问题或建议，请联系：
- 邮箱: architect@tonghuashun.com
- 项目地址: https://www.tonghuashun.com