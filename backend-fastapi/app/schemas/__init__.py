# Schemas Module
from app.schemas.common import Response, PaginatedResponse
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    AuthResponse,
)
from app.schemas.subject import (
    SubjectCreateRequest,
    SubjectUpdateRequest,
    SubjectResponse
)
from app.schemas.chapter import (
    ChapterCreateRequest,
    ChapterUpdateRequest,
    ChapterResponse,
    ChapterTreeResponse
)
from app.schemas.category import (
    ExamCategoryCreateRequest,
    ExamCategoryUpdateRequest,
    ExamCategoryResponse,
    ExamCategoryTreeResponse,
    ExamCategoryStatResponse,
    ExamCategoryUsageResponse
)
from app.schemas.exam import (
    ExamQueryParams,
    ExamCreateRequest,
    ExamUpdateRequest,
    ExamResponse,
    ExamYearStatResponse,
    ExamCategoryStatItem,
    ExamCategoryStatsResponse,
    ExamDuplicateCheckResponse,
    ExamIndexItem,
    ExamIndexResponse,
    PaginatedExamResponse
)
from app.schemas.mock import (
    MockQueryParams,
    MockCreateRequest,
    MockUpdateRequest,
    MockResponse,
    MockSourceStatResponse,
    MockSourceItem,
    MockSourcesResponse,
    MockCategoryStatItem,
    MockCategoryStatsResponse,
    MockDuplicateCheckResponse,
    PaginatedMockResponse
)
from app.schemas.image import (
    ImageUsageResponse,
    ImageResourceResponse
)

__all__ = [
    # Common
    "Response",
    "PaginatedResponse",
    # Auth
    "LoginRequest",
    "RegisterRequest",
    "AuthResponse",
    # Subject
    "SubjectCreateRequest",
    "SubjectUpdateRequest",
    "SubjectResponse",
    # Chapter
    "ChapterCreateRequest",
    "ChapterUpdateRequest",
    "ChapterResponse",
    "ChapterTreeResponse",
    # Category
    "ExamCategoryCreateRequest",
    "ExamCategoryUpdateRequest",
    "ExamCategoryResponse",
    "ExamCategoryTreeResponse",
    "ExamCategoryStatResponse",
    "ExamCategoryUsageResponse",
    # Exam
    "ExamQueryParams",
    "ExamCreateRequest",
    "ExamUpdateRequest",
    "ExamResponse",
    "ExamYearStatResponse",
    "ExamCategoryStatItem",
    "ExamCategoryStatsResponse",
    "ExamDuplicateCheckResponse",
    "ExamIndexItem",
    "ExamIndexResponse",
    "PaginatedExamResponse",
    # Mock
    "MockQueryParams",
    "MockCreateRequest",
    "MockUpdateRequest",
    "MockResponse",
    "MockSourceStatResponse",
    "MockSourceItem",
    "MockSourcesResponse",
    "MockCategoryStatItem",
    "MockCategoryStatsResponse",
    "MockDuplicateCheckResponse",
    "PaginatedMockResponse",
    # Image
    "ImageUsageResponse",
    "ImageResourceResponse",
]
