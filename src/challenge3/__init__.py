import functools
from flask import Flask, g, request, abort, jsonify
from src import DB_FILE, MODEL_FILE, CSV_FILE
from src.challenge2 import core
from src.challenge3.database import get_db, get_data 


def create_app():
    app = Flask(__name__)

    # create and populate database if not exists, then create the model.
    if not DB_FILE.exists():
        with app.app_context():
            data = core.load_csv(CSV_FILE)
            data.to_sql('diamonds', con=get_db(), if_exists='fail', index=False)
            model = core.build_model(data, MODEL_FILE)

    # if model hasn't already created, load it.
    if 'model' not in globals().keys():
        model = core.load_model(MODEL_FILE)

    def validator(*params: tuple[str, str | int | float]):
        def _wrapper(func):
            @functools.wraps(func)
            def wrapper():
                if not request.is_json:
                    abort(406, description=f'require json/application')
                for param, _type in params:
                    if param not in request.json:
                        abort(400, description=f'{param} not found')
                    if not isinstance(request.json[param], _type):
                        abort(400, description=f'{param} is {type(request.json[param])} instead {_type}.')
                return func()
            return wrapper
        return _wrapper

    @app.route("/")
    def index():
        return "<p>Hello, World!</p>"

    @app.post("/diamond/create")
    @validator(
        ('carat', float),
        ('cut', str), 
        ('color', str), 
        ('clarity', str), 
        ('depth', float), 
        ('table', float), 
        ('price', float), 
        ('x', float), 
        ('y', float), 
        ('z', float)
    )
    def create_diamond():
        query = """
            INSERT INTO diamonds
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        body = request.get_json()
        values = (
            body['carat'],
            body['cut'],
            body['color'],
            body['clarity'],
            body['depth'],
            body['table'],
            body['price'],
            body['x'],
            body['y'],
            body['z'],
        )
        db = get_db()
        cur = db.execute(query, values)
        cur.close()
        db.commit()
        return [body], 201, {'Content-Type': 'application/json'}

    @app.get("/diamond/read")
    @validator(('id', int))
    def read_diamond():
        query = """
            SELECT *
            FROM diamonds 
            WHERE rowid = ?;
        """
        body = request.get_json()
        db = get_db()
        cur = db.execute(query, (body['id'], ))
        rv = cur.fetchall()
        if len(rv) == 0:
            cur.close()
            return abort(404, description=f"id {body['id']} not found")
        cur.close()
        return get_data(cur, rv), 200, {'Content-Type': 'application/json'}

    @app.get("/diamond/table")
    @validator()
    def table_diamond():
        query = """
            SELECT rowid, *
            FROM diamonds 
        """
        db = get_db()
        cur = db.execute(query)
        rv = cur.fetchall()
        cur.close()
        return get_data(cur, rv), 200, {'Content-Type': 'application/json'}

    @app.put("/diamond/update")
    @validator(
        ('id', int),
        ('carat', float),
        ('cut', str), 
        ('color', str), 
        ('clarity', str), 
        ('depth', float), 
        ('table', float), 
        ('price', float), 
        ('x', float), 
        ('y', float), 
        ('z', float)
    )
    def update_diamond():
        query = """
            UPDATE diamonds
            SET carat = ?,
            cut = ?,
            color = ?,
            clarity = ?,
            depth = ?,
            [table] = ?,
            price = ?,
            x = ?,
            y = ?,
            z = ? 
            WHERE rowid = ?;
        """
        body = request.get_json()
        values = (
            body['carat'],
            body['cut'],
            body['color'],
            body['clarity'],
            body['depth'],
            body['table'],
            body['price'],
            body['x'],
            body['y'],
            body['z'],
            body['id'],
        )
        db = get_db()
        cur = db.execute(query, values)
        if cur.rowcount == 0:
            cur.close()
            return abort(404, description=f"id {body['id']} not found")
        cur.close()
        db.commit()
        return [body], 200, {'Content-Type': 'application/json'}

    @app.delete("/diamond/delete")
    @validator(('id', int))
    def delete_diamond():
        query = """
            DELETE FROM diamonds 
            WHERE rowid = ?
        """
        body = request.get_json()
        db = get_db()
        cur = db.execute(query, (body['id'], ))
        if cur.rowcount == 0:
            cur.close()
            return abort(404, description=f"id {body['id']} not found")
        cur.close()
        db.commit()
        return [body], 200, {'Content-Type': 'application/json'}

    @app.get("/model/predict")
    def predict():
        # by default use current model
        return ""

    @app.route("/model/update")
    def update_model():
        # save current model with timestamp in /backup_models
        # build new model with overall data
        # update current model
        return ""

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    return app
