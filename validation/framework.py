from abc import abstractmethod
from pathlib import Path

from common.error import Error
from util.filesys import make_directory


# 테스트 프레임워크 실행기 클래스.
class TestFramework():

  @abstractmethod # 구체화 시 구현 필요.
  def __init__(self, **configs):
    raise NotImplemented("no test framework initialization implementation")


  # 경로 path의 코드를 테스트하여 찾은 오류 리스트를 반환합니다.
  def test(self, path=Path("test/test.py"), **configs) -> list[Error]:
    make_directory(path)
    return self._run_framework(path, **configs)
  

  # 경로 path의 테스트 프레임워크를 실행하고 오류 리스트를 반환합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def _run_framework(self, path: Path, **configs) -> list[Error]:
    raise NotImplemented("no process running implementation")
  

# 테스트 프레임워크 실행기 팩토리 클래스.
class TestFrameworkFactory:

  _registry = {}

  # 이름 name의 테스트 프레임워크를 레지스트리에 등록합니다.
  @classmethod
  def register(cls, name: str):
    def decorator(model_cls):
      cls._registry[name] = model_cls
      return model_cls
    return decorator


  # 이름 name의 테스트 프레임워크를 생성합니다.
  @classmethod
  def create(cls, name: str, **configs) -> TestFramework:
    if name not in cls._registry:
      return None
    return cls._registry[name](**configs)
  

  # 레지스트리에 등록한 모든 테스트 프레임워크 이름을 반환합니다.
  @classmethod
  def get_keys(cls) -> list[str]:
    return list(cls._registry.keys())