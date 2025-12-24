package com.web408.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.servlet.config.annotation.ResourceHandlerRegistry;
import org.springframework.web.servlet.config.annotation.WebMvcConfigurer;

import java.nio.file.Paths;

/**
 * Web MVC 配置类
 * 配置静态资源映射，使上传的图片可以通过HTTP访问
 * 遵循KISS原则：简单的静态资源配置
 * 
 * Source: Spring MVC 官方文档
 */
@Configuration
public class WebMvcConfig implements WebMvcConfigurer {

    /**
     * 上传文件存储路径
     */
    @Value("${file.upload.path:uploads/images/}")
    private String uploadPath;

    /**
     * 配置静态资源处理器
     * 将 /uploads/** 的请求映射到本地文件系统
     * 
     * @param registry 资源处理器注册表
     */
    @Override
    public void addResourceHandlers(ResourceHandlerRegistry registry) {
        // 获取项目根目录
        String projectRoot = System.getProperty("user.dir");
        // 拼接uploads目录的绝对路径
        String uploadsPath = Paths.get(projectRoot, "uploads").toAbsolutePath().toString();
        
        // 配置静态资源映射
        // 访问路径：/uploads/images/xxx.png
        // 实际路径：file:///项目根目录/uploads/images/xxx.png
        registry.addResourceHandler("/uploads/**")
                .addResourceLocations("file:///" + uploadsPath.replace("\\", "/") + "/");
    }
}
