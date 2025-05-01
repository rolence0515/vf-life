from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for session management and flashing messages

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/orders')
def orders():
    # 假資料直接在模板中渲染
    return render_template('orders.html')

@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # 這裡可加入實際驗證邏輯，暫時只做簡單判斷
        if username == 'admin' and password == 'admin':
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

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True, port=8080)