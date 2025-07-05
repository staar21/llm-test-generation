from enum import Enum
from logging import basicConfig, getLogger, Logger, INFO, DEBUG


# 로그 이름 열거형 클래스.
class LoggerName(Enum):
  Internal = "internal"
  Tool = "tool"


# 로그 클래스.
class Logger:

  _instance = None

  def __init__(self):
    basicConfig(format="[%(levelname)s] %(message)s")
    for name in LoggerName:
      getLogger(name.value).setLevel(INFO)

  def __call__(cls):
    try:
      # 이미 만든 로그 객체를 반환합니다.
      return cls._instance
    # 이미 만든 로그 객체가 없으면 새로 객체를 생성합니다.
    except AttributeError:
      cls._instance = super(Logger, cls).__new__(cls)
      return cls._instance


  # 이름 name을 가진 로그 객체를 반환합니다.
  @classmethod
  def get_logger(cls, name: LoggerName) -> Logger:
    return getLogger(name.value)