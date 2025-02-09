from flask import Flask, render_template, request, jsonify, session
import requests
from datetime import datetime
from uuid import uuid4

app = Flask(__name__,
    static_folder='.',    # 当前目录作为静态文件夹
    static_url_path='',   # 禁用默认的/static路径
    template_folder='.')  # 当前目录作为模板文件夹
OLLAMA_URL = "http://localhost:11434/api"
app.secret_key = '5210'  # 设置安全密钥
app.config['SESSION_TYPE'] = 'filesystem'

@app.route('/')
def index():
    return render_template('index.html')  # 现在会直接渲染当前目录的index.html

@app.route('/api/models')
def get_models():
    """获取本地可用模型列表"""
    try:
        models = requests.get(f"{OLLAMA_URL}/tags").json()['models']
        return jsonify([model['name'] for model in models])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/chat/new', methods=['POST'])
def new_chat():
    """创建新对话"""
    session['chat_id'] = str(uuid4())
    session['context'] = []  # 存储对话上下文
    return jsonify({'status': 'success'})

@app.route('/api/chat', methods=['POST'])
def chat():
    """对话接口"""
    data = request.json
    try:
        # 构造带上下文的请求
        payload = {
            "model": data['model'],
            "prompt": data['prompt'],
            "stream": False,
            "context": session.get('context', []),
            "options": {
                "temperature": float(data.get('temperature', 0.7)),  # 确保转换为浮点数
                "num_ctx": 4096  # 上下文长度
            }
        }
        
        temperature = float(data.get('temperature', 0.7))
        if not 0 <= temperature <= 1:
            raise ValueError("温度值必须在0到1之间")
        
        response = requests.post(
            f"{OLLAMA_URL}/generate",
            json=payload,
            timeout=60
        )
        result = response.json()
        
        # 更新上下文
        session['context'] = result.get('context', [])
        session.modified = True
        
        return jsonify({
            "response": result['response'],
            "model": data['model'],
            "time": datetime.now().strftime("%Y-%m-%d %H:%M")
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/style.css')
def serve_css():
    return app.send_static_file('style.css')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
