from json import loads, dumps, JSONDecodeError
from os import mkdir
from os.path import exists, isdir
from pathlib import Path

from util.logger import Logger, LoggerName


# 기능 클래스 로그 출력 설정.
logger = Logger.get_logger(LoggerName.Internal)


# path 경로의 파일 내용을 불러오고 문자열 리스트로 반환합니다.
def read_file(path: str) -> list[str]:
  try:
    with open(path, "r") as f:
      return f.readlines()
  except FileNotFoundError:
    logger.warning(f"reading data failed: no {path} file")
  except IsADirectoryError:
    logger.warning(f"reading data failed: {path} is a directory")
  except PermissionError:
    logger.warning(f"reading data failed: {path} read permission denied")
  except UnicodeDecodeError:
    logger.warning(f"reading data failed: UTF-8 codec cannot decode {path}")
  return None


# path 경로의 파일을 파일 내용을 불러오고 딕셔너리로 반환합니다.
def read_json(path: str) -> dict:
  try:
    raw_data = "".join(read_file(path))
    return loads(raw_data)
  except TypeError:
    logger.warning("reading data failed: data is not dict")
  except JSONDecodeError:
    logger.warning("reading data failed: data is not json format")
  return {}


# path 경로의 파일을 data 내용의 문자열로 출력합니다.
def write_file(path: str, data: str):
  try:
    with open(path, "w") as f:
      f.write(data)
    logger.debug(f"file created: {path}")
  except TypeError:
    logger.warning("writing data failed: data is not dict")
  except IsADirectoryError:
    logger.warning(f"writing data failed: {path} is a directory")
  except PermissionError:
    logger.warning(f"writing data failed: {path} write permission denied")


# path 경로의 파일을 data 내용의 json으로 출력합니다.
def write_json(path: str, data: dict):
  try:
    with open(path, "w") as f:
      f.write(dumps(data, indent=2))
    logger.debug(f"file created: {path}")
  except IsADirectoryError:
    logger.warning(f"writing data failed: {path} is a directory")
  except PermissionError:
    logger.warning(f"writing data failed: {path} write permission denied")


# path 경로의 폴더를 생성합니다.
def make_directory(path: Path):
  path_tokens = path.parts
  for i in range(len(path_tokens)):
    path = '/'.join(path_tokens[:i+1])
    if not exists(path):
      mkdir(path)
      logger.debug(f"dictionary {path} created")
    elif not isdir(path):
      logger.debug(f"file {path} already exists")