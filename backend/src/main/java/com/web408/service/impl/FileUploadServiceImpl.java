package com.web408.service.impl;

import com.web408.mapper.MockQuestionMapper;
import com.web408.pojo.entity.ExamQuestion;
import com.web408.pojo.entity.MockQuestion;
import com.web408.pojo.vo.ImageResourceVO;
import com.web408.pojo.vo.ImageUsageExamVO;
import com.web408.service.ExamService;
import com.web408.service.FileUploadService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 文件上传服务实现类
 * 遵循KISS原则：简单直接的文件处理逻辑
 * 遵循单一职责原则：只处理文件上传相关业务
 */
@Service
public class FileUploadServiceImpl implements FileUploadService {

    @Autowired
    private ExamService examService;

    // 注入 MockQuestionMapper 用于检查图片引用
    @Autowired
    private MockQuestionMapper mockQuestionMapper;

    @Value("${file.upload.path:uploads/images/}")
    private String uploadPath;

    private static final List<String> ALLOWED_EXTENSIONS = Arrays.asList(
            "jpg", "jpeg", "png", "gif", "webp");

    /**
     * 上传图片
     */
    @Override
    public String uploadImage(MultipartFile file) {
        // 校验文件
        if (file.isEmpty()) {
            throw new RuntimeException("文件不能为空");
        }

        String originalFilename = file.getOriginalFilename();
        if (originalFilename == null || originalFilename.isEmpty()) {
            throw new RuntimeException("文件名无效");
        }

        String extension = getFileExtension(originalFilename);
        if (!ALLOWED_EXTENSIONS.contains(extension.toLowerCase())) {
            throw new RuntimeException("不支持的文件类型");
        }

        try {
            String filename = UUID.randomUUID().toString() + "." + extension;
            String projectRoot = System.getProperty("user.dir");
            Path uploadDir = Paths.get(projectRoot, uploadPath);

            if (!Files.exists(uploadDir)) {
                Files.createDirectories(uploadDir);
            }

            Path filePath = uploadDir.resolve(filename);
            file.transferTo(filePath.toFile());

            return "/" + uploadPath + filename;
        } catch (IOException e) {
            throw new RuntimeException("文件上传失败：" + e.getMessage());
        }
    }

    /**
     * 查询已上传图片列表
     */
    @Override
    public List<ImageResourceVO> listImages(Boolean onlyUnreferenced) {
        try {
            String projectRoot = System.getProperty("user.dir");
            Path uploadDir = Paths.get(projectRoot, uploadPath);

            if (!Files.exists(uploadDir) || !Files.isDirectory(uploadDir)) {
                return Collections.emptyList();
            }

            List<Path> filePaths = Files.list(uploadDir)
                    .filter(Files::isRegularFile)
                    .collect(Collectors.toList());

            List<ImageResourceVO> images = new ArrayList<>();
            for (Path path : filePaths) {
                String filename = path.getFileName().toString();
                String url = "/" + uploadPath + filename;
                long size = 0L;
                long lastModified = 0L;
                try {
                    size = Files.size(path);
                    lastModified = Files.getLastModifiedTime(path).toMillis();
                } catch (IOException ignored) {
                }

                ImageResourceVO vo = new ImageResourceVO();
                vo.setFilename(filename);
                vo.setUrl(url);
                vo.setSize(size);
                vo.setLastModified(lastModified);
                vo.setReferenced(false);
                vo.setExams(new ArrayList<>());
                images.add(vo);
            }

            // 检查图片引用
            checkImageReferences(images);

            // 过滤未引用的图片
            if (Boolean.TRUE.equals(onlyUnreferenced)) {
                images = images.stream()
                        .filter(image -> !image.isReferenced())
                        .collect(Collectors.toList());
            }

            // 按最后修改时间降序排序
            images.sort(Comparator.comparingLong(ImageResourceVO::getLastModified).reversed());
            return images;
        } catch (IOException e) {
            throw new RuntimeException("查询图片列表失败：" + e.getMessage());
        }
    }

    /**
     * 删除未引用的图片
     */
    @Override
    public int cleanupUnreferencedImages() {
        try {
            String projectRoot = System.getProperty("user.dir");
            Path uploadDir = Paths.get(projectRoot, uploadPath);

            if (!Files.exists(uploadDir) || !Files.isDirectory(uploadDir)) {
                return 0;
            }

            List<Path> filePaths = Files.list(uploadDir)
                    .filter(Files::isRegularFile)
                    .collect(Collectors.toList());

            List<ImageResourceVO> images = new ArrayList<>();
            for (Path path : filePaths) {
                ImageResourceVO vo = new ImageResourceVO();
                vo.setFilename(path.getFileName().toString());
                vo.setReferenced(false);
                images.add(vo);
            }

            checkImageReferences(images);

            int deleteCount = 0;
            for (ImageResourceVO image : images) {
                if (!image.isReferenced()) {
                    Path filePath = uploadDir.resolve(image.getFilename()).normalize();
                    try {
                        if (Files.exists(filePath) && Files.isRegularFile(filePath)) {
                            Files.delete(filePath);
                            deleteCount++;
                        }
                    } catch (IOException ignored) {
                    }
                }
            }

            return deleteCount;
        } catch (IOException e) {
            throw new RuntimeException("删除未引用图片失败：" + e.getMessage());
        }
    }

