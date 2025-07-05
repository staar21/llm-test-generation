from __future__ import annotations
from typing_extensions import override

from common.element import Element
from util.logger import Logger, LoggerName


# 오류 줄 클래스 로그 출력 설정.
logger = Logger.get_logger(LoggerName.Internal)


# 잠재적인 오류 줄 클래스.
class ErrorLine(Element):
  
  def __init__(self, code="", lineno=0, method="", reason=""):
    self.code = code
    self.lineno = lineno
    self.method = method
    self.reason = reason

  def __eq__(self, other):
    return (
      isinstance(other, ErrorLine) and
      self.code == other.code and
      self.lineno == other.lineno and
      self.method == other.method)
  
  def __hash__(self):
    return hash((self.code, self.lineno, self.method))


  # 입력 inp를 오류 줄 리스트로 변환합니다.
  @staticmethod
  def from_json(inp: dict) -> list[ErrorLine]:
    try:
      errorlines = []
      for line in inp.get("lines", []):
        code = line.get("code", "")
        lineno = line.get("lineno", 0)
        method = line.get("method", "")
        reason = line.get("reason", "")
        errorlines.append(ErrorLine(code, lineno, method, reason))
      return errorlines
    except (TypeError, ValueError):
      logger.warning(f"errorline convertion failed: not support {type(inp)} input type")
      return []


  # 잠재적인 오류 줄이 가진 변수 키, 값 쌍을 반환합니다.
  def to_dict(self) -> dict:
    var_dict = {}
    for key, value in self.__dict__.items():
      if isinstance(value, list):
        var_dict[key] = [v.__dict__() if hasattr(v, '__dict__') else v for v in value]
      elif hasattr(value, '__dict__'):
        var_dict[key] = value.__dict__()
      else:
        var_dict[key] = value
    return var_dict
  

  # 구성 요소 내용을 출력합니다.
  @override
  def to_string(self) -> str:
    return f"- [{self.method}: {self.lineno}] {self.code}\n  {self.reason}"


  # 구성 요소를 요약한 정보를 출력합니다.
  @override
  def to_summary(self) -> str:
    return f"{self.method}: {self.lineno}"