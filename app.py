from flask import Flask, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/orders')
def orders():
    # 假資料直接在模板中渲染
    return render_template('orders.html')

if __name__ == '__main__':
    app.run(debug=True, port=8080)