    /**
     * 删除指定图片
     */
    @Override
    public void deleteImage(String filename) {
        // 校验文件名
        if (filename == null || filename.isEmpty()) {
            throw new RuntimeException("文件名不能为空");
        }
        if (filename.contains("..") || filename.contains("/") || filename.contains("\\")) {
            throw new RuntimeException("文件名不合法");
        }

        try {
            String projectRoot = System.getProperty("user.dir");
            Path uploadDir = Paths.get(projectRoot, uploadPath);

            if (!Files.exists(uploadDir) || !Files.isDirectory(uploadDir)) {
                throw new RuntimeException("文件不存在");
            }

            Path filePath = uploadDir.resolve(filename).normalize();

            if (!Files.exists(filePath) || !Files.isRegularFile(filePath)) {
                throw new RuntimeException("文件不存在");
            }

            Files.delete(filePath);
        } catch (IOException e) {
            throw new RuntimeException("删除失败：" + e.getMessage());
        }
    }

    /**
     * 检查图片是否被题目引用（真题、模拟题）
     * 遵循SOLID原则中的单一职责：只负责检查引用关系
     */
    private void checkImageReferences(List<ImageResourceVO> images) {
        if (images == null || images.isEmpty()) {
            return;
        }

        // 检查真题引用
        checkExamQuestionReferences(images);

        // 检查模拟题引用
        checkMockQuestionReferences(images);
    }

    /**
     * 检查真题中的图片引用
     */
    private void checkExamQuestionReferences(List<ImageResourceVO> images) {
        List<ExamQuestion> allQuestions = examService.findAll();
        if (allQuestions == null || allQuestions.isEmpty()) {
            return;
        }

        for (ExamQuestion exam : allQuestions) {
            StringBuilder sb = new StringBuilder();
            if (exam.getContent() != null)
                sb.append(exam.getContent());
            if (exam.getAnswer() != null)
                sb.append(' ').append(exam.getAnswer());
            if (exam.getOptions() != null)
                sb.append(' ').append(exam.getOptions());
            String text = sb.toString();
            if (text.isEmpty())
                continue;

            for (ImageResourceVO image : images) {
                String filename = image.getFilename();
                if (filename != null && !filename.isEmpty() && text.contains(filename)) {
                    image.setReferenced(true);
                    List<ImageUsageExamVO> examList = image.getExams();
                    if (examList == null) {
                        examList = new ArrayList<>();
                        image.setExams(examList);
                    }
                    ImageUsageExamVO usage = new ImageUsageExamVO();
                    usage.setId(exam.getId());
                    usage.setYear(exam.getYear());
                    usage.setQuestionNumber(exam.getQuestionNumber());
                    usage.setTitle(exam.getTitle());
                    examList.add(usage);
                }
            }
        }
    }

    /**
     * 检查模拟题中的图片引用
     */
    private void checkMockQuestionReferences(List<ImageResourceVO> images) {
        List<MockQuestion> allMockQuestions = mockQuestionMapper.findAll();
        if (allMockQuestions == null || allMockQuestions.isEmpty()) {
            return;
        }

        for (MockQuestion mock : allMockQuestions) {
            StringBuilder sb = new StringBuilder();
            if (mock.getContent() != null)
                sb.append(mock.getContent());
            if (mock.getAnswer() != null)
                sb.append(' ').append(mock.getAnswer());
            if (mock.getOptions() != null)
                sb.append(' ').append(mock.getOptions());
            String text = sb.toString();
            if (text.isEmpty())
                continue;

            for (ImageResourceVO image : images) {
                String filename = image.getFilename();
                if (filename != null && !filename.isEmpty() && text.contains(filename)) {
                    image.setReferenced(true);
                    // 模拟题引用信息也添加到exams列表中（复用现有结构）
                    List<ImageUsageExamVO> examList = image.getExams();
                    if (examList == null) {
                        examList = new ArrayList<>();
                        image.setExams(examList);
                    }
                    ImageUsageExamVO usage = new ImageUsageExamVO();
                    usage.setId(mock.getId());
                    usage.setYear(null); // 模拟题没有年份字段
                    usage.setQuestionNumber(mock.getQuestionNumber());
                    usage.setTitle("[模拟题] " + (mock.getTitle() != null ? mock.getTitle() : mock.getSource()));
                    examList.add(usage);
                }
            }
        }
    }

    /**
     * 获取文件扩展名
     */
    private String getFileExtension(String filename) {
        int lastDotIndex = filename.lastIndexOf('.');
        if (lastDotIndex > 0 && lastDotIndex < filename.length() - 1) {
            return filename.substring(lastDotIndex + 1);
        }
        return "";
    }
}
