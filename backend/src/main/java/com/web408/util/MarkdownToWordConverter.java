package com.web408.util;

import org.apache.poi.util.Units;
import org.apache.poi.xwpf.usermodel.*;
import org.openxmlformats.schemas.wordprocessingml.x2006.main.*;

import java.io.ByteArrayInputStream;
import java.util.Base64;
import java.util.regex.Matcher;
import java.util.regex.Pattern;

/**
 * Markdown 转 Word 转换器
 * 遵循 SOLID 原则：单一职责 - 专注于 Markdown 到 Word 的转换
 * 遵循 KISS 原则：使用正则表达式进行简单解析，避免复杂的 AST 树
 */
public class MarkdownToWordConverter {

    // Markdown 图片正则：![alt](data:image/xxx;base64,...)
    private static final Pattern IMAGE_PATTERN = Pattern.compile("!\\[([^\\]]*)\\]\\(([^)]+)\\)");
    
    // Base64 图片 data URI 正则
    private static final Pattern BASE64_PATTERN = Pattern.compile("data:image/(\\w+);base64,(.+)");
    
    // Markdown 标题正则：# 标题
    private static final Pattern HEADING_PATTERN = Pattern.compile("^(#{1,6})\\s+(.+)$", Pattern.MULTILINE);
    
    // Markdown 加粗：**text**
    private static final Pattern BOLD_PATTERN = Pattern.compile("\\*\\*(.+?)\\*\\*");
    
    // Markdown 斜体：*text*（不匹配加粗）
    private static final Pattern ITALIC_PATTERN = Pattern.compile("(?<!\\*)\\*(?!\\*)(.+?)\\*(?!\\*)");
    
    // Markdown 行内代码：`code`
    private static final Pattern INLINE_CODE_PATTERN = Pattern.compile("`([^`]+)`");

    /**
     * 将 Markdown 文本转换为 Word 段落
     * 
     * @param document Word 文档对象
     * @param markdown Markdown 文本
     */
    public void convertMarkdownToWord(XWPFDocument document, String markdown) {
        if (markdown == null || markdown.isEmpty()) {
            return;
        }

        // 将转义的 \n 替换为实际换行符
        markdown = markdown.replace("\\n", "\n");

        // 按行处理 Markdown
        String[] lines = markdown.split("\n");
        StringBuilder paragraph = new StringBuilder();
        boolean inCodeBlock = false;

        for (String line : lines) {
            // 检测代码块标记
            if (line.trim().startsWith("```")) {
                if (inCodeBlock) {
                    // 代码块结束
                    if (paragraph.length() > 0) {
                        addCodeBlockParagraph(document, paragraph.toString());
                        paragraph = new StringBuilder();
                    }
                    inCodeBlock = false;
                } else {
                    // 代码块开始
                    if (paragraph.length() > 0) {
                        addFormattedParagraph(document, paragraph.toString());
                        paragraph = new StringBuilder();
                    }
                    inCodeBlock = true;
                }
                continue;
            }

            // 代码块内容
            if (inCodeBlock) {
                paragraph.append(line).append("\n");
                continue;
            }

            // 检测标题
            Matcher headingMatcher = HEADING_PATTERN.matcher(line);
            if (headingMatcher.matches()) {
                // 先输出之前累积的段落
                if (paragraph.length() > 0) {
                    addFormattedParagraph(document, paragraph.toString());
                    paragraph = new StringBuilder();
                }
                
                int level = headingMatcher.group(1).length();
                String text = headingMatcher.group(2);
                addHeadingParagraph(document, text, level);
                continue;
            }

            // 空行 - 段落分隔
            if (line.trim().isEmpty()) {
                if (paragraph.length() > 0) {
                    addFormattedParagraph(document, paragraph.toString());
                    paragraph = new StringBuilder();
                }
                continue;
            }

            // 累积普通行
            if (paragraph.length() > 0) {
                paragraph.append("\n");
            }
            paragraph.append(line);
        }

        // 输出最后的段落
        if (paragraph.length() > 0) {
            if (inCodeBlock) {
                addCodeBlockParagraph(document, paragraph.toString());
            } else {
                addFormattedParagraph(document, paragraph.toString());
            }
        }
    }

    /**
     * 添加标题段落
     */
    private void addHeadingParagraph(XWPFDocument document, String text, int level) {
        XWPFParagraph para = document.createParagraph();
        XWPFRun run = para.createRun();
        
        // 根据标题级别设置字号
        int fontSize = switch (level) {
            case 1 -> 24;
            case 2 -> 20;
            case 3 -> 18;
            case 4 -> 16;
            default -> 14;
        };
        
        run.setText(text);
        run.setBold(true);
        run.setFontSize(fontSize);
        run.setFontFamily("微软雅黑");
    }

    /**
     * 添加代码块段落
     */
    private void addCodeBlockParagraph(XWPFDocument document, String code) {
        XWPFParagraph para = document.createParagraph();
        para.setStyle("Code");
        
        XWPFRun run = para.createRun();
        run.setText(code.trim());
        run.setFontFamily("Consolas");
        run.setFontSize(10);
        
        // 设置背景色（灰色）
        CTShd shd = run.getCTR().addNewRPr().addNewShd();
        shd.setFill("F5F5F5");
    }

