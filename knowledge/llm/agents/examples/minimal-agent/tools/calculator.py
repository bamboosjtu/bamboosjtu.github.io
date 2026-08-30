"""计算器工具🛠️"""
import ast
import math
import operator
import re
from typing import Dict

from pyparsing import Any
from .base import Tool
from .base import ToolParameter

def calc_func(expression: str) -> str:
    """
    极简计算器：只允许数字/运算符/括号/小数点/空格，防止注入。
    """
    if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s]+", expression):
        return "ERROR: expression contains invalid characters."
    try:
        return str(eval(expression, {"__builtins__": {}}, {}))
    except Exception as e:
        return f"ERROR: {e}"
    

class CalculatorTool(Tool):
    """
    Python计算器工具
    """
    # 支持的操作符
    OPERATORS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.BitXor: operator.xor,
        ast.USub: operator.neg,
    }
    
    # 支持的函数
    FUNCTIONS = {
        'abs': abs,
        'round': round,
        'max': max,
        'min': min,
        'sum': sum,
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'exp': math.exp,
        'pi': math.pi,
        'e': math.e,
    }

    def __init__(self):
        super().__init__(
            name="python_calculator",
            description="执行数学计算。支持基本运算、数学函数等。例如：2+3*4, sqrt(16), sin(pi/2)等。"
        )

    def run(self, parameters: Dict[str, Any]) -> str:
        """
        执行计算

        Args:
            parameters: expression

        Returns:
            计算结果
        """
        print(f"🧮 正在计算: {parameters}")
        try:
            node = ast.parse(parameters, mode='eval')
            result = self._eval_node(node.body)
            result_str = str(result)
            return result_str
        except Exception as e:
            error_msg = f"计算失败: {str(e)}"
            print(f"❌ {error_msg}")
            return error_msg

    def get_args_model(self):
        """获取工具参数定义"""

        return [
            ToolParameter(
                name="input",
                type="string",
                description="要计算的数学表达式，支持基本运算和数学函数",
                required=True
            )
        ]

    def _eval_node(self, node):
        """递归计算AST节点"""
        if isinstance(node, ast.Constant):  # Python 3.8+
            return node.value
        elif isinstance(node, ast.BinOp):
            return self.OPERATORS[type(node.op)](
                self._eval_node(node.left), 
                self._eval_node(node.right)
            )
        elif isinstance(node, ast.UnaryOp):
            return self.OPERATORS[type(node.op)](self._eval_node(node.operand))
        elif isinstance(node, ast.Call):
            func_name = node.func.id
            if func_name in self.FUNCTIONS:
                args = [self._eval_node(arg) for arg in node.args]
                return self.FUNCTIONS[func_name](*args)
            else:
                raise ValueError(f"不支持的函数: {func_name}")
        elif isinstance(node, ast.Name):
            if node.id in self.FUNCTIONS:
                return self.FUNCTIONS[node.id]
            else:
                raise ValueError(f"未定义的变量: {node.id}")
        else:
            raise ValueError(f"不支持的表达式类型: {type(node)}")


