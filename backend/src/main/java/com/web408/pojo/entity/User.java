package com.web408.pojo.entity;

import lombok.Data;
import java.time.LocalDateTime;

/**
 * 用户实体类
 * 对应数据库表: user
 */
@Data
public class User {
    /**
     * 主键ID
     */
    private Long id;

    /**
     * 用户名（唯一）
     */
    private String username;

    /**
     * BCrypt加密密码
     */
    private String password;

    /**
     * 邮箱
     */
    private String email;

    /**
     * 角色: ADMIN/USER/GUEST
     */
    private String role;

    /**
     * 账户启用状态
     */
    private Boolean enabled;

    /**
     * 创建时间
     */
    private LocalDateTime createTime;

    /**
     * 更新时间
     */
    private LocalDateTime updateTime;
}

