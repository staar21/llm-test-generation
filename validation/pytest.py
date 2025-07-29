from argparse import ArgumentParser
from enum import Enum
from subprocess import run, DEVNULL
from pathlib import Path
from typing_extensions import override

from common.error import Error
from validation.framework import TestFramework, TestFrameworkFactory
from util.filesys import make_directory, read_json


# Pytest 실행기 초기 값 열거형 클래스.
class Default(Enum):
  Result_Path = Path("test/pytest.json")


# Pytest 프로세스 실행기 클래스.
@TestFrameworkFactory.register("pytest")
class Pytest(TestFramework):

  @override
  def __init__(self, **config): pass

  # 경로 path의 테스트 프레임워크를 실행하고 오류 리스트를 반환합니다.
  @override
  def _run_framework(self, path: Path, out_path=Path("test")) -> list[Error]:
    out_base_path = out_path/"pytest.json"
    make_directory(out_path)
    run(args=['python', '-m', 'pytest', path, "--json-report", "--tb=long", "-s", "--execution-timeout=20", f"--json-report-file={out_base_path}"],
        stdout=DEVNULL, stderr=DEVNULL)
    return Error.from_pytest(read_json(out_base_path))


def main():
  # 인자 파싱.
  parser = ArgumentParser()
  parser.add_argument("-s", "--src", metavar="SOURCE_PATH", type=Path, required=True,
                      help="source code file path")
  parser.add_argument("-o", "--out", metavar="OUTPUT_PATH", type=Path,
                      default=Default.Result_Path.value,
                      help="output path")
  args = parser.parse_args()

  # 파싱한 인자 연결.
  src = args.src
  out = args.out

  # 테스트 수행.
  runner = Pytest()
  for err in runner.test(src, out_path=out):
    print(err.to_string())


if __name__ == "__main__":
  main()