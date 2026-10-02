"""进程内 AI 运行模块的公开错误契约，沿用现行错误码与中文提示。

错误对象继承项目统一业务异常，只携带固定状态码与消息，不保留原始异常链、
上游响应、请求体或凭据；路由层不需要为它重复编写转换代码。
"""
from typing import Final

from web408.core.exceptions import BusinessException


PUBLIC_ERRORS: Final[dict[str, tuple[int, str]]] = {
    "UNKNOWN_SESSION": (404, "咨询会话不存在或已结束，请重新咨询"),
    "CONFIG_CHANGED": (409, "AI 配置已变化，请重新加载配置"),
    "BUSY": (409, "当前账号有模型请求尚未结束，请等待停止确认"),
    "DUPLICATE": (409, "本次请求已被接收，不能重复执行"),
    "HISTORY_LIMIT": (409, "咨询历史已达到上限，请重新创建会话"),
    "CAPACITY": (429, "AI 内存容量已满，请稍后重试"),
    "PROVIDER_UNSUPPORTED": (422, "该供应商不支持当前的单 API Key 接入方式"),
    "MODEL_UNSUPPORTED": (422, "模型目录未收录可用于文本咨询的该型号，请重新选择"),
    "TEXT_ONLY": (422, "当前阶段只支持纯文本咨询，图片链路尚未接入"),
    "INVALID_REQUEST": (422, "AI 请求字段或文本大小无效"),
    "INVALID_KEY": (422, "API Key 格式无效，请重新填写"),
    "STOP_UNCONFIRMED": (503, "模型请求停止尚未确认，暂时不能开始新的生成"),
    "SERVER_CLOSING": (503, "AI 服务正在关闭，请稍后重试"),
    "SDK_UNAVAILABLE": (503, "AI 模型运行模块初始化失败，请检查部署依赖"),
    "TIMEOUT": (502, "模型请求超时，本次请求已结束"),
    "OUTPUT_LIMIT": (502, "模型输出或流缓冲超过上限，本次回答不完整"),
    "UPSTREAM": (502, "模型调用失败，请检查供应商凭据、模型权限或稍后重试"),
    "STREAM_INTERRUPTED": (502, "咨询流已中断，本次回答不完整，请重新咨询"),
}


class AiRuntimeError(BusinessException):
    """只暴露固定公开错误，禁止把上游异常原因带出运行模块。"""

    def __init__(self, reason: str) -> None:
        status, message = PUBLIC_ERRORS[reason]
        self.reason = reason
        super().__init__(status, message)
