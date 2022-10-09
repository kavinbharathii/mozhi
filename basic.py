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
        return res 

class IllegalCharError(Error):
    def __init__(self, pos_start, pos_end, details):
        super().__init__(pos_start, pos_end, "Illegal Charecter", details)

# ---------------------------- POSITION ---------------------------- # 

class Position:
    def __init__(self, ind, ln, col, fn, ftxt):
        self.ind = ind
        self.ln = ln
        self.col = col
        self.fn = fn
        self.ftxt = ftxt

    def advance(self, current_char):
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
TT_LPAREN = "LPAREN" 
TT_RPAREN = "RPAREN"

class Token:
    def __init__(self, type_, value = None):
        self.type = type_
        self.value = value


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
                tokens.append(Token(TT_PLUS))
                self.advance()
            elif self.current_char == '-':
                tokens.append(Token(TT_MINUS))
                self.advance()
            elif self.current_char == '*':
                tokens.append(Token(TT_MULT))
                self.advance()
            elif self.current_char == '/':
                tokens.append(Token(TT_DIV))
                self.advance()
            elif self.current_char == '(':
                tokens.append(Token(TT_LPAREN))
                self.advance()
            elif self.current_char == ')':
                tokens.append(Token(TT_RPAREN))
                self.advance()
            else:
                pos_start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(pos_start, self.pos, f"'{char}'")

        return tokens, None

    def make_number(self):
        num_str = ''
        point_count = 0

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if point_count == 1: break
                num_str += '.'
                point_count += 1
            else:
                num_str += self.current_char

            self.advance()

        if point_count == 0:
            return Token(TT_INT, int(num_str))
        else:
            return Token(TT_FLOAT, float(num_str))

            
# ----------------------------  RUN  ---------------------------- # 
def run(fn, text):
    lexer = Lexer(fn, text)
    tokens, err = lexer.make_tokens()
    return tokens, err