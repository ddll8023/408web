package com.web408.util;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.nio.charset.StandardCharsets;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;

/**
 * JWT工具类
 * 用于生成、解析、验证JWT Token
 * 
 * Source: jjwt 0.12.5 官方文档
 */
@Component
public class JwtUtil {

    /**
     * JWT密钥（从配置文件读取）
     */
    @Value("${jwt.secret}")
    private String secret;

    /**
     * 生成JWT Token（永不过期）
     * 
     * @param username 用户名
     * @param role     用户角色
     * @return JWT Token字符串
     */
    public String generateToken(String username, String role) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("username", username);
        claims.put("role", role);

        Date now = new Date();

        return Jwts.builder()
                .claims(claims)
                .subject(username)
                .issuedAt(now)
                // 不设置过期时间，Token永不过期
                .signWith(getSecretKey())
                .compact();
    }

    /**
     * 解析JWT Token
     * 
     * @param token JWT Token字符串
     * @return Claims对象（包含Token中的所有信息）
     */
    public Claims parseToken(String token) {
        try {
            return Jwts.parser()
                    .verifyWith(getSecretKey())
                    .build()
                    .parseSignedClaims(token)
                    .getPayload();
        } catch (Exception e) {
            return null;
        }
    }

    /**
     * 验证JWT Token是否有效（永不过期，只验证签名）
     * 
     * @param token JWT Token字符串
     * @return true-有效，false-无效
     */
    public boolean validateToken(String token) {
        try {
            Claims claims = parseToken(token);
            // Token 永不过期，只要能成功解析就是有效的
            return claims != null;
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * 从Token中获取用户名
     * 
     * @param token JWT Token字符串
     * @return 用户名
     */
    public String getUsernameFromToken(String token) {
        Claims claims = parseToken(token);
        return claims != null ? claims.get("username", String.class) : null;
    }

    /**
     * 从Token中获取用户角色
     * 
     * @param token JWT Token字符串
     * @return 用户角色
     */
    public String getRoleFromToken(String token) {
        Claims claims = parseToken(token);
        return claims != null ? claims.get("role", String.class) : null;
    }

    /**
     * 获取密钥对象
     * 
     * @return SecretKey对象
     */
    private SecretKey getSecretKey() {
        return Keys.hmacShaKeyFor(secret.getBytes(StandardCharsets.UTF_8));
    }
}
