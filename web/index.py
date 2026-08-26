from flask import Flask
from datetime import datetime as dt
app = Flask(__name__)
@app.route('/')
def index():
    now = dt.now()
    today = now.strftime("%a-%d/%m,%Y-%B-%y %H:%M:%S")
    htmlcode = f'Hello, World!<BR>Sawadeeeeeeeeeeeeeeeeeeeeeee<BR>Today is {today}'
    return htmlcode
if __name__ == '__main__':
    app.run(debug=True)