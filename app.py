from flask import Flask, render_template, request, jsonify
import ply.lex as lex
import ply.yacc as yacc

app = Flask(__name__)

# Definición del lexer (análisis léxico)
tokens = ('NUMBER', 'PLUS', 'MINUS', 'TIMES', 'DIVIDE', 'LPAREN', 'RPAREN')

t_PLUS = r'\+'
t_MINUS = r'-'   # El signo menos se define aquí como operador
t_TIMES = r'\*'
t_DIVIDE = r'/'
t_LPAREN = r'\('
t_RPAREN = r'\)'

t_ignore = ' \t'

# Token para números enteros y decimales (sin incluir el signo menos)
def t_NUMBER(t):
    r'\d+(\.\d+)?'
    t.value = float(t.value) if '.' in t.value else int(t.value)
    return t

def t_error(t):
    print(f"Caracter no reconocido: '{t.value[0]}'")
    t.lexer.skip(1)

lexer = lex.lex()

# Definición del parser (análisis sintáctico)
def p_expression_binop(p):
    '''expression : expression PLUS expression
                  | expression MINUS expression'''
    p[0] = ('op', p[2], p[1], p[3])

def p_expression_term(p):
    'expression : term'
    p[0] = p[1]

def p_term_binop(p):
    '''term : term TIMES term
            | term DIVIDE term'''
    p[0] = ('op', p[2], p[1], p[3])

def p_term_factor(p):
    'term : factor'
    p[0] = p[1]

def p_factor_num(p):
    'factor : NUMBER'
    p[0] = ('num', p[1])

def p_factor_negative(p):
    'factor : MINUS factor'
    if isinstance(p[2], tuple) and p[2][0] == 'num':
        # Si el factor es un número, simplemente cambiamos su signo
        p[0] = ('num', -p[2][1])
    else:
        # Si el factor es una expresión, lo representamos como una operación de multiplicación por -1
        p[0] = ('op', '*', ('num', -1), p[2])

def p_factor_group(p):
    'factor : LPAREN expression RPAREN'
    p[0] = p[2]

def p_error(p):
    print("Error de sintaxis")

parser = yacc.yacc()

# Ruta principal
@app.route('/')
def calculadora():
    return render_template('index.html')

# Ruta para analizar la expresión y generar el árbol
@app.route('/analizar', methods=['POST'])
def analizar_expresion():
    try:
        data = request.get_json()
        input_expr = data.get('input')

        if not input_expr:
            return jsonify({"error": "No se recibió ninguna expresión"}), 400

        resultado = parser.parse(input_expr)

        return jsonify({
            "arbol": resultado,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Ruta para generar la tabla de tokens
@app.route("/table", methods=["POST"])
def generate_table():
    try:
        data = request.get_json()
        input_expr = data.get("input")
        if not input_expr:
            return jsonify({"error": "No se recibió ninguna expresión"}), 400

        lexer.input(input_expr)
        tokens_list = []
        for tok in lexer:
            # Si el token es un número decimal, separarlo en partes
            if tok.type == "NUMBER" and isinstance(tok.value, float):
                decimal_str = str(tok.value)
                integer_part, dot, decimal_part = decimal_str.partition(".")
                tokens_list.append({"token": integer_part, "type": "NUMBER"})
                tokens_list.append({"token": dot, "type": "DOT"})
                tokens_list.append({"token": decimal_part, "type": "NUMBER"})
            else:
                tokens_list.append({"token": tok.value, "type": tok.type})

        total_numeros = sum(1 for token in tokens_list if token["type"] == "NUMBER")
        total_operadores = len(tokens_list) - total_numeros

        return jsonify({
            "tokens": tokens_list,
            "total_numeros": total_numeros,
            "total_operadores": total_operadores,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True)
