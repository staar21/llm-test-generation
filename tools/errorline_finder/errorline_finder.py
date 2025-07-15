from enum import Enum
from json import loads
from pathlib import Path
from typing_extensions import override

from common.errorline import ErrorLine
from tools.base import ToolBase, ToolBaseBuilder
from util.codeinfo import CodeInfo
from util.filesys import read_file


# LLM 요청 메시지 형식 열거형 클래스.
class Format(Enum):
  Code = "### {}\n```python\n{}\n```"
  Query = "Find {} codes with potential to raise TypeError in '{}'."


# 잠재적인 오류 줄 탐지기 클래스.
class ErrorLineFinder(ToolBase):

  def __init__(self, info: CodeInfo, path: Path):
    self.info = info
    self.path = path


  # 이전 수행 결과 feedback을 바탕으로 LLM API의 프롬프트로 제공할 정보 및 요청 문자열 리스트를 반환합니다.
  @override
  def _generate_queries(self, feedback: bool) -> tuple[list[str], list[str]]:
    info, request = [], []

    # 피드백이 없으면 코드 정보, 생성 요청 반환.
    if not feedback:
      raw_code = "".join(read_file(self.path))
      info = [Format.Code.value.format(self.path, raw_code)]
      request = [Format.Query.value.format("all", self.path)]
      return info, request
    
    # 피드백이 있으면 수정 요청만 반환.
    else:
      request = [Format.Query.value.format("more", self.path)]
      return info, request
    
    
  # LLM API의 수행 결과 out을 처리하여 반환합니다.
  @override
  def _process_outputs(self, out: str) -> list[ErrorLine]:    
    errorlines = []
    for line in ErrorLine.from_json(loads(out)):
      line.lineno = self.info.find(line.method, line.code, line.lineno)
      errorlines.append(line)
    return errorlines
  

  # 결과 out이 유효한지 평가합니다.
  @override
  def _is_valid(self, out: ErrorLine) -> bool:
    if out.lineno <= 0: return False
    elif out.method not in self.info.get_functions(): return False
    else: return any(out.code in code for code in self.info.get_codes(out.method))


  # 결과 리스트 out을 바탕으로 조기 종료 여부를 반환합니다.
  @override
  def _is_terminated(self, out: list[ErrorLine], **kwargs) -> bool:
    return False


  # LLM API의 결과 리스트 out으로부터 결과 수정 요청을 위한 정보를 반환합니다.
  @override
  def _set_feedback(self, out: list[ErrorLine], **kwargs) -> bool:
    return out != None
  

# 잠재적인 오류 줄 탐지기 빌더 클래스.
class ErrorLineFinderBuilder(ToolBaseBuilder):
  
  def __init__(self):
    super().__init__()
    self.info = CodeInfo()
    self.path = ""


  # 대상 경로를 path로 설정합니다.
  def set_path(self, path: Path):
    self.path = path
    self.info.set_code(path)
    return self


  # 설정한 정보로 잠재적인 오류 줄 탐지기를 반환합니다.
  def build(self) -> ErrorLineFinder:
    finder = ErrorLineFinder(self.info, self.path)
    finder.model = self.model
    finder.iteration = self.iteration
    return finder