package com.web408.controller;

import com.web408.pojo.dto.LoginDTO;
import com.web408.pojo.dto.RegisterDTO;
import com.web408.pojo.vo.ApiResult;
import com.web408.pojo.vo.AuthVO;
import com.web408.service.AuthService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.Parameter;
import io.swagger.v3.oas.annotations.responses.ApiResponse;
import io.swagger.v3.oas.annotations.responses.ApiResponses;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.validation.Valid;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

/**
 * 认证控制器
 * 用途：提供用户注册和登录接口
 * 遵循KISS原则：简单清晰的接口设计，无业务逻辑
 * 
 * 职责边界：
 * - ✅ 接收HTTP请求参数
 * - ✅ 调用Service层方法
 * - ✅ 返回统一格式响应
 * - ❌ 禁止包含任何业务逻辑
 * 
 * 接口说明：
 * - POST /api/auth/register：用户注册
 * - POST /api/auth/login：用户登录
 * 
 * Source: springdoc-openapi 官方文档
 */
@Tag(name = "认证管理", description = "提供用户注册和登录功能")
@RestController
@RequestMapping("/api/auth")
public class AuthController {

    @Autowired
    private AuthService authService;

    /**
     * 用户注册接口
     * 权限：公开
     */
    @Operation(summary = "用户注册", description = "新用户注册接口，需要提供用户名、密码等信息")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "注册成功"),
        @ApiResponse(responseCode = "400", description = "请求参数错误或用户名已存在")
    })
    @PostMapping("/register")
    public ResponseEntity<ApiResult<Void>> register(
            @Parameter(description = "注册请求信息", required = true)
            @Valid @RequestBody RegisterDTO request) {
        // 依赖全局异常处理，移除冗余try-catch
        authService.register(request);
        return ResponseEntity.ok(ApiResult.success(null, "注册成功"));
    }

    /**
     * 用户登录接口
     * 权限：公开
     */
    @Operation(summary = "用户登录", description = "用户登录接口，成功返回JWT Token和用户信息")
    @ApiResponses(value = {
        @ApiResponse(responseCode = "200", description = "登录成功，返回Token和用户信息"),
        @ApiResponse(responseCode = "401", description = "用户名或密码错误")
    })
    @PostMapping("/login")
    public ResponseEntity<ApiResult<AuthVO>> login(
            @Parameter(description = "登录请求信息（用户名和密码）", required = true)
            @Valid @RequestBody LoginDTO request) {
        // 依赖全局异常处理，移除冗余try-catch
        AuthVO authVO = authService.login(request);
        return ResponseEntity.ok(ApiResult.success(authVO, "登录成功"));
    }
}
