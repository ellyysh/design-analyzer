import os
import json
from datetime import datetime
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from functools import wraps

app = Flask(__name__)
app.secret_key = '1A2B3C' 


SCREENSHOTS_DIR = "static/screenshots"
RESPONSES_DIR = "responses"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "12345"  

# Создаём папки если нет
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)
os.makedirs(RESPONSES_DIR, exist_ok=True)


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function


def get_screenshots():
    
    screenshots = []
    if os.path.exists(SCREENSHOTS_DIR):
        for file in os.listdir(SCREENSHOTS_DIR):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                screenshots.append(f"{SCREENSHOTS_DIR}/{file}")
    return screenshots

def get_random_screenshot():
  
    screenshots = get_screenshots()
    if not screenshots:
        return None
    import random
    return random.choice(screenshots)

def save_response(data):
   
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    filename = f"{RESPONSES_DIR}/response_{timestamp}.json"
    

    data['submitted_at'] = datetime.now().isoformat()
    data['screenshot_file'] = data.get('screenshot_url', '').replace(f'{SCREENSHOTS_DIR}/', '')
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return filename

def get_all_responses():
   
    responses = []
    if os.path.exists(RESPONSES_DIR):
        for file in os.listdir(RESPONSES_DIR):
            if file.endswith('.json'):
                with open(f"{RESPONSES_DIR}/{file}", 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    responses.append(data)
  
    responses.sort(key=lambda x: x.get('submitted_at', ''), reverse=True)
    return responses

def export_to_jsonl():
   
    responses = get_all_responses()
    output_file = f"{RESPONSES_DIR}/export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        for resp in responses:
            f.write(json.dumps(resp, ensure_ascii=False) + '\n')
    return output_file

def generate_expert_summary(data):
   
    parts = []
    
    noise = data.get('noise_level', '0')
    menu_count = data.get('menu_count', '0')
    accent_colors = data.get('accent_colors', '0')
    problems = []
    
   
    problem_labels = {
        'prob_much_text': 'Очень много текста',
        'prob_many_buttons': 'Слишком много кнопок/ссылок',
        'prob_many_fonts': 'Разные шрифты (4+ видов)',
        'prob_bright_colors': 'Слишком яркие/кислотные цвета',
        'prob_gray': 'Ничего не выделено, всё серое',
        'prob_many_images': 'Много картинок, мешают',
        'prob_empty': 'Пустые области (много воздуха)'
    }
    
    for key, label in problem_labels.items():
        if data.get(key) == 'on':
            problems.append(label)
    
    
    try:
        if int(noise) >= 4:
            parts.append("Анализ показал КРИТИЧЕСКУЮ визуальную перегруженность страницы.")
        elif int(noise) == 3 or len(problems) >= 3:
            parts.append("Анализ показал УМЕРЕННУЮ визуальную перегруженность страницы.")
        else:
            parts.append("Дизайн оценивается как УМЕРЕННО ЧИСТЫЙ, но есть точки роста.")
    except:
        parts.append("Дизайн требует внимания.")
    
   
    issues = []
    try:
        if int(menu_count) > 9:
            issues.append(f"Верхнее меню содержит {menu_count} пунктов (превышает когнитивный предел 7±2)")
    except:
        pass
    
    try:
        if int(accent_colors) >= 4:
            issues.append(f"Использовано {accent_colors} акцентных цветов → ощущение пестроты")
    except:
        pass
    
    if 'разные шрифты' in str(problems).lower():
        issues.append("Применено множество шрифтов без единой системы")
    
    if data.get('colors_help') == 'Мешают (всё пестрое / сливается)':
        issues.append("Цветовая схема не помогает навигации")
    
    if issues:
        parts.append(f"\nОсновные проблемы: {'; '.join(issues[:3])}")
    
   
    recs = []
    try:
        if int(menu_count) > 9:
            recs.append("Сократить главное меню до 5-7 пунктов, остальное в выпадающие подменю")
    except:
        pass
    
    try:
        if int(accent_colors) >= 4:
            recs.append("Привести цветовую гамму к 1-2 акцентным цветам + нейтральные")
    except:
        pass
    
    if 'разные шрифты' in str(problems).lower():
        recs.append("Унифицировать шрифты (максимум 2 семейства)")
    
    if recs:
        parts.append(f"\nРекомендации: {'; '.join(recs[:3])}")
    else:
        parts.append("\nРекомендации: Улучшить читаемость, уменьшить визуальный шум, выделить ключевые элементы")
    
    return ' '.join(parts)

def aggregate_for_training(responses_by_screenshot):
   
    aggregated = {
        'screenshot': '',
        'total_responses': 0,
        'avg_noise': 0,
        'avg_menu_count': 0,
        'avg_accent_colors': 0,
        'problem_frequencies': {},
        'all_comments': []
    }
    
    noise_sum = 0
    menu_sum = 0
    color_sum = 0
    problem_counts = {}
    
    for resp in responses_by_screenshot:
        aggregated['screenshot'] = resp.get('screenshot_file', '')
        aggregated['total_responses'] += 1
        
   
        try:
            noise_sum += int(resp.get('noise_level', 0))
            menu_sum += int(resp.get('menu_count', 0))
            color_sum += int(resp.get('accent_colors', 0))
        except:
            pass
        

        for key in ['prob_much_text', 'prob_many_buttons', 'prob_many_fonts', 
                    'prob_bright_colors', 'prob_gray', 'prob_many_images', 'prob_empty']:
            if resp.get(key) == 'on':
                problem_counts[key] = problem_counts.get(key, 0) + 1
        

        if resp.get('free_text', '').strip():
            aggregated['all_comments'].append(resp['free_text'])
    
    if aggregated['total_responses'] > 0:
        aggregated['avg_noise'] = round(noise_sum / aggregated['total_responses'], 1)
        aggregated['avg_menu_count'] = round(menu_sum / aggregated['total_responses'], 1)
        aggregated['avg_accent_colors'] = round(color_sum / aggregated['total_responses'], 1)
    
    aggregated['problem_frequencies'] = problem_counts
    return aggregated



@app.route('/')
def index():

    screenshots = get_screenshots()
    return render_template('index.html', screenshots=screenshots)

@app.route('/get_random_screenshot')
def get_random_screenshot_api():
   
    screenshot = get_random_screenshot()
    if screenshot:
        return jsonify({'screenshot_url': screenshot})
    return jsonify({'error': 'Нет скриншотов'}), 404

@app.route('/submit', methods=['POST'])
def submit():
   
    data = request.form.to_dict()
    data['screenshot_url'] = request.form.get('screenshot_url', '')
    

    saved_file = save_response(data)
    
 
    return jsonify({
        "status": "ok", 
        "message": "Спасибо! Ваше мнение сохранено и поможет исследованию."
    })



@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
   
    if request.method == 'POST':
        if request.form.get('username') == ADMIN_USERNAME and request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template('admin_login.html', error='Неверный логин или пароль')
    return render_template('admin_login.html')

@app.route('/admin/logout')
def admin_logout():
 
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Главная админ-панель"""
    responses = get_all_responses()
    screenshots = get_screenshots()
    stats = {
        'total_responses': len(responses),
        'total_screenshots': len(screenshots),
        'avg_responses_per_screenshot': round(len(responses) / len(screenshots), 1) if screenshots else 0
    }
    return render_template('admin_dashboard.html', responses=responses, stats=stats)

@app.route('/admin/responses')
@admin_required
def admin_responses():
   
    responses = get_all_responses()
    return render_template('admin_responses.html', responses=responses)

@app.route('/admin/export')
@admin_required
def admin_export():

    output_file = export_to_jsonl()
    return jsonify({
        'status': 'ok',
        'file': output_file,
        'count': len(get_all_responses())
    })

@app.route('/admin/export_aggregated')
@admin_required
def admin_export_aggregated():
   
    responses = get_all_responses()
    

    grouped = {}
    for resp in responses:
        screenshot = resp.get('screenshot_file', 'unknown')
        if screenshot not in grouped:
            grouped[screenshot] = []
        grouped[screenshot].append(resp)
    

    aggregated = []
    for screenshot, resp_list in grouped.items():
        agg = aggregate_for_training(resp_list)
        aggregated.append(agg)
    
  
    output_file = f"{RESPONSES_DIR}/aggregated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(aggregated, f, ensure_ascii=False, indent=2)
    
    return jsonify({
        'status': 'ok',
        'file': output_file,
        'screenshots_analyzed': len(aggregated)
    })

@app.route('/admin/response/<response_id>')
@admin_required
def admin_response_detail(response_id):

    responses = get_all_responses()
    for resp in responses:
        if response_id in resp.get('submitted_at', ''):
            return render_template('admin_response_detail.html', response=resp)
    return "Не найдено", 404

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)