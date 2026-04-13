from flask import Flask, render_template_string, request
import sympy as sp

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Калькулятор пределов</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            margin: 0;
            background-color: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            max-width: 500px;
            width: 90%;
            text-align: left;
        }
        h1 {
            text-align: center;
            color: #333;
        }
        label {
            font-weight: bold;
            display: block;
            margin-top: 15px;
        }
        input[type="text"], select {
            width: 100%;
            padding: 10px;
            margin-top: 5px;
            box-sizing: border-box;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }
        input[type="submit"] {
            background-color: #4CAF50;
            color: white;
            padding: 12px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 18px;
            width: 100%;
            margin-top: 25px;
            font-weight: bold;
        }
        input[type="submit"]:hover {
            background-color: #45a049;
        }
        .result {
            margin-top: 25px;
            padding: 15px;
            background-color: #e7f3fe;
            border-left: 6px solid #2196F3;
            border-radius: 5px;
            word-wrap: break-word;
        }
        .error {
            margin-top: 25px;
            padding: 15px;
            background-color: #ffdddd;
            border-left: 6px solid #f44336;
            border-radius: 5px;
            color: #a00;
            word-wrap: break-word;
        }
        .steps {
            margin-top: 20px;
            padding: 15px;
            background-color: #f9f9f9;
            border-left: 6px solid #ff9800;
            border-radius: 5px;
        }
        .steps pre {
            white-space: pre-wrap;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 0;
        }
        .examples {
            margin-top: 15px;
            font-size: 14px;
            color: #666;
        }
        .examples a {
            color: #2196F3;
            text-decoration: none;
            margin-right: 10px;
            cursor: pointer;
        }
        .examples a:hover {
            text-decoration: underline;
        }
        .hint {
            font-size: 13px;
            color: #888;
            margin-top: 3px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>📐 Вычисление предела</h1>
        
        <form method="post" id="limitForm">
            <label for="expression">Функция f(x):</label>
            <input type="text" id="expression" name="expression" value="{{ expression }}" placeholder="например: sin(x)/x" required>
            
            <label for="variable">Переменная:</label>
            <input type="text" id="variable" name="variable" value="{{ variable }}" placeholder="x" required>
            
            <label for="point">Стремится к:</label>
            <input type="text" id="point" name="point" value="{{ point }}" placeholder="0, 5, ∞, -∞, беск">
            <div class="hint">Можно вводить: число, ∞, -∞, бесконечность, беск</div>
            
            <label for="direction">Направление:</label>
            <select id="direction" name="direction">
                <option value="two-sided" {% if direction == 'two-sided' %}selected{% endif %}>Двусторонний</option>
                <option value="+" {% if direction == '+' %}selected{% endif %}>Справа (+)</option>
                <option value="-" {% if direction == '-' %}selected{% endif %}>Слева (-)</option>
            </select>
            
            <input type="submit" value="Вычислить предел">
        </form>
        
        <div class="examples">
            <span>Быстрые примеры: </span>
            <a onclick="fillExample('sin(x)/x', 'x', '0')">sin(x)/x</a>
            <a onclick="fillExample('(1+1/n)**n', 'n', '∞')">(1+1/n)^n</a>
            <a onclick="fillExample('1/x', 'x', '0')">1/x</a>
        </div>
        
        {% if result is not none %}
        <div class="result">
            <strong>Результат:</strong> {{ result }}
        </div>
        {% endif %}
        
        {% if steps %}
        <div class="steps">
            <h3>🧮 Пошаговое решение:</h3>
            <pre>{{ steps }}</pre>
        </div>
        {% endif %}
        
        {% if error %}
        <div class="error">
            <strong>⚠️ Ошибка:</strong> {{ error }}
        </div>
        {% endif %}
    </div>

    <script>
        function fillExample(expr, variable, point) {
            document.getElementById('expression').value = expr;
            document.getElementById('variable').value = variable;
            document.getElementById('point').value = point;
        }
    </script>
</body>
</html>
"""

def is_valid_expression(s, variable):
    try:
        expr = sp.sympify(s)
        free_symbols = expr.free_symbols
        allowed = {sp.Symbol(variable)}
        if not free_symbols.issubset(allowed):
            other = free_symbols - allowed
            return False, f"Выражение содержит посторонние переменные: {', '.join(str(s) for s in other)}"
        return True, expr
    except (sp.SympifyError, TypeError, ValueError) as e:
        return False, f"Не удалось распознать выражение: {e}"

def parse_point(point_str):
    p = point_str.strip()
    if p in ['∞', '+∞', 'oo', 'inf', 'infinity', 'бесконечность', 'беск']:
        return sp.oo
    if p in ['-∞', '-oo', '-inf', '-infinity', '-бесконечность', '-беск']:
        return -sp.oo
    return sp.sympify(p)

def generate_steps(expression, var_str, point_val, direction, limit_raw):
    """Генерирует текстовое описание шагов для популярных пределов."""
    expr_str = expression.strip()
    var = sp.Symbol(var_str)
    
    # 1. sin(x)/x при x->0
    if expr_str == "sin(x)/x" and point_val == 0:
        return ("1. Подстановка x=0 даёт неопределённость 0/0.\n"
                "2. Применяем правило Лопиталя: (sin(x))' = cos(x), (x)' = 1.\n"
                "3. Новый предел: lim cos(x)/1 = cos(0) = 1.\n"
                "4. Ответ: 1.")
    
    # 2. 1/x при x->0 (разные направления)
    if expr_str == "1/x" and point_val == 0:
        if direction == '+':
            return ("1. При x→0⁺ (x>0) функция 1/x неограниченно возрастает.\n"
                    "2. Предел равен +∞.")
        elif direction == '-':
            return ("1. При x→0⁻ (x<0) функция 1/x неограниченно убывает.\n"
                    "2. Предел равен -∞.")
        else:
            return ("1. Слева x→0⁻: 1/x → -∞.\n"
                    "2. Справа x→0⁺: 1/x → +∞.\n"
                    "3. Односторонние пределы различны → двусторонний предел не существует.")
    
    # 3. (1+1/n)^n при n→∞
    if expr_str in ["(1+1/n)**n", "(1+1/n)^n"] and point_val == sp.oo:
        return ("1. Это второй замечательный предел.\n"
                "2. Известно, что lim_{n→∞} (1+1/n)^n = e.\n"
                "3. Ответ: e (число Эйлера).")
    
    # 4. Полиномиальные/рациональные дроби при x→∞
    if point_val == sp.oo or point_val == -sp.oo:
        try:
            num, den = sp.fraction(sp.sympify(expr_str))
            if den == 1:
                # Полином
                lead = sp.LC(expr_str.subs(var, var))
                return (f"1. Предел полинома на бесконечности определяется старшим членом.\n"
                        f"2. Старший член: {lead} * {var}**{sp.degree(expr_str)}.\n"
                        f"3. При x→∞ это выражение стремится к {'∞' if lead > 0 else '-∞'}.")
            else:
                deg_num = sp.degree(num, var)
                deg_den = sp.degree(den, var)
                if deg_num < deg_den:
                    return (f"1. Степень числителя ({deg_num}) меньше степени знаменателя ({deg_den}).\n"
                            f"2. Предел равен 0.")
                elif deg_num == deg_den:
                    coeff = sp.LC(num, var) / sp.LC(den, var)
                    return (f"1. Степени числителя и знаменателя равны ({deg_num}).\n"
                            f"2. Предел равен отношению старших коэффициентов: {coeff}.")
                else:
                    return (f"1. Степень числителя ({deg_num}) больше степени знаменателя ({deg_den}).\n"
                            f"2. Предел равен ∞ (знак определяется отношением старших коэффициентов).")
        except:
            pass
    
    # 5. sin(1/x) при x->0
    if expr_str == "sin(1/x)" and point_val == 0:
        return ("1. При x→0 аргумент 1/x неограниченно растёт.\n"
                "2. Функция sin(t) при t→∞ не имеет предела, она колеблется между -1 и 1.\n"
                "3. Следовательно, предел не существует (но ограничен в [-1,1]).")
    
    # По умолчанию – короткое пояснение
    return ("Предел вычислен аналитически с помощью библиотеки SymPy.\n"
            "Использованы правила: арифметика пределов, замечательные пределы,\n"
            "правило Лопиталя (при необходимости).")

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    steps = None
    expression = "sin(x)/x"
    variable = "x"
    point = "0"
    direction = "two-sided"
    
    if request.method == 'POST':
        expression = request.form.get('expression', '').strip()
        variable = request.form.get('variable', '').strip()
        point = request.form.get('point', '').strip()
        direction = request.form.get('direction', 'two-sided')
        
        if not expression or not variable or not point:
            error = "Все поля должны быть заполнены."
        else:
            valid, msg = is_valid_expression(expression, variable)
            if not valid:
                error = msg
            else:
                try:
                    var = sp.Symbol(variable)
                    expr = sp.sympify(expression)
                    point_val = parse_point(point)
                    
                    if direction == "two-sided":
                        limit_raw = sp.limit(expr, var, point_val, dir='+-')
                    else:
                        limit_raw = sp.limit(expr, var, point_val, dir=direction)
                    
                    # Обработка AccumBounds
                    if isinstance(limit_raw, sp.AccumBounds):
                        result = f"не существует (предел колеблется от {limit_raw.min} до {limit_raw.max})"
                    elif limit_raw == sp.zoo:
                        result = "не существует (комплексная бесконечность)"
                    elif limit_raw == sp.oo:
                        result = "∞"
                    elif limit_raw == -sp.oo:
                        result = "-∞"
                    else:
                        result = str(limit_raw)
                    
                    # Генерация шагов
                    steps = generate_steps(expression, variable, point_val, direction, limit_raw)
                    
                except Exception as e:
                    error = f"Ошибка при вычислении: {e}"
    
    return render_template_string(
        HTML_TEMPLATE,
        result=result,
        error=error,
        steps=steps,
        expression=expression,
        variable=variable,
        point=point,
        direction=direction
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)