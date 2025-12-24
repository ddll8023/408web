package com.web408.exception;

import com.web408.pojo.vo.ApiResult;
import org.springframework.http.ResponseEntity;
import org.springframework.validation.FieldError;
import org.springframework.web.bind.MethodArgumentNotValidException;
import org.springframework.web.bind.annotation.ExceptionHandler;
import org.springframework.web.bind.annotation.RestControllerAdvice;

/**
 * 全局异常处理器
 * 统一处理所有Controller抛出的异常
 * 遵循开闭原则：易于扩展新的异常类型
 */
@RestControllerAdvice
public class GlobalExceptionHandler {

    /**
     * 处理参数验证异常
     * 
     * @param ex MethodArgumentNotValidException
     * @return 统一JSON响应
     */
    @ExceptionHandler(MethodArgumentNotValidException.class)
    public ResponseEntity<ApiResult<Void>> handleValidationException(MethodArgumentNotValidException ex) {
        // 提取第一个验证错误信息
        FieldError fieldError = ex.getBindingResult().getFieldError();
        String errorMessage = fieldError != null ? fieldError.getDefaultMessage() : "参数验证失败";
        return ResponseEntity.badRequest().body(ApiResult.error(400, errorMessage));
    }

    /**
     * 处理运行时异常
     * 
     * @param ex RuntimeException
     * @return 统一JSON响应
     */
    @ExceptionHandler(RuntimeException.class)
    public ResponseEntity<ApiResult<Void>> handleRuntimeException(RuntimeException ex) {
        return ResponseEntity.status(500).body(ApiResult.error(500, ex.getMessage()));
    }

    /**
     * 处理所有未捕获的异常
     * 
     * @param ex Exception
     * @return 统一JSON响应
     */
    @ExceptionHandler(Exception.class)
    public ResponseEntity<ApiResult<Void>> handleException(Exception ex) {
        return ResponseEntity.status(500).body(ApiResult.error(500, "服务器内部错误：" + ex.getMessage()));
    }
}
