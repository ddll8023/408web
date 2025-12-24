package com.web408.mapper;

import com.web408.pojo.entity.User;
import org.apache.ibatis.annotations.Mapper;
import org.apache.ibatis.annotations.Param;

/**
 * 用户Mapper接口
 */
@Mapper
public interface UserMapper {
    
    /**
     * 根据用户名查询用户
     * 
     * @param username 用户名
     * @return User对象，不存在返回null
     */
    User findByUsername(@Param("username") String username);

    /**
     * 插入新用户
     * 
     * @param user 用户对象
     * @return 影响行数
     */
    int insert(User user);

    /**
     * 根据ID查询用户
     * 
     * @param id 用户ID
     * @return User对象，不存在返回null
     */
    User findById(@Param("id") Long id);

    /**
     * 更新用户角色
     * 
     * @param id 用户ID
     * @param role 新角色
     * @return 影响行数
     */
    int updateRole(@Param("id") Long id, @Param("role") String role);

    /**
     * 更新用户启用状态
     * 
     * @param id 用户ID
     * @param enabled 启用状态
     * @return 影响行数
     */
    int updateEnabled(@Param("id") Long id, @Param("enabled") Boolean enabled);
}

