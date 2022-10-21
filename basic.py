# ---------------------------- IMPORTS ---------------------------- # 

from utils import arrow_string

# ---------------------------- CONSTS ---------------------------- # 

DIGITS = "0123456789"

# ---------------------------- ERRORS ---------------------------- # 

class Error:
    def __init__(self, pos_start, pos_end, err_name, details):
        self.pos_start = pos_start
        self.pos_end = pos_end 
        self.err_name = err_name
        self.details = details

    def as_string(self):
        res = f"{self.err_name}: {self.details}"
        res += f"\nFile {self.pos_start.fn}, line {self.pos_start.ln + 1}"
        res += '\n\n' + arrow_string(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return res 

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Charecter", details)

class IllegalSyntaxError(Error):
    def __init__(self, pos_start, pos_end, details=""):
        super().__init__(pos_start, pos_end, "Illegal Syntax", details)

class RunTimeError(Error):
    def __init__(self, pos_start, pos_end, details, context):
        super().__init__(pos_start, pos_end, "Runtime Error", details)
        self.context = context

    def as_string(self):
        res = self.generate_traceback()
        res += f"{self.err_name}: {self.details}"
        res += '\n\n' + arrow_string(self.pos_start.ftxt, self.pos_start, self.pos_end)
        return res 
    
    def generate_traceback(self):
        res = ''
        pos = self.pos_start
        ctx = self.context

        while ctx:
            res += f"  File {pos.fn}, line {str(pos.ln + 1)}, in {ctx.display_name}\n" + res
            pos = ctx.parent_entry_pos
            ctx = ctx.parent

        return 'Traceback (most recent call last):\n' + res

# ---------------------------- POSITION ---------------------------- # 

class Position:
    def __init__(self, ind, ln, col, fn, ftxt):
        self.ind = ind
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char=None):
        self.ind += 1
        self.col += 1

        if current_char == '\n':
            self.ln += 1
            self.col = 0

        return self

    def copy(self):
        return Position(self.ind, self.ln, self.col, self.fn, self.ftxt)

# ---------------------------- TOKENS ---------------------------- # 

TT_INT = "INT"
TT_FLOAT = "FLOAT"
TT_PLUS = "PLUS"
TT_MINUS = "MINUS"
TT_MULT = "MULT"
TT_DIV = "DIV"
TT_EXP = "EXP"
TT_LPAREN = "LPAREN" 
TT_RPAREN = "RPAREN"
TT_EOF = "EOF"

class Token:
    def __init__(self, type_, value = None, pos_start = None, pos_end = None):
        self.type = type_
        self.value = value

        if pos_start:
            self.pos_start = pos_start
            self.pos_end = pos_start.copy()
            self.pos_end.advance()

        if pos_end:
            self.pos_end = pos_end

    def __repr__(self):
        if self.value: return f"{self.type}:{self.value}"
        return f"{self.type}"

# ---------------------------- LEXER ---------------------------- # 


class Lexer:
    def __init__(self, fn, text):
        self.fn = fn
        self.text = text
        self.pos = Position(-1, 0, -1, fn, text)
        self.current_char = None
        self.advance()

    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.ind] if self.pos.ind < len(self.text) else None

    def make_tokens(self):
        tokens = []

        while self.current_char != None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char == '+':
                tokens.append(Token(TT_PLUS, pos_start = self.pos))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS, pos_start = self.pos))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MULT, pos_start = self.pos))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV, pos_start = self.pos))
                self.advance()
            elif self.current_char == '^':
                tokens.append(Token(TT_EXP, pos_start = self.pos))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN, pos_start = self.pos))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN, pos_start = self.pos))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        tokens.append(Token(TT_EOF, pos_start = self.pos))
        return tokens, None

    def make_number(self):
        num_str = ''
        point_count = 0
        pos_start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if point_count == 1: break
                num_str += '.'
                point_count += 1
            else:
                num_str += self.current_char

            self.advance()

        if point_count == 0:
            return Token(TT_INT, int(num_str), pos_start, self.pos)
        else:
            return Token(TT_FLOAT, float(num_str), pos_start, self.pos)

# ----------------------------  NODES  ---------------------------- # 

class NumberNode:
    def __init__(self, tok):
        self.tok = tok
        self.pos_start = self.tok.pos_start
        self.pos_end = self.tok.pos_end
    
    def __repr__(self):
        return f"{self.tok}"


class BinaryOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node
        self.pos_start = self.left_node.pos_start
        self.pos_end = self.right_node.pos_end

    def __repr__(self):
        return f"({self.left_node}, {self.op_token}, {self.right_node})"

class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node

        self.pos_start = self.op_token.pos_start
        self.pos_end = self.node.pos_end

    def __repr__(self):
        return f"({self.op_token}, {self.node})"

# ---------------------------- PARSE RESULT ---------------------------- # 

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None

    def register(self, res):
        if isinstance(res, ParseResult):
            if res.error: self.error = res.error
            return res.node

        return res

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        self.error = error
        return self


# ---------------------------- PARSER ---------------------------- # 

