from ast import NodeVisitor, parse

from util.filesys import read_file


# 함수 AST 탐색 클래스.
class FunctionVisitor(NodeVisitor):

  def __init__(self):
    self.stack = []
    self.names = []


  # 클래스 정의 구문 노드 진입 시 클래스 이름을 스택에 추가합니다.
  def visit_ClassDef(self, node):
    self.stack.append(node.name)
    self.generic_visit(node)
    self.stack.pop()


  # 함수 정의 구문 노드 진입 시 완성된 함수 이름을 리스트에 추가합니다.
  def visit_FunctionDef(self, node):
    if self.stack:
      name = ".".join(self.stack + [node.name])
      self.names.append(name)
    else:
      self.names.append(node.name)


  # 경로 path의 코드를 파싱하면서 구성합니다.
  def get_attribute_names(self, path):
    self.stack.clear()
    self.names.clear()

    raw_code = "".join(read_file(path))
    tree = parse(raw_code)
    self.visit(tree)
    return self.names