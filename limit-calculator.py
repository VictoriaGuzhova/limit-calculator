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
            <a onclick="fillExample('(1+1/n)**n', 'n', '∞')">(1+1/n)^n → e</a>
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

def parse_point(point_str):
    """Преобразует строку с точкой в число или бесконечность SymPy."""
    p = point_str.strip()
    # Обработка символов бесконечности
    if p in ['∞', '+∞', 'oo', 'inf', 'infinity', 'бесконечность', 'беск']:
        return sp.oo
    if p in ['-∞', '-oo', '-inf', '-infinity', '-бесконечность', '-беск']:
        return -sp.oo
    # Иначе пытаемся распарсить как число
    return sp.sympify(p)

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
            try:
                var = sp.Symbol(variable)
                expr = sp.sympify(expression)
                point_val = parse_point(point)
                
                # Вычисление предела
                if direction == "two-sided":
                    limit_raw = sp.limit(expr, var, point_val, dir='+-')
                else:
                    limit_raw = sp.limit(expr, var, point_val, dir=direction)
                
                # Красивое отображение результата
                if limit_raw == sp.zoo:
                    result = "не существует (комплексная бесконечность)"
                elif limit_raw == sp.oo:
                    result = "∞"
                elif limit_raw == -sp.oo:
                    result = "-∞"
                else:
                    result = str(limit_raw)
                
                # Пошаговое решение (демонстрационное для sin(x)/x)
                if expression == "sin(x)/x" and str(point_val) == "0":
                    steps = (
                        "1. Исходный предел: lim (sin(x)/x) при x → 0.\n"
                        "2. Подстановка x=0 даёт неопределённость 0/0.\n"
                        "3. Применяем правило Лопиталя: производная числителя cos(x), знаменателя 1.\n"
                        "4. Новый предел: lim cos(x) при x → 0 = cos(0) = 1.\n"
                        "5. Ответ: 1."
                    )
                else:
                    steps = "Пошаговое решение доступно для примера sin(x)/x при x→0."
                    
            except Exception as e:
                error = f"Ошибка: {e}"
    
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