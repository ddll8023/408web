package com.web408;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

/**
 * Spring Boot 启动类
 * 408知识点阅读网站后端应用
 * 
 * 技术栈：
 * - Spring Boot 3.2.5
 * - Spring Security 6
 * - MyBatis 3.0.3
 * - MySQL 8.0.33
 * - JWT (jjwt 0.12.5)
 */
@SpringBootApplication
public class Web408Application {

    public static void main(String[] args) {
        SpringApplication.run(Web408Application.class, args);
        System.out.println("========================================");
        System.out.println("408知识点阅读网站后端启动成功！");
        System.out.println("API地址: http://localhost:8081");
        System.out.println("========================================");
    }
}

