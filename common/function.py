from __future__ import annotations
from typing_extensions import override

from common.element import Element
from util.logger import Logger, LoggerName


# 함수 클래스 로그 출력 설정.
logger = Logger().get_logger(LoggerName.Internal)


# 함수 클래스.
class Function(Element):

  def __init__(self, name="", param="", code="", result=""):
    self.name = name
    self.param = param
    self.code = code
    self.result = result

  def __eq__(self, other):
    return (isinstance(other, Function) and self.code == other.code)
  
  def __hash__(self):
    return hash(self.code)


  # json 형식 dict 입력 inp를 함수로 변환합니다.
  @staticmethod
  def from_json(inp: dict) -> list[Function]:
    try:
      functions = []
      for line in inp.get("codes", []):
        name = line.get("name", "")
        code = line.get("code", "")
        fct = Function(name=name, code=Function._normalize_code(code))
        functions.append(fct)
      return functions
    except (TypeError, ValueError) as e:
      print(e)
      logger.warning(f"function convertion failed: not support {type(inp)} input type")
      return []
  

  # code에서 코드를 포함한 함수 정의문을 없애고 함수 밖의 코드를 제거한 코드를 반환합니다.
  @staticmethod
  def _normalize_code(code: str) -> str:
    # 함수 정의문 제거.
    raw_code = code
    if code.startswith("def "):
      raw_code = code.split(":\n", 1)[1]

    codes = raw_code.split("\n")
    initial_indent = " " * (len(codes[0]) - len(codes[0].lstrip(' ')))

    # 함수 밖의 코드 제거.
    if initial_indent:
      codes = [line for line in codes if line.startswith(initial_indent)]
    else:
      codes = ["\t" + line for line in codes]
    return "\n".join(codes)


  # Python 코드를 반환합니다.
  def to_py(self) -> str:
    return f"def {self.name}({self.param}):\n{self.code}"
  

  # 함수가 가진 변수 키, 값 쌍을 반환합니다.
  def to_dict(self) -> dict:
    var_dict = {}
    for key, value in self.__dict__.items():
      if isinstance(value, list):
        var_dict[key] = [v.__dict__() if hasattr(v, '__dict__') else v for v in value]
      elif hasattr(value, 'to_dict'):
        var_dict[key] = value.to_dict()
      elif hasattr(value, '__dict__'):
        var_dict[key] = value.__dict__()
      else:
        var_dict[key] = value
    return var_dict
  

  # 구성 요소 내용을 출력합니다.
  @override
  def to_string(self) -> str:
    if self.result:
      return f"{self.to_py}\n> {self.result.to_summary}"
    else:
      return f"{self.to_py}"

  # 구성 요소를 요약한 정보를 출력합니다.
  @override
  def to_summary(self) -> str:
    if self.result:
      return f"[{self.name}] {self.result.to_summary()}"
    else:
      return f"[{self.name}]"