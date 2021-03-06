import re
from flask import Flask, render_template, g, request, session, url_for
from werkzeug.utils import redirect
from database import get_db
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = b'\xd6[\xa4S\xb2\xcb\xaa*\xe9/\xef Yc\xab\x92\xbat\xc4\x8aw\x86\xe5['

@app.teardown_appcontext
def close_db(error):
    if 'postgres_db_conn' in g:
        g.postgres_db_conn.close()

def get_current_user():
    user_result = None
    if 'user' in session:
        user = session['user']
    
        db = get_db()
        cur = db.cursor()
        cur.execute('select id, name, password, expert, admin from users where name = %s', (user, ))
        user_result = cur.fetchone()

    return user_result

@app.route('/')
def index():
    user = get_current_user()
    db = get_db()
    cur = db.cursor()

    cur.execute('select questions.id, questions.question_text, askers.name as asker, experts.name as expert from questions join users as askers on askers.id = questions.asked_by_id join users as experts on experts.id = questions.expert_id where questions.answer_text is not null')
    questions_results = cur.fetchall()

    return render_template('home.html', user=user, questions=questions_results)

@app.route('/register', methods=['GET', 'POST'])
def register():
    user = get_current_user()

    if request.method == 'POST':
        db = get_db()
        cur = db.cursor()

        cur.execute('select id from users where name = %s', (request.form['name'], ))
        existing_user = cur.fetchone()

        if existing_user:
            return render_template('register.html', user=user, error='User already exists!')

        hashed_password = generate_password_hash(request.form['password'], method='sha256')
        cur.execute('insert into users (name, password, expert, admin) values (%s, %s, %s, %s)', (request.form['name'], hashed_password, 'False', 'False', ))

        session['user'] = request.form['name']
        return redirect(url_for('index'))

    return render_template('register.html', user=user)

@app.route('/login', methods=['GET', 'POST'])
def login():
    user = get_current_user()
    error = None

    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']

        db = get_db()
        cur = db.cursor()
        cur.execute('select id, name, password from users where name = %s', (name, ))
        user_result = cur.fetchone()
        
        if user_result:

            if check_password_hash(user_result['password'], password):
                session['user'] = user_result['name']
                return redirect(url_for('index'))
            else:
                error = "password is incorrect"
        else:
            error = "username is incorrect"
    
    return render_template('login.html', user=user, error=error)

@app.route('/question/<question_id>') 
def question(question_id):
    user = get_current_user()
    db = get_db()
    cur = db.cursor()

    cur.execute('select questions.id, questions.question_text, questions.answer_text, askers.name as asker, experts.name as expert from questions join users as askers on askers.id = questions.asked_by_id join users as experts on experts.id = questions.expert_id where questions.id = %s', (question_id, ))
    question_result = cur.fetchone()

    return render_template('question.html', user=user, question=question_result)

@app.route('/answer/<question_id>', methods=['GET', 'POST'])
def answer(question_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['expert']:
        return redirect(url_for('index'))
    
    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        cur.execute('update questions set answer_text = %s where id = %s', (request.form['answer'], question_id, ))
        return redirect(url_for('unanswered'))

    cur.execute('select id, question_text from questions where id = %s', (question_id, ))
    question_result = cur.fetchone()

    return render_template('answer.html', user=user, question=question_result)

@app.route('/ask', methods=['GET', 'POST'])
def ask():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))

    db = get_db()
    cur = db.cursor()

    if request.method == 'POST':
        cur.execute('insert into questions (question_text, asked_by_id, expert_id) values (%s, %s, %s)', (request.form['question'], user['id'], request.form['expert'], ))
        return redirect(url_for('index'))

    cur.execute('select id, name from users where expert = True')
    expert_results = cur.fetchall()

    return render_template('ask.html', user=user, experts=expert_results)

@app.route('/unanswered')
def unanswered():
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['expert']:
        return redirect(url_for('index'))
    
    db = get_db()
    cur = db.cursor()

    cur.execute('select questions.id, questions.question_text, users.name from questions join users on users.id = questions.asked_by_id where questions.answer_text is null and questions.expert_id = %s', (user['id'], ))
    question_results = cur.fetchall()

    return render_template('unanswered.html', user=user, questions=question_results)

@app.route('/users')
def users():
    user = get_current_user()

    if not user:
        return redirect(url_for('login'))
    if not user['admin']:
        return redirect(url_for('index'))

    db = get_db()
    cur = db.cursor()
    cur.execute('select id, name, expert, admin from users')
    user_results = cur.fetchall()

    return render_template('users.html', user=user, users=user_results)

@app.route('/promote/<user_id>')
def promote(user_id):
    user = get_current_user()
    if not user:
        return redirect(url_for('login'))
    if not user['admin']:
        return redirect(url_for('index'))

    db = get_db()
    cur = db.cursor()
    cur.execute('update users set expert = True where id = %s', (user_id, ))
    return redirect(url_for('users'))

@app.route('/logout')
def logout():
    user = get_current_user()

    session.pop('user', None)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)