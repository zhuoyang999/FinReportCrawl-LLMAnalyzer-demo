@echo off
chcp 65001
echo ========================================
echo 同花顺财务报告系统 - Java后端服务启动脚本
echo ========================================

echo.
echo 正在检查Java环境...
java -version
if %errorlevel% neq 0 (
    echo 错误：未找到Java环境，请确保已安装Java 17或更高版本
    pause
    exit /b 1
)

echo.
echo 正在检查Maven环境...
mvn -version
if %errorlevel% neq 0 (
    echo 错误：未找到Maven环境，请确保已安装Maven
    pause
    exit /b 1
)

echo.
echo 正在编译项目...
mvn clean compile
if %errorlevel% neq 0 (
    echo 错误：项目编译失败
    pause
    exit /b 1
)

echo.
echo 正在启动Java后端服务...
echo 服务地址: http://localhost:8080/api
echo API文档: http://localhost:8080/api/swagger-ui.html
echo.

mvn spring-boot:run

pause