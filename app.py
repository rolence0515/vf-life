from flask import Flask, render_template, request, redirect, url_for, flash, session
import requests
from functools import wraps
import secrets

app = Flask(__name__)
app.secret_key = secrets.token_urlsafe(32)  # 使用隨機產生的安全密鑰

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('請先登入', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/orders')
def orders():
    # 假資料直接在模板中渲染
    return render_template('orders.html')

@app.route('/admin')
@login_required
def admin():
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        hcaptcha_token = request.form.get('h-captcha-response')
        if not hcaptcha_token:
            flash('請完成驗證碼', 'danger')
            return render_template('login.html')
        # hCaptcha 驗證
        hcaptcha_secret = 'ES_e3cff9ee84a04dc08df9f3543d599641'  # 請換成你的 secret key
        verify_url = 'https://hcaptcha.com/siteverify'
        data = {
            'secret': hcaptcha_secret,
            'response': hcaptcha_token,
            'remoteip': request.remote_addr
        }
        try:
            resp = requests.post(verify_url, data=data, timeout=5)
            result = resp.json()
            if not result.get('success'):
                flash('驗證碼失敗，請重試', 'danger')
                return render_template('login.html')
        except Exception:
            flash('驗證服務異常，請稍後再試', 'danger')
            return render_template('login.html')
        # 這裡可加入實際驗證邏輯，暫時只做簡單判斷
        if username == 'admin' and password == 'admin':
            session['logged_in'] = True
            flash('登入成功', 'success')
            return redirect(url_for('admin'))
        else:
            flash('帳號或密碼錯誤', 'danger')
    return render_template('login.html')

@app.route('/change-password', methods=['GET', 'POST'])
def change_password():
    if request.method == 'POST':
        old_password = request.form.get('old_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        if new_password != confirm_password:
            flash('新密碼與確認密碼不一致', 'danger')
        elif old_password == new_password:
            flash('新密碼不可與舊密碼相同', 'danger')
        else:
            # 這裡應加入實際密碼驗證與更新邏輯
            flash('密碼修改成功', 'success')
            return redirect(url_for('login'))
    return render_template('change_password.html')

@app.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')
        # 這裡應加入發送重設密碼信件的邏輯
        flash('重設密碼信已寄出，請檢查您的信箱', 'info')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('您已成功登出', 'success')
    return redirect(url_for('login'))

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=8080)