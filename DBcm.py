import rethinkdb as db

class UseDatabase:
    def __init__(self, config: dict) -> None:
        self.config = config
        self.tasks = None
        self.task = None
        self.val = None
        self.ins = None
        self.upd = None
        self.dell = None
        self.count = None
        self.countal = None
        self.conn = None

    def __enter__(self):
        """Подключение к базе данных RethinkDB"""
        self.conn = db.connect(**self.config).repl()
        return self

    def gettasks(self, table):
        """Получение всех записей из таблицы базы данных"""
        self.tasks = list(db.table(table).run())
        return self.tasks

    def gettask(self, table, req):
        """Получение записей из таблицы базы данных по определенному ID"""
        self.task = db.table(table).get(req).run()
        return self.task

    def getval(self, id, table):
        """Получение только значений, без ключей из таблицы базы данных
        по определенному ID"""
        self.val = list(db.table(table).get(id).values().run())
        return self.val

    def insert(self, table, json):
        """Функция добавления новой записи в таблицe БД"""
        self.ins = db.table(table).insert(json).run()
        return self.ins

    def updat(self, table, id, json):
        """Функция обновления записи в таблице БД по определнному ID"""
        self.upd = db.table(table).get(id).update(json).run()
        return self.upd

    def delltask(self, table, req):
        """Функция удаления записи в таблице БД по определнному ID"""
        self.dell = db.table(table).get(req).delete().run()
        return self.dell

    def countid(self, table, req):
        """Функция определения записи в таблице БД по определнному ID
        0 - записи нет, 1 - запись имеется"""
        self.count = db.table(table).filter({'id': req}).count().run()
        return self.count

    def countall(self, table):
        """Функция определения количества записи в таблице БД"""
        self.countal = db.table(table).count().run()
        return self.countal

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Отключение от БД"""
        self.conn.close()
