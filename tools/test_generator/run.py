from argparse import ArgumentParser
from enum import Enum
from pathlib import Path

from models.model import ModelFactory
from common.errorline import ErrorLine
from common.function import Function
from tools.test_generator.run_neg import run as run_neg
from tools.test_generator.run_pos import run as run_pos
from util.filesys import read_json, write_file, write_json, make_directory
from validation.framework import TestFrameworkFactory


# 테스트 생성기 실행 초기 값 열거형 클래스.
class Default(Enum):
  Model = "response"
  Framework = "pytest"
  Model_Neg_Config_Path = Path("configs/openai/response/neg_test_generator.json")
  Model_Pos_Config_Path = Path("configs/openai/response/pos_test_generator.json")
  Framework_Config_Path = Path()
  Out_DirPath = Path("out")


# 코드 경로 리스트 src, 사용자 정의 정보 딕셔녀리 res, 오류 줄 리스트 lines에 대하여
# n개의 유효한 테스트를 찾거나 최대 iter번 수행하기 전까지 cand개씩 Positive 테스트를 만들고 유효한 테스트를 반환합니다.
def run(src: list[Path], res: dict, lines: list[ErrorLine], iter=1, cand=3, n=3,
        model=Default.Model.value, neg_conf={}, pos_conf={}, frame=Default.Framework.value, frame_conf={}) -> tuple[list[Function], list[Function]]:
  neg_tests = run_neg(src, lines, res, iter, cand, n,
                      model, neg_conf, frame, frame_conf)
  if len(neg_tests) == 0: return [], []
  
  pos_tests = run_pos(src, lines, res, iter, cand, 10 - len(neg_tests),
                      model, pos_conf, frame, frame_conf)
  return neg_tests, pos_tests


def main():
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
  parser.add_argument("-e", "--err", metavar="ERRORLINE_PATH", type=Path, required=True,
                      help="errorline list path")
  parser.add_argument("-i", "--iter", metavar="ITERATION_NUM", type=int,
                      default=1,
                      help="request iteration number")
  parser.add_argument("-g", "--gen", metavar="GENERATION_NUM", type=int,
                      default=3,
                      help="generate test number per iteration")
  parser.add_argument("-n", "--num", metavar="TARGET_TEST_NUM", type=int,
                      default=3,
                      help="target test number")
  parser.add_argument("-m", "--model", metavar="MODEL_NAME", type=str,
                      default=Default.Model.value, choices=available_models,
                      help=f"LLM model name {available_models}")
  parser.add_argument("-mn", "--model-neg-config", metavar="MODEL_NEG_CONFIG_PATH", type=Path,
                      default=Default.Model_Neg_Config_Path.value,
                      help="LLM model config for negative test json path")
  parser.add_argument("-mp", "--model-pos-config", metavar="MODEL_POS_CONFIG_PATH", type=Path,
                      default=Default.Model_Pos_Config_Path.value,
                      help="LLM model config for positive test json path")
  parser.add_argument("-fw", "--framework", metavar="FRAMEWORK_NAME", type=str,
                      default=Default.Framework.value, choices=available_frameworks,
                      help=f"Test framework name {available_frameworks}")
  parser.add_argument("-fc", "--framework-config", metavar="FRAMEWORK_CONFIG_PATH", type=Path,
                      default=Default.Framework_Config_Path.value,
                      help="Test framework config json path")
  parser.add_argument("-o", "--out", metavar="OUTPUT_PATH", type=Path,
                      default=Default.Out_DirPath.value,
                      help="output path")
  args = parser.parse_args()

  # 파싱한 인자 연결.
  src = args.src
  res = args.res
  err = args.err
  iter = args.iter
  gen = args.gen
  num = args.num
  model = args.model
  model_neg_path = args.model_neg_config
  model_pos_path = args.model_neg_config
  fw = args.framework
  fw_path = args.framework_config
  out = args.out

  # 추가 정보, 설정 내용 상세 구성.
  res = dict(item.split(":", 1) for item in res if ":" in item)
  model_neg_config = read_json(model_neg_path) if model_neg_path != Path() else {}
  model_pos_config = read_json(model_pos_path) if model_pos_path != Path() else {}
  fw_config = read_json(fw_path) if fw_path != Path() else {}

  # 테스트케이스 생성.
  errorlines = ErrorLine.from_json(read_json(err))
  neg_tests, pos_tests = run(src, res, errorlines, iter, gen, num,
                  model, model_neg_config, model_pos_config, fw, fw_config)

  # 테스트케이스 기록.
  tests_dirpath = out/"tests"
  test_neg_code_path = tests_dirpath/"_neg_test.py"
  test_pos_code_path = tests_dirpath/"_pos_test.py"
  test_neg_json_path = tests_dirpath/"_neg_test.json"
  test_pos_json_path = tests_dirpath/"_pos_test.json"

  make_directory(tests_dirpath)
  
  if neg_tests:
    write_file(test_neg_code_path, "\n\n".join(test.to_py() for test in neg_tests))
    write_json(test_neg_json_path, {"codes": [test.to_dict() for test in neg_tests]})

  if pos_tests:
    write_file(test_pos_code_path, "\n\n".join(test.to_py() for test in pos_tests))
    write_json(test_pos_json_path, {"codes": [test.to_dict() for test in pos_tests]})


if __name__ == "__main__":
  main()