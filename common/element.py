from abc import abstractmethod


# 구성 요소 클래스.
class Element():

  # 구성 요소 내용을 출력합니다.
  @abstractmethod # 구체화 시 구현 필요
  def to_string(self) -> str:
    raise NotImplementedError("no print implementation")


  # 구성 요소를 요약한 정보를 출력합니다.
  @abstractmethod # 구체화 시 구현 필요
  def to_summary(self) -> str:
    raise NotImplementedError("no summary implementation")