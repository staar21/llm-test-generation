from argparse import ArgumentParser
from collections import defaultdict
from enum import Enum
from pathlib import Path

from common.errorline import ErrorLine
from models.model import ModelFactory
from tools.errorline_finder.errorline_finder import ErrorLineFinderBuilder
from util.filesys import make_directory, read_json, write_json


# 오류 탐색기 실행 초기 값 열거형 클래스.
class Default(Enum):
  Model = "response"
  Config_Path = Path("configs/openai/response/errorline_finder.json")
  Out_DirPath = Path("out")


# 이름 model과 configs 설정으로 구성한 LLM 모델을 iter 횟수만큼 실행하여
# 경로 path 코드의 fcts 함수에 대한 TypeError 오류 줄 리스트를 찾습니다.
def run(path: Path, fcts=[], iter=1, model=Default.Model.value, configs={}) -> list[ErrorLine]:
  finder = (ErrorLineFinderBuilder()
            .set_path(path)
            .set_model(model, config=configs)
            .set_iteration(iter)
            .build())

  # 관심 함수를 설정하지 않으면 그대로 반환.
  errorlines = finder.run()
  if not fcts: return errorlines

  # 관심 함수를 설정하면 관심 없는 함수를 제거하여 반환.
  filtered = [line for line in errorlines if line.method in fcts]
  return filtered


# 오류 줄 리스트 lines를 함수 별로 구분하여 dict로 반환합니다.
def _classify_by_function(lines: list[ErrorLine]) -> dict:
  classified = defaultdict(list)
  for line in lines:
    classified[line.method].append(line)
  return classified


def main():
  # 선택 가능한 모델 리스트 구성.
  available_models = ModelFactory.get_keys()

  # 인자 파싱.  
  parser = ArgumentParser()
  parser.add_argument("-s", "--src", metavar="SOURCE_PATH", type=Path, required=True,
                      help="source code file path")
  parser.add_argument("-f", "--fcts", metavar="FUNCTION_NAMES",
                      default=[], nargs='+',
                      help="target function names")
  parser.add_argument("-i", "--iter", metavar="ITERATION_NUM", type=int,
                      default=1,
                      help="request iteration number")
  parser.add_argument("-m", "--model", metavar="MODEL_NAME", type=str,
                      default=Default.Model.value,
                      choices=available_models,
                      help=f"LLM model name {available_models}")
  parser.add_argument("-c", "--configs", metavar="CONFIGS_PATH", type=Path,
                      default=Default.Config_Path.value,
                      help="LLM model configs json path")
  parser.add_argument("-o", "--out", metavar="OUTPUT_PATH", type=Path,
                      default=Default.Out_DirPath.value,
                      help="output path")
  args = parser.parse_args()

  # 파싱한 인자 연결.
  src = args.src
  fcts = args.fcts
  iter = args.iter
  model = args.model
  configs = args.configs
  out = args.out

  # TypeError 발생 가능 코드 줄 탐지.
  errorlines = run(src, fcts, iter, model, read_json(configs))

  # TypeError 오류 줄 기록.
  errorlines_dirpath = out/"errorlines"
  make_directory(errorlines_dirpath)

  for fct, lines in _classify_by_function(errorlines).items():
    errorlines_path = errorlines_dirpath/f"{fct}.json"
    write_json(errorlines_path, {"lines": [line.to_dict() for line in lines]})

if __name__ == "__main__":
  main()