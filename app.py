import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Flask, render_template, request, jsonify
from datetime import datetime

app = Flask(__name__)

# ===== НАСТРОЙКИ ПОЧТЫ (ЗАМЕНИ НА СВОИ) =====
# Для Gmail нужно включить "Доступ для ненадежных приложений" или создать пароль приложения
EMAIL_SENDER = "manko.04171@gmail.com"        # Твой email (отправитель)
EMAIL_PASSWORD = "emlxwkmowktzegcg"         # Пароль приложения (не обычный пароль!)
EMAIL_RECEIVER = "veryberry.khv@gmail.com"   # Куда отправлять отчеты (может быть тот же)

# Если используешь другой почтовый сервис, поменяй SMTP
SMTP_SERVER = "smtp.gmail.com"               # Для Gmail
SMTP_PORT = 587                               # Для Gmail
# ===========================================

def send_email(subject, body):
    """Отправляет email"""
    try:
        msg = MIMEMultipart()
        msg["From"] = EMAIL_SENDER
        msg["To"] = EMAIL_RECEIVER
        msg["Subject"] = subject
        
        msg.attach(MIMEText(body, "html", "utf-8"))
        
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(EMAIL_SENDER, EMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        print("✅ Email отправлен")
        return True
    except Exception as e:
        print(f"❌ Ошибка отправки email: {e}")
        return False

# Автосканирование скриншотов
def get_screenshots():
    screenshots_dir = "static/screenshots"
    screenshots = []
    
    if not os.path.exists(screenshots_dir):
        os.makedirs(screenshots_dir)
        print(f"📁 Создана папка {screenshots_dir}, положи туда скриншоты")
    
    if os.path.exists(screenshots_dir):
        for file in os.listdir(screenshots_dir):
            if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.webp')):
                screenshots.append(f"{screenshots_dir}/{file}")
    
    if not screenshots:
        screenshots.append("https://placehold.co/800x600/1e293b/white?text=Загрузи+скриншоты+в+папку")
    
    return screenshots

def generate_expert_summary(impression, problems, noise_level, menu_count, accent_colors, fonts, colors_help):
    """Генерирует экспертный вывод"""
    summary_parts = []
    
    noise_int = str(noise_level) if noise_level else "0"
    if noise_int in ['4', '5']:
        summary_parts.append("Анализ показал критическую визуальную перегруженность страницы.")
    elif noise_int == '3' or len(problems) >= 3:
        summary_parts.append("Анализ показал умеренную визуальную перегруженность страницы.")
    else:
        summary_parts.append("Дизайн оценивается как умеренно чистый, но есть точки роста.")
    
    issues = []
    try:
        if int(menu_count) > 9:
            issues.append(f"Верхнее меню содержит {menu_count} пунктов, превышая когнитивный предел (7±2)")
    except:
        pass
    
    try:
        if int(accent_colors) >= 4:
            issues.append(f"Использовано {accent_colors} акцентных цветов, создающих ощущение пестроты")
    except:
        pass
    
    if 'разные шрифты' in str(problems).lower():
        issues.append("Применено множество шрифтов без единой системы")
    
    if colors_help == 'Мешают (всё пестрое / сливается)':
        issues.append("Цветовая схема не помогает навигации, элементы сливаются или конфликтуют")
    
    if issues:
        summary_parts.append(f"\nОсновные проблемы: {', '.join(issues[:3])}")
    
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
    
    if colors_help == 'Мешают (всё пестрое / сливается)':
        recs.append("Увеличить контрастность и создать четкую визуальную иерархию")
    
    if recs:
        summary_parts.append(f"\nРекомендации: {', '.join(recs[:3])}")
    else:
        summary_parts.append("\nРекомендации: Улучшить читаемость, уменьшить визуальный шум, выделить ключевые элементы")
    
    return ' '.join(summary_parts)

def format_feedback(data):
    """Форматирует ответы в красивый отчет (HTML для email)"""
    screenshot = data.get('screenshot_url', 'неизвестно').replace('static/screenshots/', '')
    
    impression = data.get('impression', '—')
    
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
    
    menu_count = data.get('menu_count', '—')
    noise_level = data.get('noise_level', '—')
    fonts = data.get('fonts', '—')
    colors_help = data.get('colors_help', '—')
    cta_found = data.get('cta_found', '—')
    accent_colors = data.get('accent_colors', '—')
    looks_old = data.get('looks_old', '—')
    main_focus = data.get('main_focus', '—')
    free_text = data.get('free_text', '').strip()
    
    # HTML версия для письма
    html_report = f"""
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2 style="color: #3b82f6;">📸 Анализ дизайна</h2>
        <p><strong>Время:</strong> {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}</p>
        <p><strong>Скриншот:</strong> {screenshot}</p>
        
        <h3>📊 Общее впечатление</h3>
        <p>{impression}</p>
        
        <h3>⚠️ Выявленные проблемы</h3>
        <ul>{''.join([f'<li>{p}</li>' for p in problems]) if problems else '<li>Не указаны</li>'}</ul>
        
        <h3>🔢 Количественные параметры</h3>
        <ul>
            <li>Пунктов меню: {menu_count}</li>
            <li>Уровень визуального шума (1-5): {noise_level}</li>
            <li>Акцентных цветов: {accent_colors}</li>
        </ul>
        
        <h3>📖 Читаемость и логика</h3>
        <ul>
            <li>Шрифты: {fonts}</li>
            <li>Цвета: {colors_help}</li>
            <li>Главная кнопка/действие: {cta_found}</li>
            <li>Ощущение устаревшести: {looks_old}</li>
            <li>Главное на сайте: {main_focus}</li>
        </ul>
        
        <h3>💬 Мнение пользователя</h3>
        <p>{free_text if free_text else '—'}</p>
        
        <hr style="border: 1px solid #e2e8f0; margin: 20px 0;">
        
        <h2 style="color: #8b5cf6;">🎯 ИТОГОВАЯ ОЦЕНКА ДЛЯ РЕДИЗАЙНА</h2>
        <p style="background: #f1f5f9; padding: 15px; border-radius: 10px;">
            {generate_expert_summary(impression, problems, noise_level, menu_count, accent_colors, fonts, colors_help)}
        </p>
    </body>
    </html>
    """
    
    # Текстовая версия (на всякий случай)
    text_report = f"""
Анализ дизайна | {datetime.now().strftime('%d.%m.%Y %H:%M')}
Скрин: {screenshot}

Общее впечатление: {impression}

Выявленные проблемы:
{chr(10).join(['• ' + p for p in problems]) if problems else '• Не указаны'}

Количественные параметры:
• Пунктов меню: {menu_count}
• Визуальный шум: {noise_level}
• Акцентных цветов: {accent_colors}

Читаемость:
• Шрифты: {fonts}
• Цвета: {colors_help}
• Кнопка: {cta_found}
• Устаревшесть: {looks_old}
• Главное: {main_focus}

Мнение: {free_text}

ИТОГО: {generate_expert_summary(impression, problems, noise_level, menu_count, accent_colors, fonts, colors_help)}
"""
    
    return html_report, text_report

@app.route('/')
def index():
    screenshots = get_screenshots()
    return render_template('index.html', screenshots=screenshots)

@app.route('/submit', methods=['POST'])
def submit():
    data = request.form.to_dict()
    html_report, text_report = format_feedback(data)
    
    # Сохраняем локально (на всякий случай)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
    if not os.path.exists('responses'):
        os.makedirs('responses')
    
    with open(f"responses/response_{timestamp}.html", 'w', encoding='utf-8') as f:
        f.write(html_report)
    
    # Отправляем на почту
    subject = f"🎨 Новый анализ дизайна | {datetime.now().strftime('%d.%m %H:%M')}"
    email_sent = send_email(subject, html_report)
    
    if email_sent:
        return jsonify({"status": "ok", "message": "Спасибо! Отчет отправлен на почту"})
    else:
        return jsonify({"status": "error", "message": "Ошибка отправки, но данные сохранены локально"}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)