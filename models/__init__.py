from enum import Enum

# 레지스트리 모듈 등록
from models.openai.response import Response

# 레지스트리 이름 등록
class Available_Model(Enum):
  Response = "response"