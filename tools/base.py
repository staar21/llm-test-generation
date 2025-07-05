from abc import abstractmethod
from time import time
from typing_extensions import Any

from models.model import ModelFactory
from util.logger import Logger, LoggerName


# LLM 요청 도구 로그 출력 설정.
logger = Logger.get_logger(LoggerName.Tool)


# LLM 요청 도구 클래스.
class ToolBase():

  def __init__(self, model, iter):
    self.model = model
    self.iteration = iter


  # LLM 요청 도구를 실행합니다.
  def run(self, **kwargs) -> list[Any]:
    outputs, feedback = [], []
    start_time = time()
    self.model.reset()

    for _ in range(self.iteration):
      valids, invalids = self._validate(self.run_once(feedback, **kwargs), **kwargs)
      new_valids = [cand for cand in valids if cand not in outputs]
      
      # 새로운 유효한 결과, 유효하지 않은 결과가 없으면 조기 종료.
      if not new_valids and not invalids:
        logger.info(f"LLM tool stopped: no more items")
        break

      outputs.extend(new_valids)
      if new_valids:
        str_outputs = ", ".join(out.to_summary() for out in new_valids)
        logger.info(f"{len(new_valids)} new items found: total {len(outputs)}\n{str_outputs}")
      else:
        logger.info(f"no items found: total {len(outputs)}")


      # 충분한 결과를 찾으면 조기 종료.
      if self._is_terminated(outputs, **kwargs):
        logger.info(f"LLM running stopped: enough items")
        break

      feedback = self._set_feedback(invalids, **kwargs)

    end_time = time() - start_time
    logger.info(f"LLM running total elapsed time: {end_time:.2f} sec")
    return outputs


  # 이전 수행 결과 feedback을 바탕으로 LLM 요청 도구를 1번 실행하고 결과 리스트를 반환합니다.
  def run_once(self, feedback=None, **kwargs) -> list[Any]:
    info, request = self._generate_queries(feedback, **kwargs)
    str_request = " ".join(request)
    logger.debug(f"send message: {str_request}")

    process = self.model.send_prompt(info + request)
    output = self.model.receive_prompt(process)
    logger.debug(f"received message: {output}")

    if not output: return []
    return self._process_outputs(output, **kwargs)


  # 이전 수행 결과 feedback을 바탕으로 LLM API의 프롬프트로 제공할 정보 및 요청 문자열 리스트를 반환합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def _generate_queries(self, feedback=None, **kwargs) -> tuple[list[str], list[str]]:
    raise NotImplemented("no query generation implementation")


  # LLM API의 수행 결과 out을 원하는 형태로 반환합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def _process_outputs(self, out: list[Any], **kwargs) -> Any:
    raise NotImplemented("no output processing implementation")


  # 결과 리스트 outs의 유효성을 평가하여 유효한 결과, 유효하지 않은 결과 쌍을 반환합니다.
  # 유효한 결과는 LLM 응용 도구의 수행 결과로, 유효하지 않은 결과는 피드백으로 활용합니다.
  def _validate(self, outs: list[Any], **kwargs) -> tuple[list[Any], list[Any]]:
    valids, invalids = [], []
    for out in outs:
      if self._is_valid(out, **kwargs):
        valids.append(out)
      else:
        invalids.append(out)
    return valids, invalids


  # 결과 out이 유효한지 평가합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def _is_valid(self, out: Any, **kwargs) -> bool:
    raise NotImplemented("no validation condition implementation")


  # 결과 리스트 out을 바탕으로 조기 종료 여부를 반환합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def _is_terminated(self, out: list[Any], **kwargs) -> bool:
    raise NotImplemented("no termination condition implementation")


  # LLM API의 결과 리스트 out으로부터 결과 수정 요청을 위한 정보를 반환합니다.
  @abstractmethod # 구체화 시 구현 필요.
  def _set_feedback(self, out: list[Any], **kwargs) -> list[Any]:
    raise NotImplemented("no feedback setting implementation")
  

# LLM 요청 도구 빌더 클래스.
class ToolBaseBuilder():

  def __init__(self):
    self.model = None
    self.iteration = 1


  # LLM 모델을 이름 name의 모델로 구성합니다.
  def set_model(self, name: str, **configs):
    self.model = ModelFactory().create(name, **configs)
    return self


  # LLM 호출 반복 수행 횟수 제한을 iter로 설정합니다.
  def set_iteration(self, iter: int):
    self.iteration = iter
    return self


  # 설정한 정보로 LLM 모델 요청 도구를 반환합니다.
  def build(self) -> ToolBase:
    return ToolBase(self.model, self.iteration)
