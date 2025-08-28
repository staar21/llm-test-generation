from argparse import ArgumentParser, Namespace
from enum import Enum
from pathlib import Path

from models.model import ModelFactory
from tools.error_line_identifier.run import run as run_identifier, _classify_by_function
from tools.test_generator.run import run as run_tester
from util.filesys import read_json, write_file, write_json, make_directory
from util.logger import Logger, LoggerName
from validation.framework import TestFrameworkFactory
from web_response import WebResponse

# 기능 클래스 로그 출력 설정.
logger = Logger.get_logger(LoggerName.Tool)


# LLM을 이용한 테스트 코드 생성 초기 값 열거형 클래스.
class Default(Enum):
  Model = "response"
  Framework = "pytest"
  Finder_Config_Path = Path("configs/openai/response/error_line_identifier.json")
  Neg_Config_Path = Path("configs/openai/response/neg_test_generator.json")
  Pos_Config_Path = Path("configs/openai/response/pos_test_generator.json")
  Framework_Config_Path = Path()
  Out_DirPath = Path("out")


# 웹 인터페이스 응답 메시지 열거형 클래스.
class ResponseMessage(Enum):
  Error_No_Line = "no type error lines identified"
  Error_No_Neg = "no negative testcases"
  Message_Complete = "negative({}), positive({}) tests generated"


# 입력 인자를 파싱합니다.
def parse_arguments() -> Namespace:
  # 선택 가능한 모델, 테스트 프레임워크 리스트 구성.
  available_models = ModelFactory.get_keys()
  available_frameworks = TestFrameworkFactory.get_keys()

  # 인자 파싱.
  parser = ArgumentParser()
  parser.add_argument("-s", "--src", metavar="SOURCE_PATH", type=Path, required=True,
                      default=[], nargs='+',
                      help="source code file path")
  parser.add_argument("-r", "--res", metavar="MANUAL_RESOURCE", type=str,
                      default=[], nargs='+',
                      help="manual additional data <title>:<content>")
  parser.add_argument("-f", "--fcts", metavar="FUNCTION_NAMES", default=[], nargs='+',
                      help="target function names")
  parser.add_argument("-n", "--neg-num", metavar="NEG_TEST_NUM", type=int,
                      default=3,
                      help="negative test number")
  parser.add_argument("-p", "--pos-num", metavar="POS_TEST_NUM", type=int,
                      default=7,
                      help="positive test number")
  parser.add_argument("-i", "--iter", metavar="ITERATION_NUM", type=int,
                      default=1,
                      help="request iteration number")
  parser.add_argument("-m", "--model", metavar="MODEL_NAME", type=str,
                      default=Default.Model.value, choices=available_models,
                      help=f"LLM model name {available_models}")
  parser.add_argument("-fw", "--framework", metavar="FRAMEWORK_NAME", type=str,
                      default=Default.Framework.value, choices=available_frameworks,
                      help=f"Test framework name {available_frameworks}")
  parser.add_argument("-ec", "--err-configs", metavar="ERRORLINE_CONFIGS_PATH", type=Path,
                      default=Default.Finder_Config_Path.value,
                      help="errorlines finder configs path")
  parser.add_argument("-nc", "--neg-configs", metavar="NEG_CONFIGS_PATH", type=Path,
                      default=Default.Neg_Config_Path.value,
                      help=f"negative test generation configs path")
  parser.add_argument("-pc", "--pos-configs", metavar="POS_CONFIGS_PATH", type=Path,
                      default=Default.Pos_Config_Path.value,
                      help=f"positive test generation configs path")
  parser.add_argument("-fc", "--fw-configs", metavar="FRAMEWORK_CONFIG_PATH", type=Path,
                      default=Default.Framework_Config_Path.value,
                      help="Test framework config json path")
  parser.add_argument("-o", "--out", metavar="OUTPUT_PATH", type=Path,
                      default=Default.Out_DirPath.value,
                      help="output path")
  return parser.parse_args()


def main():

  # 파싱한 인자 연결.
  args = parse_arguments()
  src = args.src
  res = args.res
  fcts = args.fcts
  iter = args.iter
  n_num = args.neg_num
  p_num = args.pos_num
  model = args.model
  fw = args.framework
  err_path = args.err_configs
  neg_path = args.neg_configs
  pos_path = args.pos_configs
  fw_path = args.fw_configs
  out = args.out

  response_dir_path = out/"response"
  make_directory(response_dir_path)
  response = WebResponse()

  # 추가 정보, 설정 내용 상세 구성.
  res = dict(item.split(":", 1) for item in res if ":" in item)
  err_config = read_json(err_path) if err_path != Path() else {}
  neg_config = read_json(neg_path) if neg_path != Path() else {}
  pos_config = read_json(pos_path) if pos_path != Path() else {}
  fw_config = read_json(fw_path) if fw_path != Path() else {}

  # TypeError 발생 가능 코드 줄 탐지.
  errorlines = run_identifier(src[0], fcts, 5, model, err_config)
  classified = _classify_by_function(errorlines)
  for fct in fcts:
    classified.setdefault(fct, [])

  for fct, errs in classified.items():
    if not errs:
      response.set_success(False)
      response.set_message(ResponseMessage.Error_No_Line.value)
      write_json(response_dir_path/f"{fct}.json", response.to_dict())
      logger.info(f"Failed: function {fct} - {ResponseMessage.Error_No_Line.value}")
      continue

    # 테스트케이스 생성.
    neg_tests, pos_tests = run_tester(src, res, errs, iter, 5, n_num, p_num, model, neg_config, pos_config, fw, fw_config)
    response.reset()
    response.set_function(fct)
    response.set_negative_tests(neg_tests)
    response.set_positive_tests(pos_tests)
    
    # Negative 테스트케이스 파일 출력.
    if not neg_tests:
      response.set_success(False)
      response.set_message(ResponseMessage.Error_No_Neg.value)
      write_json(response_dir_path/f"{fct}.json", response.to_dict())
      logger.info(f"Failed: function {fct} - {ResponseMessage.Error_No_Neg.value}")
      continue

    # Negative 테스트케이스 파일 출력.
    if neg_tests:  
      codes = "\n\n".join(test.to_py() for test in neg_tests)
      write_file(out/f"{fct}_neg_test.py", codes)

    # Positive 테스트케이스 파일 출력.
    if pos_tests:
      codes = "\n\n".join(test.to_py() for test in pos_tests)
      write_file(out/f"{fct}_pos_test.py", codes)
    
    msg = ResponseMessage.Message_Complete.value.format(len(neg_tests), len(pos_tests))
    response.set_success(True)
    response.set_message(msg)
    write_json(response_dir_path/f"{fct}.json", response.to_dict())
    logger.info(f"Success: function {fct} - {msg}")


if __name__ == "__main__":
  main()