from abc import abstractmethod
from typing_extensions import Any


# LLM 모델 클래스.
class Model:

  @abstractmethod # 구체화 시 구현 필요.
  def __init__(self, **configs):
    raise NotImplemented("no model initialization implementation")


  # LLM 모델로 inps 메시지 리스트로 작업을 요청합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def send_prompt(self, inps: list[str]) -> Any:
    raise NotImplemented("no prompt send implementation")


  # LLM 모델의 요청 req의 수행 결과를 문자열로 반환합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def receive_prompt(self, req: object) -> str:
    raise NotImplemented("no prompt receive implementation")
  

  # 모델 기록을 초기화합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def reset(self):
    raise NotImplemented("no reset implementation")


# LLM 모델 객체 생성 팩토리 클래스.
class ModelFactory:

  _registry = {}

  # 이름 name의 LLM 모델을 레지스트리에 등록합니다.
  @classmethod
  def register(cls, name: str):
    def decorator(model_cls):
      cls._registry[name] = model_cls
      return model_cls
    return decorator


  # 이름 name의 LLM 모델을 생성합니다.
  @classmethod
  def create(cls, name: str, **configs) -> Model:
    if name not in cls._registry:
      return None
    return cls._registry[name](**configs)
  

  # 레지스트리에 등록한 모든 LLM 모델 이름을 반환합니다.
  @classmethod
  def get_keys(cls) -> list[str]:
    return list(cls._registry.keys())