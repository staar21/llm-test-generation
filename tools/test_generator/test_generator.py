from abc import abstractmethod
from enum import Enum
from json import loads
from pathlib import Path
from re import search
from typing_extensions import override

from common.function import Function
from tools.base import ToolBase, ToolBaseBuilder

from util.filesys import make_directory, write_file
from util.logger import Logger, LoggerName
from util.codeinfo import CodeInfo
from validation.framework import TestFrameworkFactory


# 테스트 생성기 로그 출력 설정.
logger = Logger().get_logger(LoggerName.Tool)

# 오류 탐색기 실행 초기 값.
class Default(Enum):
  Test_DirPath = Path("test")


# 테스트케이스 생성기 클래스.
class TestGenerator(ToolBase):

  def __init__(self, passed, info, framework, src, res, cands, targets, name):
    self.pass_type = passed
    self.info = info
    self.framework = framework

    self.src = src
    self.res = res
    self.candidates = cands
    self.targets = targets
    
    self.name = name
    self.count = 1


  # LLM API의 수행 결과 out을 처리하여 반환합니다.
  @override
  def _process_outputs(self, out: str, **kwargs) -> list[Function]:
    path = Default.Test_DirPath.value/f"test_{self.name}{self.count}.py"
    functions = Function.from_json(loads(out))
    
    make_directory(Default.Test_DirPath.value)
    write_file(path, "\n\n".join(fct.to_py() for fct in functions))
    errors = self.framework.test(path)
    self.count += 1
    
    # 함수마다 대응하는 오류 매핑.
    pytest_functions = []
    for fct, err in dict(zip(functions, errors)).items():
      fct.result = err
      pytest_functions.append(fct)
    return pytest_functions


  # 결과 out가 유효한 결과인지 판단합니다.
  @override
  def _is_valid(self, out: Function, fct: str, **kwargs) -> bool:
    # 비공개 내부 변수, 함수를 사용하면 유효하지 않음.
    if search('(?:= |\n|\t|\.)\_[a-zA-Z0-9_]+', out.code): return False
    # 통과 가능한 오류 타입이 아니면 유효하지 않음.
    elif out.result.type not in self.pass_type: return False
    elif out.result.type != "None":
      target_fct = fct if "." not in fct else fct.split(".")[-1]
      # 경로가 일치하지 않으면 유효하지 않음.
      if out.result.path != str(self.src[0]): return False
      # 목표 함수가 아니면 유효하지 않음.
      elif target_fct != out.result.function: return False
      elif not self.info.is_in_range(out.result.function, out.result.lineno): return False
    return True
      

  # 결과 out을 참고하여 종료 여부를 반환합니다.
  @override
  def _is_terminated(self, out: list[Function], **kwargs) -> bool:
    return len(out) >= self.targets


  # LLM API의 수행 결과 out으로 정제하기 위한 정보를 반환합니다.
  @override
  def _set_feedback(self, out: list[Function], **kwargs) -> list[Function]:
    return out
  

# 테스트케이스 생성기 빌더 클래스.
class TestGeneratorBuidler(ToolBaseBuilder):

  def __init__(self):
    self.pass_type = []
    self.info = CodeInfo()
    self.framework = None
    
    self.src = []
    self.res = []
    self.candidates = 3
    self.targets = 3
    
    self.name = ""
    self.count = 1


  # 통과 오류 타입 리스트에 이름 name의 오류를 추가합니다.
  def add_pass_type(self, name: str):
    self.pass_type.append(name)
    return self


  # 테스트 프레임워크를 이름 name의 테스트 프레임워크로 구성합니다.
  def set_framework(self, name: str, **configs):
    self.framework = TestFrameworkFactory().create(name, **configs)
    return self


  # 대상 경로를 paths로 설정합니다. 
  def set_paths(self, paths: list[Path]):
    self.src = paths
    self.info.set_code(paths[0])
    return self


  # 사용자 정의 정보를 res로 설정합니다.
  def set_res(self, res: dict):
    self.res = res
    return self


  # 생성할 테스트 후보 개수를 n으로 설정합니다. 
  def set_candidates(self, n: int):
    self.candidates = n
    return self


  # 목표 테스트 개수를 n으로 설정합니다. 
  def set_targets(self, n: int):
    self.targets = n
    return self
  

  # 테스트 제목을 주어진 이름 name으로 설정합니다.
  def set_name(self, name: str):
    self.name = name.replace(".", "_")
    return self
  

  # 설정한 정보로 테스트케이스 생성기를 반환합니다.
  @abstractmethod # 구체화 시 구현 필요
  def build(self) -> TestGenerator:
    raise NotImplementedError("no build implementation")