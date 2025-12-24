package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.NotBlank;
import lombok.Data;

/**
 * 用户登录请求DTO
 * 
 * Source: springdoc-openapi 官方文档
 */
@Schema(name = "用户登录请求", description = "用户登录请求")
@Data
public class LoginDTO {
    /**
     * 用户名（必填）
     */
    @Schema(description = "用户名", example = "admin", required = true)
    @NotBlank(message = "用户名不能为空")
    private String username;

    /**
     * 密码（必填）
     */
    @Schema(description = "密码", example = "123456", required = true)
    @NotBlank(message = "密码不能为空")
    private String password;
}

