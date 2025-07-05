from enum import Enum
from functools import reduce
from importlib import import_module
from inspect import getsourcelines
from os.path import sep
from pathlib import Path

from util.function_visitor import FunctionVisitor
from util.logger import Logger, LoggerName


# 코드 조회기 로그 출력 설정.
logger = Logger().get_logger(LoggerName.Internal)

# 괄호 열거형 클래스.
class Params(Enum):
  Open = ("(", "[", "{")
  Close = (")", "]", "}")


# 함수 속성 정보 클래스.
class FunctionAttribute:
  def __init__(self, codes={}, start=0, end=0):
    self.codes = codes
    self.start_lineno = start
    self.end_lineno = end


# 실제 코드 위치 검색기 클래스.
class CodeInfo():

  def __init__(self):
    self.codes = {}


  # 경로 path의 코드에서 함수 별 코드를 설정합니다.
  def set_code(self, path: Path):
    module = import_module(path.with_suffix('').as_posix().replace(sep, '.'))

    for name in FunctionVisitor().get_attribute_names(path):      
      # 찾은 속성이 함수가 아닌 property라면 넘어가기.  
      attrs = name.split(".") if "." in name else [name]
      attr = reduce(getattr, attrs, module)
      if not callable(attr): continue

      codes, lineno = getsourcelines(attr)
      self.codes[name] = FunctionAttribute(CodeInfo._get_complete_codes(codes), lineno, lineno + len(codes) - 1)


  # 코드 리스트 codes에서 구문이 완전한 코드 문장의 첫 위치, 내용 쌍을 dict로 반환합니다.
  @staticmethod
  def _get_complete_codes(codes: list[str]) -> dict:
    complete_codes, buffer, start_id = {}, "", 0

    for i, line in enumerate(codes):
      # 공백, 이스케이프 제거 시 내용이 없으면 넘어가기.
      clean_line = line.encode('utf-8').decode('unicode_escape').strip()
      if not clean_line: continue
      
      # 기록 중인 코드에 구문 오류가 있으면 넘어가기.
      buffer = CodeInfo._add_codes(buffer, clean_line)
      if sum(buffer.count(c) for c in '([{') != sum(buffer.count(c) for c in ')]}'): continue

      complete_codes[start_id+1] = buffer
      buffer, start_id = "", i
      
    return complete_codes


  # 두 코드 a, b를 연결합니다.
  @staticmethod
  def _add_codes(a: str, b: str) -> str:
    if not a or a.endswith(Params.Open.value) or b.startswith(Params.Close.value):
      return f"{a}{b}"
    return f"{a} {b}"
  

  # lineno를 기준으로 함수 fct, 코드 code의 가장 가까운 코드 줄 위치를 반환합니다.
  def find(self, fct: str, code: str, lineno=0) -> int:
    # 코드에 없는 함수라면 탐색 중단.
    if fct not in self.codes.keys(): return -1

    # 가장 가능성이 높은 코드 줄 위치가 없으면 탐색 중단.
    candidates = self._get_potential_lineno(fct, code)
    if not candidates: return -1

    distance = [cand - lineno for cand in candidates]
    return candidates[distance.index(min(distance))]
  

  # 함수 fct의 코드 code의 가장 가능성이 높은 실제 코드 줄 위치 리스트를 반환합니다.
  def _get_potential_lineno(self, fct: str, code: str) -> list[int]:
    try:
      candidates = []
      for i, codes in self.codes[fct].codes.items():
        if code not in codes: continue
        candidates.append(self.codes[fct].start_lineno + i)
      return candidates
    # 함수를 찾을 수 없는 경우 위치 탐색 중단.
    except TypeError:
      logger.warning(f"errorline ignored: can't find '{fct}' function")
      return []
    # 일치하는 내용의 코드가 없는 경우 위치 탐색 중단.
    except ValueError:
      logger.warning(f"errorline ignored: can't find matched code")
      return []
    

  # 코드 조회기에 등록한 함수 이름 리스트를 반환합니다.
  def get_functions(self) -> list[str]:
    return self.codes.keys()
  

  # 코드 조회기에 등록한 함수 fct의 코드 리스트를 반환합니다.
  def get_codes(self, fct: str) -> list[str]:
    if fct not in self.get_functions(): return []
    if not self.codes[fct]: return []
    return self.codes[fct].codes.values()
  

  # 코드 조회기에 등록한 줄 번호 lineno가 함수 fct 안에 있는지 여부를 반환합니다.
  def is_in_range(self, fct:str, lineno: int) -> bool:
    for full_name in self.get_functions():
      if not full_name.endswith(fct): continue
      if not self.codes[full_name]: continue
      if not self.codes[full_name].start_lineno <= lineno <= self.codes[full_name].end_lineno: continue
      return True
    return False