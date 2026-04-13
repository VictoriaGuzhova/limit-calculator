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
            <input type="text" id="point" name="point" value="{{ point }}" placeholder="например: 5, бесконечность, беск, ∞">            
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
            <a onclick="fillExample('sin(x)/x', 'x', '0')">sin(x)/x → 0</a>
            <a onclick="fillExample('(1+1/n)**n', 'n', 'oo')">(1+1/n)^n → ∞</a>
            <a onclick="fillExample('1/x', 'x', '0')">1/x → 0</a>
        </div>
        
        {% if result is not none %}
        <div class="result">
            <strong>Результат:</strong> {{ result }}
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
            // Можно автоматически отправить форму
            // document.getElementById('limitForm').submit();
        }
    </script>
</body>
</html>
"""

def is_valid_expression(s, variable):
    """Проверяет, что строка является корректным математическим выражением с заданной переменной."""
    try:
        expr = sp.sympify(s)
        # Проверяем, что в выражении присутствует переменная (иначе это просто число или строка)
        if not expr.has(sp.Symbol(variable)):
            # Если переменной нет, но это число, то предел можно вычислить (константа)
            # Но если это какая-то строка типа "vze", sympify вернет Symbol('vze'), который не равен переменной
            free_symbols = expr.free_symbols
            if len(free_symbols) > 0 and sp.Symbol(variable) not in free_symbols:
                return False, "Выражение содержит другие переменные, а не указанную."
        return True, expr
    except (sp.SympifyError, TypeError, ValueError) as e:
        return False, f"Не удалось распознать выражение: {e}"

@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    error = None
    expression = "sin(x)/x"
    variable = "x"
    point = "0"
    direction = "two-sided"
    
    if request.method == 'POST':
        expression = request.form.get('expression', '').strip()
        variable = request.form.get('variable', '').strip()
        point = request.form.get('point', '').strip()
        direction = request.form.get('direction', 'two-sided')
        
        # Проверка на пустые поля
        if not expression or not variable or not point:
            error = "Все поля должны быть заполнены."
        else:
            # Проверка корректности выражения
            valid, msg = is_valid_expression(expression, variable)
            if not valid:
                error = msg
            else:
                try:
                    var = sp.Symbol(variable)
                    expr = sp.sympify(expression)
                    
                    # Обработка бесконечности
                    # Обработка бесконечности (русские и английские варианты)
                    point_lower = point.lower().strip()
                    if point_lower in ['oo', 'inf', 'infinity', 'бесконечность', 'беск', '∞']:
                        point_val = sp.oo
                    elif point_lower in ['-oo', '-inf', '-infinity', '-бесконечность', '-беск', '-∞']:
                        point_val = -sp.oo
                    else:
                        try:
                            point_val = sp.sympify(point)
                        except:
                            error = f"Некорректное значение точки: {point}"
                            point_val = None
                    
                    if point_val is not None:
                        # Вычисление предела
                        if direction == "two-sided":
                            result = sp.limit(expr, var, point_val, dir='+-')
                        else:
                            result = sp.limit(expr, var, point_val, dir=direction)
                        
                        # Преобразование zoo/oo/-oo в читаемый вид
                        if result == sp.zoo:
                            result = "не существует (комплексная бесконечность)"
                        elif result == sp.oo:
                            result = "∞"
                        elif result == -sp.oo:
                            result = "-∞"
                        else:
                            result = str(result)
                        
                        # Преобразуем в строку для отображения
                        result = str(result)
                except Exception as e:
                    error = f"Ошибка при вычислении: {e}"
    
    return render_template_string(
        HTML_TEMPLATE,
        result=result,
        error=error,
        expression=expression,
        variable=variable,
        point=point,
        direction=direction
    )

if __name__ == '__main__':
    # Для доступа с телефона замени host='127.0.0.1' на host='0.0.0.0'
    # После запуска смотри в консоли IP-адрес компьютера (например, 192.168.1.5) и подключайся с телефона по http://192.168.1.5:5000
    app.run(host='0.0.0.0', port=5000, debug=True)