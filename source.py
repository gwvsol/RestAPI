from flask import Flask, jsonify, abort, make_response, request, render_template
from flask import redirect, session
from flask_httpauth import HTTPBasicAuth
from functools import wraps
import datetime as time
import json
from DBcm import UseDatabase
from hashlib import md5

app = Flask(__name__)
auth = HTTPBasicAuth()


"""Определяем параметры подключения к БД"""
app.config['dbconf'] = {'host': 'localhost',
                        'port': '28015',
                        'db': 'log', }

"""Определяем таблицы в БД"""
app.config['db_tab'] = {'t1': 'api',
                         't2': 'logs',
                         't3': 'users', }

app.config['form'] = { 'title': 'Мониторинг работы',
                       'hd_title': 'Мониторинг работы ферм',
                       'tb_head': ('Name', 'GPU', 'Hashrate', 'Power', 'Temp', \
                       'Fan', 'UpTime', 'MinerUp'),
                       'request': ['id', 'totalgpu', 'totalhashrate', 'totalpower', \
                       'maxtemp', 'maxfan', 'sysuptime', 'uptimeminer'],}

"""Определяем время проверки свыше 45сек, не доступна и ждем доступности,
свяше 600 сек, нет надежды на доступность фермы, удаляем запись о ней из БД"""
app.config['time'] = {'min': 45,
                      'max': 600, }

"""Секретный ключ для системы аунтфикации"""
app.secret_key = '4d7f29fcddd2d82a537de4c35d500ed7'


#Функция преобразования пароля и логина в хеш MD5
def setpasswd(login:str, passw:str) -> str:
    return str(md5(str(passw+login).lower().encode('utf-8')).hexdigest())


#Функция извлечения для извления хеша MD5 из БД и сравнения его с хешем логина и пароля
def return_pw(db_conf, db_table, login, passwd):
    with UseDatabase(db_conf) as ps: #Перебираем в БД логины
        for f in range(ps.countall(db_table)): #При совпедении проверяем пароль
            if ps.gettasks(db_table)[f]['user'] == login.lower():
                if ps.gettasks(db_table)[f]['pass'] == \
                setpasswd(login.lower(), passwd): #При совпедении пароля, возвращаем пароль из БД
                    return ps.gettasks(db_table)[f]['pass']
        return None #В противном случае возращаем None


#Декоратор для формы Login и для доступа к странице мониторинга
def check_login(func):
   @wraps(func)
   def wrapper(*arg, **kwargs):
      if 'login' in session:
           return func(*arg, **kwargs)
      return redirect('/login')
   return wrapper


@auth.verify_password
#Функция проверки подлинности для API интерфейса
def verify_password(username, password):
    return return_pw(app.config['dbconf'], app.config['db_tab']['t3'], username, password)


@auth.error_handler
def unauthorized():
#    """Возврат 403 вместо 401, чтобы запретить браузерам отображать диалоговое
#     окно проверки подлинности по умолчанию"""
    return make_response(jsonify( { 'error': 'UnauthorizedAccess' } ), 403)


@app.errorhandler(400)
def bad_request(error):
    """Ответ при неправильном запросе"""
    return make_response(jsonify({'error': 'BadRequest'}), 400)


@app.errorhandler(404)
def not_found(error):
    """Ответ при отсутствии данных в базе"""
    return make_response(jsonify({'error': 'NotFound'}), 404)


@app.route('/login')
def login():
    title = 'Мониторинг работы'
    hd_title = 'Мониторинг работы ферм'
    return render_template('login.html', the_title = app.config['form']['title'],
                            header_title = app.config['form']['hd_title'])


@app.route('/pass', methods=['POST'])
def pass_chesk():
    if return_pw(app.config['dbconf'], app.config['db_tab']['t3'], \
    request.form['login'], request.form['passwd']) is not None:
        session['login'] = True
        return redirect('/')
    else: return redirect('/login')


@app.route('/logout')
@check_login
def logout():
    if 'login' in session:
        session.pop('login')
    return render_template('logout.html', the_title = app.config['form']['title'],
                            header_title = app.config['form']['hd_title'])

