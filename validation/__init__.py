from enum import Enum

# 레지스트리 모듈 등록
from validation.pytest import Pytest

# 레지스트리 이름 등록
class Available_Valiator(Enum):
  Pytest = "pytest"