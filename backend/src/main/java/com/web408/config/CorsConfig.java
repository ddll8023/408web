package com.web408.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;
import org.springframework.web.filter.CorsFilter;

/**
 * 跨域配置类
 * 允许前端（localhost:5173）跨域访问后端API
 * 遵循KISS原则：简单的CORS配置
 */
@Configuration
public class CorsConfig {

    /**
     * 配置CORS过滤器
     * 
     * @return CorsFilter
     */
    @Bean
    public CorsFilter corsFilter() {
        CorsConfiguration config = new CorsConfiguration();
        
        // 允许的源（前端地址）
        config.addAllowedOrigin("http://localhost:5174");
        config.addAllowedOrigin("http://localhost:5173");
        
        // 允许携带凭证（Cookie等）
        config.setAllowCredentials(true);
        
        // 允许所有请求头
        config.addAllowedHeader("*");
        
        // 允许所有请求方法
        config.addAllowedMethod("*");
        
        // 暴露的响应头
        config.addExposedHeader("Authorization");

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", config);
        
        return new CorsFilter(source);
    }
}

