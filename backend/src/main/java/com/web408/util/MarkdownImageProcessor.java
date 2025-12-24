package com.web408.util;

import org.springframework.stereotype.Component;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Markdown图片处理工具类
 * 用于将Markdown中的图片链接转换为base64嵌入
 * 遵循KISS原则：简单直接的图片处理逻辑
 */
@Component
public class MarkdownImageProcessor {

    // Markdown图片语法正则：![alt](url)
    private static final Pattern IMAGE_PATTERN = Pattern.compile("!\\[([^\\]]*)\\]\\(([^)]+)\\)");

    /**
     * 处理Markdown内容，将图片链接转换为base64
     * 
     * @param markdown Markdown内容
     * @return 处理后的Markdown（图片已转为base64）
     */
    public String processImages(String markdown) {
        if (markdown == null || markdown.isEmpty()) {
            return markdown;
        }

        Matcher matcher = IMAGE_PATTERN.matcher(markdown);
        StringBuffer result = new StringBuffer();

        while (matcher.find()) {
            String alt = matcher.group(1);
            String url = matcher.group(2);
            
            // 尝试转换图片为base64
            String base64Image = convertToBase64(url);
            
            if (base64Image != null) {
                // 替换为base64数据URI
                String replacement = String.format("![%s](%s)", alt, base64Image);
                matcher.appendReplacement(result, Matcher.quoteReplacement(replacement));
            } else {
                // 转换失败，保留原链接
                matcher.appendReplacement(result, Matcher.quoteReplacement(matcher.group(0)));
            }
        }
        matcher.appendTail(result);

        return result.toString();
    }

    /**
     * 将图片URL转换为base64数据URI
     * 
     * @param url 图片URL（可以是相对路径或绝对路径）
     * @return base64数据URI，失败返回null
     */
    private String convertToBase64(String url) {
        try {
            // 判断是否为本地文件路径
            Path imagePath = resolveImagePath(url);
            
            if (imagePath == null || !Files.exists(imagePath)) {
                return null;
            }

            // 读取图片文件
            byte[] imageBytes = Files.readAllBytes(imagePath);
            
            // 转换为base64
            String base64 = Base64.getEncoder().encodeToString(imageBytes);
            
            // 根据文件扩展名确定MIME类型
            String mimeType = getMimeType(imagePath.toString());
            
            // 返回data URI
            return String.format("data:%s;base64,%s", mimeType, base64);
            
        } catch (IOException e) {
            // 转换失败，返回null
            System.err.println("图片转换失败: " + url + " - " + e.getMessage());
            return null;
        }
    }

    /**
     * 解析图片路径
     * 支持：
     * 1. HTTP/HTTPS URL：http://localhost:8081/uploads/xxx.png
     * 2. 相对路径：/uploads/xxx.png
     * 3. 绝对路径：C:/path/to/image.png
     * 
     * @param url 图片URL
     * @return 图片文件路径
     */
    private Path resolveImagePath(String url) {
        if (url == null || url.isEmpty()) {
            return null;
        }

        // 处理 HTTP/HTTPS URL：提取路径部分
        if (url.startsWith("http://") || url.startsWith("https://")) {
            try {
                // 找到协议后的第一个路径分隔符
                int pathStart = url.indexOf('/', url.indexOf("://") + 3);
                if (pathStart > 0) {
                    url = url.substring(pathStart); // 提取路径部分
                } else {
                    return null; // 无效 URL
                }
            } catch (Exception e) {
                return null;
            }
        }

        // 移除可能的查询参数
        int queryIndex = url.indexOf('?');
        if (queryIndex > 0) {
            url = url.substring(0, queryIndex);
        }

        // 如果是相对路径（以/开头）
        if (url.startsWith("/")) {
            // 移除开头的/
            url = url.substring(1);
        }

        // 尝试解析为绝对路径
        Path path = Paths.get(url);
        if (path.isAbsolute() && Files.exists(path)) {
            return path;
        }

        // 尝试从项目根目录的uploads文件夹查找
        path = Paths.get(url);
        if (Files.exists(path)) {
            return path;
        }

        return null;
    }

    /**
     * 根据文件扩展名获取MIME类型
     * 
     * @param fileName 文件名
     * @return MIME类型
     */
    private String getMimeType(String fileName) {
        String extension = "";
        int dotIndex = fileName.lastIndexOf('.');
        if (dotIndex > 0) {
            extension = fileName.substring(dotIndex + 1).toLowerCase();
        }

        return switch (extension) {
            case "png" -> "image/png";
            case "jpg", "jpeg" -> "image/jpeg";
            case "gif" -> "image/gif";
            case "bmp" -> "image/bmp";
            case "webp" -> "image/webp";
            case "svg" -> "image/svg+xml";
            default -> "image/png"; // 默认
        };
    }
}
