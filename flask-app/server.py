from flask import Flask
from spotify_api import get_user_info
from secrets import AWS_ACCESS_KEY, AWS_SECRET_KEY

app = Flask(__name__)

@app.route("/connect")
def hello():
    return 'Hello world'

if __name__ == '__main__':
    app.run(debug=True, port=8000)