@app.route('/')
@check_login
def get_main():
    """Формирование главной страници сервиса"""
    #Определяем переменные
    tb_data = []
    #Подключаемся к БД получаем общее количесво записей и сами записи из таблици
    with UseDatabase(app.config['dbconf']) as all:
        # Формирум список ID и сортируем его
        id = [int(all.gettasks(app.config['db_tab']['t1'])[c]['id']) for c in \
        range(all.countall(app.config['db_tab']['t1']))] #Определяем пустой список
        id.sort()
        for i in id:
            #Определяем время последнего обновления базы
            delta = time.datetime.now() - time.datetime.strptime(all.gettask(app.config['db_tab']['t2'], \
            str(i))['updata'], "%Y-%m-%d %X")
            if delta.seconds > app.config['time']['min'] and delta.seconds < app.config['time']['max']:
                json_data = json.loads(json.dumps({'maxfan': '--', 'uptimeminer': 'NoWork', \
                'miner': '----', 'maxtemp': '--', 'totalhashrate': '--', 'totalpower': '--', \
                'method': 'stats', 'id': str(i), 'sysuptime': 'NotAvailable', 'name': '--', \
                'totalgpu': '--', 'jsonrpc': '2.0'}))
                all.updat(app.config['db_tab']['t1'], str(i), json_data)
            if delta.seconds > app.config['time']['max']:
                all.delltask(app.config['db_tab']['t1'], str(i))
                all.delltask(app.config['db_tab']['t2'], str(i))
        id = [int(all.gettasks(app.config['db_tab']['t1'])[c]['id']) \
        for c in range(all.countall(app.config['db_tab']['t1']))] #Определяем список
        id.sort()
        """Делаем из списка, список списков и добавляем в него записи в соответствии
        c данными в переменной request"""
        for i in id:
            tb_data.append([])      #Добавляем в список, новый список
            for req in app.config['form']['request']:     #Выбираем из полученных из базы данных,
                                    #нужные в соответствии с переменной request
                tb_data[-1].append(all.gettask(app.config['db_tab']['t1'], str(i))[req])
    """Отправляем переменные на web страницу"""
    return render_template('data.html', the_title = app.config['form']['title'],
                            header_title = app.config['form']['hd_title'],
                            table_head = app.config['form']['tb_head'],
                            table_data = tb_data)


@app.route('/api/v1.0', methods=['GET'])
#@auth.login_required
def get_tasks():
    """Обрабатываем запрос GET и выдаем в JSON все данные из базы"""
    #Подключаемся к базе
    with UseDatabase(app.config['dbconf']) as all:
        all_db = all.gettasks(app.config['db_tab']['t1'])
    #Отвечаем на запрос
    return jsonify({'info': all_db})


@app.route('/api/v1.0/<int:task_id>', methods=['GET'])
#@auth.login_required
def get_task(task_id):
    """Обрабатываем запрос GET и выдаем в JSON данные из базы по определенному ID"""
    #Подключаемся к базе
    with UseDatabase(app.config['dbconf']) as task:
        #Проверяем имеется ли запись с нужным ID
        if task.countid(app.config['db_tab']['t1'], str(task_id)) == 0:
            #Если записи нет, отвечаем, что запись отсутствует
            abort(404)
        #Если запись имеется, отвечаем на запрос
        taskreq = task.gettask(str(task_id), app.config['db_tab']['t1'])
    return jsonify({'info': taskreq})


@app.route('/api/v1.0/<int:task_id>', methods=['DELETE'])
@auth.login_required
def del_task(task_id):
    """Обрабатываем запрос DELETE и удаляем данные из базы по определенному ID"""
    #Подключемся к базе
    with UseDatabase(app.config['dbconf']) as dell:
        #Проверяем имеется ли запись с нужным ID для удаления
        if dell.countid(app.config['db_tab']['t1'], str(task_id)) == 0:
            #Если записи нет, отвечаем, что запись отсутствует
            abort(404)
        #Если запись имеется, удаляем ее
        dell.delltask(app.config['db_tab']['t1'], str(task_id))
        dell.delltask(app.config['db_tab']['t2'], str(task_id))
    return jsonify({'request': 'DeleteData'})


@app.route('/api/v1.0', methods=['POST'])
@auth.login_required
def create_task():
    """Обрабатываем запрос POST для обноления данныx в базе"""
    #Проверяем запрос на определенные параметры, если отсутствуют, ошибка 400
    if not request.json or not 'id' in request.json or not 'method' in request.json \
    or not 'jsonrpc' in request.json:
        abort(400)
    json_log = json.loads(json.dumps({'id': request.json['id'], \
    'updata': time.datetime.now().strftime("%Y-%m-%d %X")}))
    #Подключаемся к базе данных
    with UseDatabase(app.config['dbconf']) as ins:
        #Определяем, имеется ли запись с присланным ID в базе
        if ins.countid(app.config['db_tab']['t1'], request.json['id']) == 0:
            #Если записи нет, добавляем новую
            ins.insert(app.config['db_tab']['t1'], request.json)
            ins.insert(app.config['db_tab']['t2'], json_log) #Пишем лог в базу, о времени обновления записи
            return jsonify({'request': 'InsertData'}), 201
        else:
            #Если запись имеется, обноляем
            ins.updat(app.config['db_tab']['t1'], request.json['id'], request.json)
            ins.updat(app.config['db_tab']['t2'], request.json['id'], json_log) #Пишем лог в базу, о времени обновления записи
            return jsonify({'request': 'UpdateData'}), 201


if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5000', debug=True)
