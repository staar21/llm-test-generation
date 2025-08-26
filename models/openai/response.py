from dotenv import load_dotenv
from enum import Enum
from openai import APITimeoutError, BadRequestError, NotFoundError, OpenAI
from openai.types.responses import Response, ResponseItem
from os import getenv
from time import sleep
from typing_extensions import override

from models.model import Model, ModelFactory
from util.logger import Logger, LoggerName


# 환경 변수로 등록한 OpenAI API 키, 시간 제한 가져오기.
load_dotenv()
try:
  _timeout = float(getenv("LLM_TIMEOUT"))
except Exception:
  _timeout = 60.0
_client = OpenAI(api_key=getenv("OPENAI_API_KEY"), timeout=_timeout)

# LLM 모델 로그 출력 수준 설정.
logger = Logger.get_logger(LoggerName.Internal)

# Response API가 사용 가능한 LLM 모델 열거형 클래스.
class Available_Model(Enum):
  GPT_4o = "gpt-4o"

# Response API의 작업 수행 상태 열거형 클래스.
class Status(Enum):
  Completed = "completed"
  Validating = "validating"
  In_Progress = "in_progress"
  Finalizing = "finializing"
  Cancelling = "cancelling"
  Working = [Validating, In_Progress, Finalizing, Cancelling]


# OpenAI의 Response API를 사용하는 모델 클래스.
@ModelFactory.register("response")
class Response(Model):

  @override
  def __init__(self, config: dict):
    self.model = config.pop('model', Available_Model.GPT_4o.value)
    self.configs = config


  # LLM 모델로 inps 메시지 리스트로 작업을 요청합니다.
  @override
  def send_prompt(self, inps: list[str]) -> Response:
    prompt_inputs = [{"role": "user", "content": inp} for inp in inps]
    response = self._create(self.model, prompt_inputs, **self.configs)
    return response


  # LLM 모델의 요청 req의 수행 결과를 문자열로 반환합니다.
  @override
  def receive_prompt(self, req: Response) -> str:
    try:
      # response 불러오기.
      response = self._retrieve(req.id)
      while response and response.status in Status.Working.value:
        response = self._retrieve(req.id)
        sleep(3)

      # 수행 결과 출력.
      if response.status == Status.Completed.value:
        self.configs["previous_response_id"] = req.id

        for output in response.output:
          if output.type != "message": continue
          for content in output.content:
            if content.type != "output_text": continue
            return content.text
      # 요청을 성공하지 못하면 None 출력.
      else:
        logger.warning(f"{response.status}: {response.output_text}")
        return None
    # 응답을 불러오지 못하면 None 출력.
    except AttributeError:
      logger.warning("no response retrieved")
      return None


  # 모델 기록을 초기화합니다.
  @override
  def reset(self):
    self.configs["previous_response_id"] = None


  # 모델 model로 주어진 입력 inp에 응답하는 OpenAI의 Response를 등록하고 그 객체를 반환합니다.
  # model 목록: https://platform.openai.com/docs/pricing
  # 인자 목록: https://platform.openai.com/docs/api-reference/responses/create
  @staticmethod
  def _create(model: str, inp: list[dict], **kwargs) -> Response:
    try:
      # Response 생성.
      response = _client.responses.create(model=model, input=inp, **kwargs)
      logger.debug(f"new response {response.id} created")
      return response
    # 응답 시간을 초과하면 None 반환.
    except APITimeoutError:
      logger.debug(f"response creation failed: timeout")
      return None
    # 요청을 실패하면 None 반환.
    except BadRequestError or NotFoundError as e:
      error_message = e.body["message"]
      logger.debug(f"response creation failed: {error_message}")
      return None
  

  # id를 가진 OpenAI의 Response를 불러오고 그 객체를 반환합니다.
  @staticmethod
  def _retrieve(id: str) -> Response:
    try:
      # Response 찾기.
      response = _client.responses.retrieve(id)
      logger.debug(f"response {id} retrieved")
      return response
    # 존재하지 않는 id라면 None 반환.
    except ValueError:
      logger.debug("response retrieval failed: invalid id")
      return None
    # 응답 시간을 초과하면 None 반환.
    except APITimeoutError:
      logger.debug(f"response retrieval failed: timeout")
      return None
    # 요청을 실패하면 None 반환.
    except BadRequestError or NotFoundError as e:
      error_message = e.body["message"]
      logger.debug(f"response retrieval failed: {error_message}")
      return None

  # id를 가진 OpenAI의 Response를 제거합니다.
  @staticmethod
  def _delete(id: str):
    try:
      # Response 제거.
      _client.responses.delete(id)
      logger.debug(f"response {id} deleted")
    # 존재하지 않는 id라면 종료.
    except ValueError:
      logger.debug(f"response deletion failed: invalid id")
    # 응답 시간을 초과하면 종료.
    except APITimeoutError:
      logger.debug(f"response deletion failed: timeout")
    # 요청을 실패하면 종료.
    except BadRequestError or NotFoundError as e:
      error_message = e.body["message"]
      logger.debug(f"response deletion failed: {error_message}")


  # rid를 가진 OpenAI의 Response의 입력 요소 목록을 반환합니다.
  # 인자 목록: https://platform.openai.com/docs/api-reference/responses/input-items
  @staticmethod
  def _list(self, rid: str, **kwargs) -> list[ResponseItem]:
    try:
      # Response의 입력 요소 찾기.
      input_items = _client.responses.input_items.list(rid, **kwargs)
      return input_items.data
    # 응답 시간을 초과하면 빈 리스트 반환.
    except APITimeoutError as e:
      logger.debug(f"input item listing failed: timeout")
      return []
    # 요청을 실패하면 빈 리스트 반환.
    except BadRequestError or NotFoundError as e:
      error_message = e.body["message"]
      logger.debug(f"input item listing failed: {error_message}")
      return []