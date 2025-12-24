package com.web408.config;

import com.web408.filter.JwtAuthenticationFilter;
import org.springframework.http.HttpMethod;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;

/**
 * Spring Security配置类
 * 配置JWT认证过滤器和URL访问权限
 * 遵循YAGNI原则：只配置必需的安全功能
 * 
 * Source: Spring Security 6 官方文档
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity(prePostEnabled = true)
public class SecurityConfig {

    @Autowired
    private JwtAuthenticationFilter jwtAuthenticationFilter;

    /**
     * 配置安全过滤器链
     * 
     * @param http HttpSecurity对象
     * @return SecurityFilterChain
     */
    @Bean
    public SecurityFilterChain securityFilterChain(HttpSecurity http) throws Exception {
        http
            // 禁用CSRF（前后端分离架构不需要）
            .csrf(csrf -> csrf.disable())
            
            // 配置Session管理策略（无状态，使用JWT）
            .sessionManagement(session -> 
                session.sessionCreationPolicy(SessionCreationPolicy.STATELESS)
            )
            
            // 配置URL访问权限
            .authorizeHttpRequests(auth -> auth
                // Swagger UI 和 API 文档公开访问
                .requestMatchers("/swagger-ui/**", "/swagger-ui.html", "/v3/api-docs/**", "/swagger-resources/**").permitAll()
                // 公开接口：注册、登录
                .requestMatchers("/api/auth/register", "/api/auth/login").permitAll()
                // 公开接口：上传的静态资源访问
                .requestMatchers("/uploads/**").permitAll()
                // 公开接口：真题浏览（仅GET方法，列表和详情）
                .requestMatchers(HttpMethod.GET, "/api/exam", "/api/exam/*").permitAll()
                // 公开接口：真题分类统计导出（与浏览统计保持一致）
                .requestMatchers(HttpMethod.GET, "/api/exam/category-stats/export").permitAll()
                // 公开接口：科目查询（仅GET方法）
                .requestMatchers(HttpMethod.GET, "/api/subject", "/api/subject/*", "/api/subject/code/*").permitAll()
                // 公开接口：章节查询（仅GET方法）
                // 管理专用：查询科目下所有章节（包含禁用）——仅ADMIN
                .requestMatchers(HttpMethod.GET, "/api/chapter/subject/*/all").hasRole("ADMIN")
                // 公开：启用章节查询、章节详情
                .requestMatchers(HttpMethod.GET, "/api/chapter/*", "/api/chapter/subject/*").permitAll()
                // 其他所有请求需要认证（包括POST方法的管理接口）
                .anyRequest().authenticated()
            )
            
            // 添加JWT过滤器（在UsernamePasswordAuthenticationFilter之前执行）
            .addFilterBefore(jwtAuthenticationFilter, UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }
}

