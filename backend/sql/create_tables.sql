-- 408真题网站 - 数据库表结构创建脚本
-- 字符集: utf8mb4
-- 存储引擎: InnoDB
-- 说明：本文件仅包含表结构定义，不含数据初始化
-- 遵循SOLID原则：表结构清晰、职责明确

-- ====================================
-- 创建数据库
-- ====================================
# CREATE DATABASE IF NOT EXISTS web408 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE web408;

-- ====================================
-- 1. 用户表 (user)
-- ====================================
CREATE TABLE IF NOT EXISTS `user` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名',
    `password` VARCHAR(255) NOT NULL COMMENT 'BCrypt加密密码',
    `email` VARCHAR(100) DEFAULT NULL COMMENT '邮箱',
    `role` ENUM('ADMIN', 'USER', 'GUEST') NOT NULL DEFAULT 'GUEST' COMMENT '角色',
    `enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '账户启用状态',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_role` (`role`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户表';

-- ====================================
-- 2. 科目表 (subject)
-- ====================================
CREATE TABLE IF NOT EXISTS `subject` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `name` VARCHAR(100) NOT NULL COMMENT '科目名称（如：数据结构、操作系统等）',
    `code` VARCHAR(50) NOT NULL COMMENT '科目编码（用于URL参数，如：data-structure）',
    `description` TEXT DEFAULT NULL COMMENT '科目描述（Markdown格式）',
    `order_num` INT NOT NULL DEFAULT 0 COMMENT '排序序号（升序）',
    `enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_name` (`name`),
    UNIQUE KEY `uk_code` (`code`),
    INDEX `idx_order` (`order_num`),
    INDEX `idx_enabled` (`enabled`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='科目表';

-- ====================================
-- 3. 章节表 (chapter)
-- ====================================
CREATE TABLE IF NOT EXISTS `chapter` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `subject_id` BIGINT NOT NULL COMMENT '所属科目ID',
    `parent_id` BIGINT NULL COMMENT '父章节ID（NULL表示顶级章节）',
    `name` VARCHAR(200) NOT NULL COMMENT '章节名称',
    `order_num` INT NOT NULL DEFAULT 0 COMMENT '排序序号（升序）',
    `enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    INDEX `idx_subject` (`subject_id`),
    INDEX `idx_parent` (`parent_id`),
    INDEX `idx_order` (`order_num`),
    INDEX `idx_enabled` (`enabled`),
    FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`parent_id`) REFERENCES `chapter`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='章节表（支持两级结构）';

-- ====================================
-- 4. 真题表 (exam_question)
-- ====================================
CREATE TABLE IF NOT EXISTS `exam_question` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `year` INT NOT NULL COMMENT '年份',
    `question_number` INT DEFAULT NULL COMMENT '题号',
    `question_type` ENUM('CHOICE', 'ESSAY') NOT NULL DEFAULT 'ESSAY' COMMENT '题型：CHOICE=选择题，ESSAY=主观题',
    `title` VARCHAR(200) DEFAULT NULL COMMENT '题目标题',
    `content` TEXT NOT NULL COMMENT 'Markdown格式题目内容（选择题为题干，主观题为完整题目）',
    `options` TEXT DEFAULT NULL COMMENT '选择题选项（JSON格式，如：{"A":"选项A","B":"选项B","C":"选项C","D":"选项D"}）',
    `answer` TEXT DEFAULT NULL COMMENT '答案（选择题为正确选项如"A"或"AB"，主观题为Markdown格式答案解析）',
    `category` JSON DEFAULT NULL COMMENT '分类（JSON数组，如：["数据结构", "操作系统"]）',
    `subject_id` BIGINT DEFAULT NULL COMMENT '所属科目ID',
    `difficulty` ENUM('EASY', 'MEDIUM', 'HARD') DEFAULT NULL COMMENT '难度',
    `author_id` BIGINT NOT NULL COMMENT '作者ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_year` (`year`),
    INDEX `idx_exam_subject` (`subject_id`),
    INDEX `idx_question_type` (`question_type`),
    UNIQUE INDEX `idx_year_question_unique` (`year`, `question_number`) COMMENT '同一年份题号唯一（NULL题号不受限制）',
    FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`author_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='真题表（支持选择题和主观题）';

-- ====================================
-- 6. 资源文件表 (resource_file)
-- ====================================
CREATE TABLE IF NOT EXISTS `resource_file` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `filename` VARCHAR(200) NOT NULL COMMENT '存储文件名',
    `original_filename` VARCHAR(200) NOT NULL COMMENT '原始文件名',
    `file_path` VARCHAR(500) NOT NULL COMMENT '文件存储路径',
    `file_size` BIGINT DEFAULT NULL COMMENT '文件大小（字节）',
    `file_type` VARCHAR(50) DEFAULT NULL COMMENT '文件类型',
    `description` TEXT DEFAULT NULL COMMENT '资源描述',
    `download_count` INT NOT NULL DEFAULT 0 COMMENT '下载次数',
    `uploader_id` BIGINT NOT NULL COMMENT '上传者ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_uploader` (`uploader_id`),
    FOREIGN KEY (`uploader_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='资源文件表';

-- ====================================
-- 7. 分类标签表 (exam_category)
-- ====================================
-- 说明：分类标签按科目管理，支持两级分类结构（顶级分类→子分类）
CREATE TABLE IF NOT EXISTS `exam_category` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `subject_id` BIGINT NOT NULL COMMENT '所属科目ID',
    `parent_id` BIGINT DEFAULT NULL COMMENT '父分类ID（NULL表示顶级分类）',
    `name` VARCHAR(50) NOT NULL COMMENT '分类名称（如：栈和队列、进程管理等）',
    `code` VARCHAR(50) NOT NULL COMMENT '分类编码（如：stack-queue、process等）',
    `description` VARCHAR(255) DEFAULT NULL COMMENT '分类描述（可选）',
    `order_num` INT NOT NULL DEFAULT 0 COMMENT '排序序号（升序）',
    `enabled` BOOLEAN NOT NULL DEFAULT TRUE COMMENT '是否启用',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_exam_category_subject_name` (`subject_id`, `name`),
    UNIQUE KEY `uk_exam_category_subject_code` (`subject_id`, `code`),
    INDEX `idx_exam_category_subject` (`subject_id`),
    INDEX `idx_exam_category_parent` (`parent_id`),
    INDEX `idx_exam_category_order` (`order_num`),
    INDEX `idx_exam_category_enabled` (`enabled`),
    FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`parent_id`) REFERENCES `exam_category`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='分类标签表（支持两级分类结构）';

-- ====================================
-- 8. 随机出题统计表 (exam_random_stat)
-- ====================================
CREATE TABLE IF NOT EXISTS `exam_random_stat` (
    `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '主键ID',
    `user_id` BIGINT NOT NULL COMMENT '用户ID',
    `total_attempts` INT NOT NULL DEFAULT 0 COMMENT '完成随机出题的总次数',
    `last_attempt_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '最近一次完成时间',
    PRIMARY KEY (`id`),
    UNIQUE KEY `uk_exam_random_user` (`user_id`),
    INDEX `idx_exam_random_user` (`user_id`),
    FOREIGN KEY (`user_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='随机出题完成次数统计表';

-- ====================================
-- 9. 模拟题表 (mock_question)
-- ====================================
-- 说明：与真题表独立，用于存储模拟题，以来源机构区分
CREATE TABLE IF NOT EXISTS `mock_question` (
    `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '主键ID',
    `source` VARCHAR(100) NOT NULL COMMENT '来源机构名称（如：王道、天勤等）',
    `question_number` INT DEFAULT NULL COMMENT '题号',
    `question_type` ENUM('CHOICE', 'ESSAY') NOT NULL DEFAULT 'ESSAY' COMMENT '题型：CHOICE=选择题，ESSAY=主观题',
    `title` VARCHAR(200) DEFAULT NULL COMMENT '题目标题（可包含详细信息）',
    `content` TEXT NOT NULL COMMENT 'Markdown格式题目内容',
    `options` TEXT DEFAULT NULL COMMENT '选择题选项（JSON格式），主观题为NULL',
    `answer` TEXT DEFAULT NULL COMMENT '答案（选择题为正确选项，主观题为Markdown解析）',
    `category` JSON DEFAULT NULL COMMENT '分类（支持多个分类，JSON数组）',
    `subject_id` BIGINT DEFAULT NULL COMMENT '科目ID',
    `difficulty` ENUM('EASY', 'MEDIUM', 'HARD') DEFAULT NULL COMMENT '难度',
    `author_id` BIGINT NOT NULL COMMENT '作者ID',
    `create_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    `update_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    INDEX `idx_mock_source` (`source`),
    INDEX `idx_mock_subject_id` (`subject_id`),
    INDEX `idx_mock_question_type` (`question_type`),
    INDEX `idx_mock_difficulty` (`difficulty`),
    FOREIGN KEY (`subject_id`) REFERENCES `subject`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`author_id`) REFERENCES `user`(`id`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='模拟题表';


-- ====================================
-- 索引说明
-- ====================================
-- user表: username唯一索引（登录查询），role索引（权限筛选）
-- subject表: name和code唯一索引，order_num和enabled索引（排序和筛选）
-- chapter表: subject_id索引（按科目查询），parent_id索引（树形结构），order_num索引（排序）
-- exam_question表: year索引（年份筛选），category索引（分类筛选）
-- mock_question表: source索引（来源筛选），subject_id索引（科目筛选）
-- resource_file表: uploader_id索引（上传者查询）
-- exam_category表: name和code唯一索引（分类唯一约束），order_num和enabled索引（排序和筛选）

-- ====================================
-- 外键约束说明
-- ====================================
-- 1. chapter.subject_id -> subject.id (ON DELETE CASCADE)
-- 2. chapter.parent_id -> chapter.id (ON DELETE CASCADE)
-- 3. exam_question.author_id -> user.id (ON DELETE CASCADE)
-- 4. mock_question.author_id -> user.id (ON DELETE CASCADE)
-- 5. mock_question.subject_id -> subject.id (ON DELETE SET NULL)
-- 6. resource_file.uploader_id -> user.id (ON DELETE CASCADE)