    /**
     * 添加带格式的段落（处理加粗、斜体、图片等）
     */
    private void addFormattedParagraph(XWPFDocument document, String text) {
        XWPFParagraph para = document.createParagraph();
        processInlineFormats(para, text);
    }

    /**
     * 处理行内格式（加粗、斜体、图片、行内代码）
     */
    private void processInlineFormats(XWPFParagraph para, String text) {
        // 先处理图片（独立段落）
        Matcher imageMatcher = IMAGE_PATTERN.matcher(text);
        if (imageMatcher.find()) {
            String imageUrl = imageMatcher.group(2);
            
            // 添加图片前的文本
            String beforeImage = text.substring(0, imageMatcher.start());
            if (!beforeImage.trim().isEmpty()) {
                addStyledText(para, beforeImage);
            }
            
            // 插入图片
            insertBase64Image(para, imageUrl);
            
            // 处理图片后的文本
            String afterImage = text.substring(imageMatcher.end());
            if (!afterImage.trim().isEmpty()) {
                processInlineFormats(para, afterImage);
            }
            return;
        }

        // 处理行内代码
        text = processInlineCode(para, text);
        
        // 处理加粗和斜体
        addStyledText(para, text);
    }

    /**
     * 处理行内代码
     */
    private String processInlineCode(XWPFParagraph para, String text) {
        Matcher codeMatcher = INLINE_CODE_PATTERN.matcher(text);
        if (codeMatcher.find()) {
            // 添加代码前的文本
            String before = text.substring(0, codeMatcher.start());
            if (!before.isEmpty()) {
                addStyledText(para, before);
            }
            
            // 添加代码
            XWPFRun codeRun = para.createRun();
            codeRun.setText(codeMatcher.group(1));
            codeRun.setFontFamily("Consolas");
            CTShd shd = codeRun.getCTR().addNewRPr().addNewShd();
            shd.setFill("F5F5F5");
            
            // 递归处理剩余文本
            String after = text.substring(codeMatcher.end());
            if (!after.isEmpty()) {
                return processInlineCode(para, after);
            }
            return "";
        }
        return text;
    }

    /**
     * 添加带样式的文本（加粗、斜体）
     */
    private void addStyledText(XWPFParagraph para, String text) {
        if (text == null || text.isEmpty()) {
            return;
        }

        // 处理加粗
        Matcher boldMatcher = BOLD_PATTERN.matcher(text);
        if (boldMatcher.find()) {
            // 添加加粗前的文本
            String before = text.substring(0, boldMatcher.start());
            if (!before.isEmpty()) {
                addStyledText(para, before);
            }
            
            // 添加加粗文本
            XWPFRun run = para.createRun();
            run.setText(boldMatcher.group(1));
            run.setBold(true);
            
            // 递归处理剩余文本
            String after = text.substring(boldMatcher.end());
            if (!after.isEmpty()) {
                addStyledText(para, after);
            }
            return;
        }

        // 处理斜体
        Matcher italicMatcher = ITALIC_PATTERN.matcher(text);
        if (italicMatcher.find()) {
            // 添加斜体前的文本
            String before = text.substring(0, italicMatcher.start());
            if (!before.isEmpty()) {
                addStyledText(para, before);
            }
            
            // 添加斜体文本
            XWPFRun run = para.createRun();
            run.setText(italicMatcher.group(1));
            run.setItalic(true);
            
            // 递归处理剩余文本
            String after = text.substring(italicMatcher.end());
            if (!after.isEmpty()) {
                addStyledText(para, after);
            }
            return;
        }

        // 无特殊格式，直接添加
        if (!text.trim().isEmpty()) {
            XWPFRun run = para.createRun();
            run.setText(text);
            run.setFontFamily("微软雅黑");
        }
    }

    /**
     * 插入 base64 编码的图片
     */
    private void insertBase64Image(XWPFParagraph para, String dataUri) {
        try {
            // 解析 data URI
            Matcher matcher = BASE64_PATTERN.matcher(dataUri);
            if (!matcher.matches()) {
                // 不是 base64 图片，跳过
                return;
            }

            String imageType = matcher.group(1); // png, jpeg, etc.
            String base64Data = matcher.group(2);

            // 解码 base64
            byte[] imageBytes = Base64.getDecoder().decode(base64Data);

            // 确定图片格式
            int format = switch (imageType.toLowerCase()) {
                case "png" -> XWPFDocument.PICTURE_TYPE_PNG;
                case "jpg", "jpeg" -> XWPFDocument.PICTURE_TYPE_JPEG;
                case "gif" -> XWPFDocument.PICTURE_TYPE_GIF;
                case "bmp" -> XWPFDocument.PICTURE_TYPE_BMP;
                default -> XWPFDocument.PICTURE_TYPE_PNG;
            };

            // 插入图片
            XWPFRun run = para.createRun();
            ByteArrayInputStream bis = new ByteArrayInputStream(imageBytes);
            
            // 设置图片尺寸（宽度 400px，高度自适应）
            run.addPicture(bis, format, "image." + imageType, Units.toEMU(400), Units.toEMU(300));
            
            bis.close();

        } catch (Exception e) {
            // 图片插入失败，添加错误提示
            XWPFRun run = para.createRun();
            run.setText("[图片加载失败]");
            run.setColor("FF0000");
            System.err.println("插入图片失败: " + e.getMessage());
        }
    }
}
