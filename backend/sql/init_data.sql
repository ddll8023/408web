-- 408真题网站 - 初始化数据脚本
-- 说明：本文件仅包含初始化数据，需要先执行create_tables.sql创建表结构
-- 遵循KISS原则：数据初始化清晰、逻辑简单

USE web408;

-- ====================================
-- 1. 初始化管理员账户
-- ====================================
-- 密码: admin123 (BCrypt加密后的密文)
INSERT INTO `user` (`username`, `password`, `email`, `role`, `enabled`) 
VALUES ('admin', '$2a$10$imDojW00LaQg5wwkbRiMweZe/MXfflophDLIyocrmekKANWgJtwHe', 'admin@web408.com', 'ADMIN', TRUE);

-- ====================================
-- 2. 插入初始科目数据
-- ====================================
INSERT INTO `subject` (`name`, `code`, `description`, `order_num`, `enabled`) VALUES
('数据结构', 'data-structure', '数据结构是计算机存储、组织数据的方式，研究数据元素之间的逻辑关系和物理存储结构。主要内容包括：线性表、栈、队列、树、图、查找和排序算法等。是计算机科学的核心基础课程，对于算法设计和程序优化具有重要意义。', 1, TRUE),
('操作系统', 'operating-system', '操作系统是管理计算机硬件与软件资源的系统软件，为用户提供使用计算机的接口。主要内容包括：进程管理、内存管理、文件系统、设备管理、并发控制等。理解操作系统原理对于系统编程和性能优化至关重要。', 2, TRUE),
('计算机网络', 'computer-network', '计算机网络研究计算机系统之间的互联和通信技术。主要内容包括：网络体系结构、TCP/IP协议栈、数据链路层、网络层、传输层、应用层协议等。是互联网时代程序员必备的知识领域。', 3, TRUE),
('计算机组成原理', 'computer-organization', '计算机组成原理研究计算机系统的组成、结构和工作原理。主要内容包括：数据表示、运算器、存储器、指令系统、CPU结构、总线系统、输入输出系统等。是理解计算机硬件工作机制的基础课程。', 4, TRUE);


-- ====================================
-- 3. 插入数据结构的章节数据
-- ====================================
-- 获取数据结构的科目ID（使用变量）
SET @subject_id = (SELECT id FROM subject WHERE code = 'data-structure');

-- 插入顶级章节（父章节）
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, NULL, '绪论', 1, TRUE),
(@subject_id, NULL, '线性表', 2, TRUE),
(@subject_id, NULL, '线性数据结构', 3, TRUE),
(@subject_id, NULL, '字符串', 4, TRUE),
(@subject_id, NULL, '树与二叉树', 5, TRUE),
(@subject_id, NULL, '图', 6, TRUE),
(@subject_id, NULL, '查找', 7, TRUE),
(@subject_id, NULL, '排序', 8, TRUE);

-- 插入子章节（绪论）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '绪论' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '数据结构基本概念', 1, TRUE),
(@subject_id, @parent_id, '算法基本概念', 2, TRUE);

-- 插入子章节（线性表）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '线性表' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '线性表的定义', 1, TRUE),
(@subject_id, @parent_id, '顺序表', 2, TRUE),
(@subject_id, @parent_id, '链表', 3, TRUE);

-- 插入子章节（线性数据结构）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '线性数据结构' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '栈', 1, TRUE),
(@subject_id, @parent_id, '队列', 2, TRUE);

-- 插入子章节（字符串）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '字符串' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '字符串的定义', 1, TRUE),
(@subject_id, @parent_id, '字符串的匹配', 2, TRUE);

-- 插入子章节（树与二叉树）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '树与二叉树' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '树的定义', 1, TRUE),
(@subject_id, @parent_id, '二叉树', 2, TRUE),
(@subject_id, @parent_id, '树的遍历', 3, TRUE);

-- 插入子章节（图）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '图' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '图的定义', 1, TRUE),
(@subject_id, @parent_id, '图的遍历', 2, TRUE),
(@subject_id, @parent_id, '最短路径', 3, TRUE);

-- 插入子章节（查找）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '查找' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '顺序查找', 1, TRUE),
(@subject_id, @parent_id, '二分查找', 2, TRUE),
(@subject_id, @parent_id, '哈希查找', 3, TRUE);

-- 插入子章节（排序）
SET @parent_id = (SELECT id FROM chapter WHERE subject_id = @subject_id AND name = '排序' AND parent_id IS NULL);
INSERT INTO `chapter` (`subject_id`, `parent_id`, `name`, `order_num`, `enabled`) VALUES
(@subject_id, @parent_id, '插入排序', 1, TRUE),
(@subject_id, @parent_id, '快速排序', 2, TRUE),
(@subject_id, @parent_id, '归并排序', 3, TRUE);

-- ====================================
-- 完成提示
-- ====================================
-- 注：
-- 1. 其他科目的章节数据可通过管理后台添加
-- 2. 建议按以下顺序执行SQL脚本：
--    第一步：create_tables.sql (创建所有表结构)
--    第二步：init_data.sql (初始化基础数据)

