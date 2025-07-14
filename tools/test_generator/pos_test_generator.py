from enum import Enum
from re import search
from typing_extensions import override

from common.function import Function
from tools.test_generator.test_generator import TestGenerator, TestGeneratorBuidler
from util.filesys import read_file


# LLM 요청 메시지 형식 열거형 클래스.
class Format(Enum):
  Code = "### {}\n```python\n{}\n```"
  Init_Query = "Write {} tests not to trigger any error in '{}'."
  Fix_Query = "Rewrite test codes not to trigger {} in '{}'."
  Errorlines = " at `{}`, line {} of '{}'"
  Error = "{} triggers `{}`."

# 특수한 형태의 오류 이름 열거형 클래스.
class Type(Enum):
  Nothing = "None"
  Syntax_Error = "SyntaxError"
  Private_Error = "PrivateByConventionAccessError"
  Other = "Other"


# 오류가 발생하지 않는 Positive 테스트케이스 생성기 클래스.
class PositiveTestGenerator(TestGenerator):

  # LLM API의 프롬프트로 제공할 정보 및 요청 문자열 리스트를 반환합니다.
  @override
  def _generate_queries(self, feedback: dict, fct: str, **kwargs) -> list[str]:
    info, request = [], []
    
    # 피드백이 없으면 코드, 생성 요청을 반환.
    if not feedback:
      for p in self.src:
        raw_code = "".join(read_file(p))
        info.append(Format.Code.value.format(self.src[0], raw_code))

      for r in self.res:
        raw_res = "".join(read_file(p)[:10])
        info.append(Format.Code.value.format(r, raw_res))

      request.append(Format.Init_Query.value.format(self.candidates, fct))

    # 피드백이 있으면 수정 요청을 반환.
    else:
      classified = self._classify(feedback)

      for type, targets in classified.items():
        # 해당 오류 발생 테스트가 없으면 넘어가기.
        if not targets: continue

        for msg, names in targets.items():
          stringfy_names = ", ".join(names)

          # 테스트 통과 타입이 아닌 SyntaxError인 경우.
          if type == Type.Syntax_Error.value:
            request.append(Format.Error.value.format("All tests", msg))
          # 테스트 통과 타입이 아닌 다른 오류인 경우.
          else:
            request.append(Format.Error.value.format(stringfy_names, msg))
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
  

# Positive 테스트케이스 생성기 빌더 클래스.
class PositiveTestGeneratorBuilder(TestGeneratorBuidler):

  # 설정한 정보로 Positive 테스트케이스 생성기를 반환합니다.
  @override
  def build(self) -> PositiveTestGenerator:
    generator = PositiveTestGenerator(self.pass_type, self.info, self.framework,
                                      self.src, self.res, self.candidates, self.targets, self.name)
    generator.model = self.model
    generator.iteration = self.iteration
    return generator