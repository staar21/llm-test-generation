from __future__ import annotations
from typing_extensions import override

from common.element import Element
from util.logger import Logger, LoggerName


# 오류 정보 클래스 로그 출력 설정.
logger = Logger.get_logger(LoggerName.Internal)


# 오류 정보 클래스.
class Error(Element):

  def __init__(self, type="None", msg="", path="", fct="", code="", lineno=0):
    self.type = type
    self.message = msg
    self.path = path
    self.function = fct
    self.code = code
    self.lineno = lineno
    

  # 오류 종류를 type으로 설정합니다.
  def set_type(self, type: str):
    self.type = type


  # 오류 메시지를 msg로 설정합니다.
  def set_message(self, msg: str):
    self.message = msg


  # pytest 테스트 결과 입력 inp를 오류 리스트로 변환합니다.
  @staticmethod
  def from_pytest(inp: dict) -> list[Error]:
    try:
      results = []
      exitcode = inp.get("exitcode", 2)

      # 인터프리터 실행 실패
      if exitcode > 1:
        collectors = inp.get("collectors", [])
        longrepr = collectors[-1].get("longrepr", "")

        error_line = longrepr.split("\n")[-1].lstrip("E ")
        type, message = error_line.split(": ", 1)
        results.append(Error(type, message))
        return results
      
      # 인터프리터 실행 성공
      else:
        for log in inp.get("tests", []):
          call = log.get("call", {})
          outcome = call.get("outcome", "")

          # 테스트 성공 로그 기록
          if outcome != "failed":
            results.append(Error())

          # 테스트 실패 로그 기록
          else:
            crash = call.get("crash", {})
            longrepr = call.get("longrepr", "")
            traceback = call.get("traceback", [])
            error_line = crash.get("message", "")

            type, message = error_line, ""
            if ": " in error_line:
              type, message = error_line.split(": ", 1)
            path = traceback[-1].get("path", "")
            fct, code, lineno = Error._get_error(longrepr)
            results.append(Error(type, message, path, fct, code, lineno))
        return results
      
    except (TypeError or ValueError):
      logger.warning("error convertion failed: input is not dict")
      return []


  # repr의 호출 함수 리스트를 반환합니다.
  @staticmethod
  def _get_error(repr: list[str]) -> tuple[str, str, int]:
    fct, code = "", ""
    codes = repr.split("\n")
    ind = [0] + [i for i in range(len(codes)) if "_ _ _" in codes[i]] + [-1]
    pairs = [(ind[i], ind[i + 1]) for i in range(len(ind)-2, -1, -1)]

    # 함수 찾기.
    for a, b in pairs:
      for line in codes[a:b]:
        if "def " not in line: continue
        fct = line.split("def ")[1].split("(")[0]
        break
      if fct: break
    
    # 코드 찾기.
    for line in codes[-4::-1]:
      if not line.startswith(">"): continue
      code = line.split(">", 1)[1].strip()
      break

    # 코드 줄 찾기.
    lineno = int(codes[-1].split(":")[1])
    
    return fct, code, lineno


  # 잠재적인 오류 줄이 가진 변수 키, 값 쌍을 반환합니다.
  def to_dict(self):
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
    if self.type == "None":
      return "- no error"
    return f"- {self.path}: {self.function}: {self.code}\n  {self.to_summary()}"


  # 구성 요소를 요약한 정보를 출력합니다.
  @override
  def to_summary(self) -> str:
    if self.type == "None":
      return "passed"
    if self.message:
      return f"{self.type}: {self.message}"
    return self.type