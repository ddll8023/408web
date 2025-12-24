package com.web408.pojo.dto;

import io.swagger.v3.oas.annotations.media.Schema;
import jakarta.validation.constraints.Email;
import jakarta.validation.constraints.NotBlank;
import jakarta.validation.constraints.Size;
import lombok.Data;

/**
 * 用户注册请求DTO
 * 
 * Source: springdoc-openapi 官方文档
 */
@Schema(name = "用户注册请求", description = "用户注册请求")
@Data
public class RegisterDTO {
    /**
     * 用户名（必填，3-50字符）
     */
    @Schema(description = "用户名", example = "testuser", required = true, minLength = 3, maxLength = 50)
    @NotBlank(message = "用户名不能为空")
    @Size(min = 3, max = 50, message = "用户名长度必须在3-50字符之间")
    private String username;

    /**
     * 密码（必填，6-20字符）
     */
    @Schema(description = "密码", example = "123456", required = true, minLength = 6, maxLength = 20)
    @NotBlank(message = "密码不能为空")
    @Size(min = 6, max = 20, message = "密码长度必须在6-20字符之间")
    private String password;

    /**
     * 邮箱（可选，需符合邮箱格式）
     */
    @Schema(description = "邮箱地址", example = "test@example.com", required = false)
    @Email(message = "邮箱格式不正确")
    private String email;
}

