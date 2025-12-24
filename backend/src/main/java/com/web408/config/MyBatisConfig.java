package com.web408.config;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.context.annotation.Configuration;

/**
 * MyBatis配置类
 * 扫描Mapper接口包路径
 */
@Configuration
@MapperScan("com.web408.mapper")
public class MyBatisConfig {
    // MyBatis自动扫描配置
    // 其他配置项在application.yml和mybatis-config.xml中
}

