package com.web408.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import io.swagger.v3.oas.models.info.License;
import io.swagger.v3.oas.models.security.SecurityRequirement;
import io.swagger.v3.oas.models.security.SecurityScheme;
import io.swagger.v3.oas.models.Components;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

/**
 * Swagger/OpenAPI 配置类
 * 提供 API 文档的自动生成和交互式界面
 * 遵循 KISS 原则：简单清晰的配置
 * 
 * Source: springdoc-openapi 官方文档
 */
@Configuration
public class SwaggerConfig {

    /**
     * 配置 OpenAPI 基本信息
     * 包含 API 标题、描述、版本等信息
     * 
     * @return OpenAPI 配置对象
     */
    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
                .info(new Info()
                        .title("408知识点阅读网站 API 文档")
                        .description("提供知识点管理、真题管理、章节管理等功能的 RESTful API")
                        .version("1.0.0")
                        .contact(new Contact()
                                .name("Web408 Team")
                                .email("support@web408.com"))
                        .license(new License()
                                .name("Apache 2.0")
                                .url("https://www.apache.org/licenses/LICENSE-2.0.html")))
                // 添加 JWT 安全方案
                .addSecurityItem(new SecurityRequirement().addList("JWT"))
                .components(new Components()
                        .addSecuritySchemes("JWT", new SecurityScheme()
                                .type(SecurityScheme.Type.HTTP)
                                .scheme("bearer")
                                .bearerFormat("JWT")
                                .description("JWT 认证，格式：Bearer {token}")));
    }
}

