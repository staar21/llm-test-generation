from argparse import ArgumentParser
from enum import Enum
from pathlib import Path

from common.errorline import ErrorLine
from common.function import Function
from models.model import ModelFactory
from tools.test_generator.neg_test_generator import NegativeTestGeneratorBuidler
from util.filesys import read_json, write_file, write_json, make_directory
from util.logger import Logger, LoggerName
from validation.framework import TestFrameworkFactory


# 테스트 생성기 로그 출력 설정.
logger = Logger().get_logger(LoggerName.Tool)

# 테스트 생성기 실행 초기 값 열거형 클래스.
class Default(Enum):
  Model = "response"
  Framework = "pytest"
  Model_Config_Path = Path("configs/openai/response/neg_test_generator.json")
  Framework_Config_Path = Path()
  Out_DirPath = Path("out")


# 코드 경로 리스트 src, 사용자 정의 정보 딕셔너리 res, 오류 줄 리스트 lines에 대하여
# n개의 유효한 테스트를 찾거나 최대 iter번 수행하기 전까지 cand개씩 Negative 테스트를 만들고 유효한 테스트를 반환합니다.
def run(src: list[Path], lines: list[ErrorLine], res={}, iter=1, cand=3, n=3,
        model=Default.Model.value, model_conf={}, frame=Default.Framework.value, frame_conf={}) -> list[Function]:
  generator = (NegativeTestGeneratorBuidler()
               .add_pass_type("TypeError")
               .set_paths(src)
               .set_res(res)
               .set_iteration(iter)
               .set_candidates(cand)
               .set_targets(n)
               .set_model(model, config=model_conf)
               .set_framework(frame, config=frame_conf)
               .set_name(f"{lines[0].method}_neg")
               .build())

  candidates = {}
  logger.info("Running negative testcase generation")

  for line in lines:
    logger.info(f"target: {line.method}: {line.lineno}:: {line.code}")
    generated = generator.run(fct=line.method, line=line)

    # 생성한 테스트가 없으면 넘어가기.
    if not generated: continue

    for fct in generated:
      candidates.setdefault(fct.result.code, []).append(fct)

    # 충분한 종류의 테스트를 찾으면 중단.
    if len(candidates) >= n: break

  # 테스트 후보가 하나도 없으면 중단.
  if not candidates: return []

  tests = []
  for i in range(max(len(fcts) for fcts in candidates.values())):
    for _, fcts in candidates.items():
      # 최대 테스트 개수를 벗어난 테스트 리스트는 넘어가기.
      if i >= len(fcts): continue

      # 이미 기록한 테스트는 넘어가기.
      if fcts[i] in tests: continue
      tests.append(fcts[i])

      # 충분한 테스트를 찾으면 중단.
      if len(tests) >= n: break
    
    # 충분한 테스트를 찾으면 중단.
    if len(tests) >= n: break
  
  # 테스트 이름 재설정.
  for i in range(len(tests)):
    tests[i].name = f"test_neg_{i+1}"
  return tests[:min(n, len(tests))]


def main():
  # 선택 가능한 모델, 테스트 프레임워크 리스트 구성.
  available_models = ModelFactory.get_keys()
  available_frameworks = TestFrameworkFactory.get_keys()

  # 인자 파싱.
  parser = ArgumentParser()
  parser.add_argument("-s", "--src", metavar="SOURCE_PATH", type=Path, required=True,
                      default=[], nargs="+",
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
  parser.add_argument("-mc", "--model-conf-path", metavar="MODEL_CONFIG_PATH", type=Path,
                      default=Default.Model_Config_Path.value,
                      help="LLM model config json path")
  parser.add_argument("-fw", "--framework", metavar="FRAMEWORK_NAME", type=str,
                      default=Default.Framework.value, choices=available_frameworks,
                      help=f"Test framework name {available_frameworks}")
  parser.add_argument("-fc", "--framework-conf-path", metavar="FRAMEWORK_CONFIG_PATH", type=Path,
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
  model_path = args.model_conf_path
  fw = args.framework
  fw_path = args.framework_conf_path
  out = args.out

  # 추가 정보, 설정 내용 상세 구성.
  res = dict(item.split(":", 1) for item in res if ":" in item)
  model_config = read_json(model_path) if model_path != Path() else {}
  fw_config = read_json(fw_path) if fw_path != Path() else {}

  # 테스트케이스 생성.
  errorlines = ErrorLine.from_json(read_json(err))
  testcases = run(src, errorlines, res, iter, gen, num,
                  model, model_config, fw, fw_config)

  # 테스트케이스 기록.
  tests_dirpath = out/"tests"
  neg_code_path = tests_dirpath/"neg.py"
  neg_json_path = tests_dirpath/"neg.json"
  make_directory(tests_dirpath)
  write_file(neg_code_path, "\n\n".join(test.to_py() for test in testcases))
  write_json(neg_json_path, {"codes": [test.to_dict() for test in testcases]})

if __name__ == "__main__":
  main()