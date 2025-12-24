package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * 认证响应视图对象
 * 用途：返回给前端的认证信息（包含JWT Token）
 * 遵循YAGNI原则：只包含前端需要的字段
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
@Schema(name = "AuthVO", description = "认证响应视图对象")
public class AuthVO {
    /**
     * JWT Token
     */
    @Schema(description = "JWT Token", example = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...")
    private String token;

    /**
     * 用户名
     */
    @Schema(description = "用户名", example = "admin")
    private String username;

    /**
     * 用户角色
     */
    @Schema(description = "用户角色", example = "ADMIN")
    private String role;
}