class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.tok_ind = -1
        self.advance()

    def advance(self):
        self.tok_ind += 1
        if self.tok_ind < len(self.tokens):
            self.current_tok = self.tokens[self.tok_ind]
        return self.current_tok

    def parse(self):
        res = self.expr()
        if not res.error and self.current_tok.type != TT_EOF: 
            return res.failure(IllegalSyntaxError(
                self.current_tok.pos_start, self.current_tok.pos_end,
                "Expected '+', '-', '*' or '/'"
            ))
        return res

    def atom(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_INT, TT_FLOAT):
            res.register(self.advance())
            return res.success(NumberNode(tok))

        elif tok.type == TT_LPAREN:
            res.register(self.advance())
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_tok.type == TT_RPAREN:
                res.register(self.advance())
                return res.success(expr)
            else:
                res.failure(IllegalSyntaxError(
                    self.current_tok.pos_start, self.current_tok.pos_end,
                    "Expected ')'"
                ))

        return res.failure(IllegalSyntaxError(
            tok.pos_start, tok.pos_end,
            "Expected int, float, '+', '-', or '('"
        ))

    def power(self):
        return self.bin_op(self.atom, (TT_EXP, ), self.factor)
    
    def factor(self):
        res = ParseResult()
        tok = self.current_tok

        if tok.type in (TT_PLUS, TT_MINUS):
            res.register(self.advance())
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(tok, factor))

        return self.power()

    def term(self):
        x = self.bin_op(self.factor, (TT_MULT, TT_DIV))
        return x

    def expr(self):
        x = self.bin_op(self.term, (TT_PLUS, TT_MINUS))
        return x

    def bin_op(self, func_a, ops, func_b = None):
        if func_b == None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a()) 
        if res.error: return res

        while self.current_tok.type in ops:
            op_tok = self.current_tok
            res.register(self.advance())
            right = res.register(func_b())
            if res.error: return res
            left = BinaryOpNode(left, op_tok, right)

        return res.success(left)

# ----------------------------  RUNTIME RESULT  ---------------------------- # 

class RunTimeResult:
    def __init__(self):
        self.value = None
        self.error = None

    def register(self, res):
        if res.error: self.error = res.error
        return res.value

    def success(self, value):
        self.value = value
        return self

    def failure(self, error):
        self.error = error
        return self

# ----------------------------  VALUES  ---------------------------- # 

class Number:
    def __init__(self, value):
        self.value = value
        self.set_pos()
        self.set_context()
        
    def set_pos(self, pos_start = None, pos_end = None):
        self.pos_start = pos_start
        self.pos_end = pos_end
        return self

    def set_context(self, context = None):
        self.context = context
        return self

    def added_to(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None

    def subbed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None

    def multed_by(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None

    def dived_by(self, other):
        if isinstance(other, Number):
            if other.value == 0: return None, RunTimeError(
                other.pos_start, other.pos_end,
                "Division by Zero",
                self.context
            )
            return Number(self.value / other.value).set_context(self.context), None

    def powerd_by(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None

    def __repr__(self):
        return str(self.value)

# ----------------------------  CONTEXTS  ---------------------------- # 

class Context:
    def __init__(self, display_name, parent = None, parent_entry_pos = None):
        self.display_name = display_name
        self.parent = parent
        self.parent_entry_pos = parent_entry_pos


# ----------------------------  INTERPRETER  ---------------------------- # 

class Interpreter:
    def visit(self, node, context):
        method_name = f"visit_{type(node).__name__}"
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)

    def no_visit_method(self, node, context):
        raise Exception(f"No visit_{type(node).__name__} method defined")

    def visit_NumberNode(self, node, context):
        return RunTimeResult().success(
            Number(node.tok.value).set_context(context).set_pos(node.pos_start, node.pos_end)
        )

    def visit_BinaryOpNode(self, node, context):
        res = RunTimeResult()
        left = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_token.type == TT_PLUS:
            result, error = left.added_to(right)

        if node.op_token.type == TT_MINUS:
            result, error = left.subbed_by(right)
        
        if node.op_token.type == TT_MULT:
            result, error = left.multed_by(right)
        
        if node.op_token.type == TT_DIV:
            result, error = left.dived_by(right)

        if node.op_token.type == TT_EXP:
            result, error = left.powerd_by(right)

        if error: return res.failure(error) 
        else: return res.success(result.set_pos(node.pos_start, node.pos_end))
        
    def visit_UnaryOpNode(self, node, context):
        res = RunTimeResult()
        number = res.register(self.visit(node.node, context))
        if res.error: return res

        error = None

        if node.op_token.type == TT_MINUS:
            number, error = number.multed_by(Number(-1))

        if error: return res.failure(error)
        else: return res.success(number.set_pos(node.pos_start, node.pos_end))
        
# ----------------------------  RUN  ---------------------------- # 
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, err = lexer.make_tokens()
    if err: return None, err

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    interpreter = Interpreter()
    context = Context('<program>')
    result = interpreter.visit(ast.node, context)

    return result.value, result.error
