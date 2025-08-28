from typing_extensions import List

from common.function import Function


# PySTAAR 웹 서버 전송용 정보 클래스.
class WebResponse:
  def __init__(self):
    self.function = ""
    self.success = False
    self.message = ""
    self.neg_tests = []
    self.pos_tests = []


  # 함수를 fct로 설정합니다.
  def set_function(self, fct: str):
    self.function = fct


  # 성공 여부를 succ로 설정합니다.
  def set_success(self, succ: bool):
    self.success = succ


  # 메시지를 msg로 설정합니다.
  def set_message(self, msg: str):
    self.message = msg


  # Negative 테스트 목록을 test로 설정합니다.
  def set_negative_tests(self, tests: List[Function]):
    self.neg_tests = tests


  # Positive 테스트 목록을 test로 설정합니다.
  def set_positive_tests(self, tests: List[Function]):
    self.pos_tests = tests


  # 설정 정보를 초기화합니다.
  def reset(self):
    self.function = ""
    self.success = False
    self.message = ""
    self.neg_tests = []
    self.pos_tests = []


  # 웹서버에 전송할 정보를 딕셔너리로 반환합니다.
  def to_dict(self) -> dict:
    response = {
      "function_name": self.function,
      "success": str(self.success),
      "message": self.message,
      "tests": {
        "negatives": [{"code": n.to_py()} for n in self.neg_tests],
        "positives": [{"code": p.to_py()} for p in self.pos_tests]
      }
    }
    return response