package com.web408.pojo.vo;

import io.swagger.v3.oas.annotations.media.Schema;

@Schema(name = "ApiResult", description = "统一API响应封装")
public class ApiResult<T> {
    @Schema(description = "业务状态码", example = "200")
    private Integer code;

    @Schema(description = "业务提示信息", example = "成功")
    private String message;

    @Schema(description = "业务数据")
    private T data;

    public ApiResult() {
    }

    private ApiResult(Integer code, String message, T data) {
        this.code = code;
        this.message = message;
        this.data = data;
    }

    public static <T> ApiResult<T> success(T data) {
        return new ApiResult<>(200, "成功", data);
    }

    public static <T> ApiResult<T> success(T data, String message) {
        return new ApiResult<>(200, message, data);
    }

    public static <T> ApiResult<T> error(int code, String message) {
        return new ApiResult<>(code, message, null);
    }

    public Integer getCode() {
        return code;
    }

    public void setCode(Integer code) {
        this.code = code;
    }

    public String getMessage() {
        return message;
    }

    public void setMessage(String message) {
        this.message = message;
    }

    public T getData() {
        return data;
    }

    public void setData(T data) {
        this.data = data;
    }
}
