from enum import Enum
from re import search
from typing_extensions import override

from common.errorline import ErrorLine
from common.function import Function
from tools.test_generator.test_generator import TestGenerator, TestGeneratorBuidler
from util.filesys import read_file


# LLM 요청 메시지 형식 열거형 클래스.
class Format(Enum):
  Code = "### {}\n```python\n{}\n```"
  Init_Query = "Write {} tests that trigger {} at `{}`, line {} of {}."
  Fix_Query = "Rewrite test codes to trigger {} in '{}'."
  Nothing = "{} don't trigger any error."
  Other = "{} triggers `{}`."
  Unlocated = "{} triggers `{}` but not in '{}'."

# 특수한 형태의 오류 이름 열거형 클래스.
class Type(Enum):
  Nothing = "None"
  Syntax_Error = "SyntaxError"
  Private_Error = "PrivateAccessError"
  Other = "Other"


# 주어진 지점에서 오류가 발생하는 Negative 테스트케이스 생성기 클래스.
class NegativeTestGenerator(TestGenerator):

  # LLM API의 프롬프트로 제공할 정보 및 요청 문자열 리스트를 반환합니다.
  @override
  def _generate_queries(self, feedback: dict, fct: str, line: ErrorLine, **kwargs) -> list[str]:
    info, request = [], []

    # 피드백이 없으면 코드, 자료, 생성 요청을 반환.
    if not feedback:
      for p in self.src:
        raw_code = "".join(read_file(p))
        info.append(Format.Code.value.format(p, raw_code))

      for key, val in self.res.items():
        info.append(Format.Code.value.format(key, val))

      str_targets = ", ".join(self.pass_type)
      request.append(Format.Init_Query.value.format(self.candidates, str_targets, line.code, line.lineno, line.method))
    
    # 피드백이 있으면 수정 요청을 반환.
    else:
      classified = self._classify(feedback)

      for type, targets in classified.items():
        # 해당 오류 발생 테스트가 없으면 넘어가기.
        if not targets: continue

        for msg, names in targets.items():
          stringfy_names = ", ".join(names)

          # 테스트 통과 타입이지만 오류 발생 코드, 함수가 다른 경우.
          if type in self.pass_type:
            request.append(Format.Unlocated.value.format(stringfy_names, msg, fct))
          # 테스트 통과 타입이 아닌 None인 경우.
          elif type == Type.Nothing.value:
            request.append(Format.Nothing.value.format(stringfy_names))
          # 테스트 통과 타입이 아닌 SyntaxError인 경우.
          elif type == Type.Syntax_Error.value:
            request.append(Format.Other.value.format("All tests", msg))
          # 테스트 통과 타입이 아닌 다른 오류인 경우.
          else:
            request.append(Format.Other.value.format(stringfy_names, msg))
      errors = ", ".join(self.pass_type)
      request.append(Format.Fix_Query.value.format(errors, fct))

    # 내부 변수 사용 시 추가 요청.
    if search('(?:= |\n|\t|\.)\_[a-zA-Z0-9_]+', fct):
      request.append(f"As {fct} is underscore-prefixed, use public method instead.")

    return info, request


  # 수정이 필요한 함수 리스트 feedback을 오류 종류에 따라 구분하고 dict로 반환합니다.
  def _classify(self, feedback: list[Function]) -> dict:
    # 오류 종류 별로 메세지 구분, 대상 테스트 함수 기록.
    special_types = [type.value for type in Type]
    all_types = self.pass_type + special_types
    errors = {type: {} for type in all_types}

    for fct in feedback:
      if search('(?:= |\n|\t|\.)\_[a-zA-Z0-9_]+', fct.code):
        fct.result.type = Type.Private_Error.value
        fct.result.message = "use public method instead of underscore-prefix named method and variable"
        type = Type.Private_Error.value
      else:
        type = fct.result.type if fct.result.type in all_types else Type.Other.value
      errors[type].setdefault(fct.result.to_summary(), []).append(fct.name)
    return errors
  

# Negative 테스트케이스 생성기 빌더 클래스.
class NegativeTestGeneratorBuidler(TestGeneratorBuidler):

  # 설정한 정보로 Negative 테스트케이스 생성기를 반환합니다.
  @override
  def build(self) -> NegativeTestGenerator:
    generator = NegativeTestGenerator(self.pass_type, self.info, self.framework,
                                      self.src, self.res, self.candidates, self.targets, self.name)
    generator.model = self.model
    generator.iteration = self.iteration
    return generator