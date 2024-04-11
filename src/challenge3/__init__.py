from datetime import datetime
import functools
from flask import Flask, g, request, abort
from src import DB_FILE, CURRENT_MODEL_PATH, CSV_FILE, BACKUP_MODELS_PATH
from src.challenge2.core import Model
import pandas as pd
import sqlite3

def create_app(config: dict = {}):

    app = Flask(__name__)

    with app.app_context():
        app.config.update(config)
        if not app.config['TESTING']:
            app.config['DB_FILE'] = DB_FILE
            app.config['CURRENT_MODEL_PATH'] = CURRENT_MODEL_PATH
            app.config['BACKUP_MODELS_PATH'] = BACKUP_MODELS_PATH

    
    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            app.config['DB_FILE'].parent.mkdir(parents=True, exist_ok=True)
            db = g._database = sqlite3.connect(app.config['DB_FILE'])
        return db
    
    def get_data(rvs):
        return [{k:v for k, v in zip(['id', *Model.features, 'price'], rv)} for rv in rvs]

    def get_model() -> Model:
        # if model hasn't already loaded, load it.
        model = getattr(g, '_model', None)
        if model is None:
            model = g._model = Model.load(app.config['CURRENT_MODEL_PATH'])
        return model
    
    with app.app_context():
        # create and populate database if not exists, then create the model.
        if not app.config['DB_FILE'].exists():
            print('Init database from csv file ... ')
            data = pd.read_csv(CSV_FILE)
            data.to_sql('diamonds', con=get_db(), if_exists='fail', index=False)
            model = Model.build(data)
            model.save(app.config['CURRENT_MODEL_PATH'])

    def validator(*params: tuple[str, str | int | float]):
        def _wrapper(func):
            @functools.wraps(func)
            def wrapper():
                if not request.is_json:
                    abort(415, description=f'require json/application')
                for param, _type in params:
                    if param not in request.json:
                        abort(400, description=f'{param} not found')
                    if not isinstance(request.json[param], _type):
                        abort(400, description=f'{param} is {type(request.json[param])} instead {_type}.')
                return func()
            return wrapper
        return _wrapper

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
        values = [body[k] for k in [*Model.features[:7], 'price', *Model.features[7:]] ]
        db = get_db()
        cur = db.execute(query, values)
        body['id'] = cur.lastrowid
        cur.close()
        db.commit()
        return body, 201, {'Content-Type': 'application/json'}

    @app.get("/diamond/read")
    @validator(('id', int))
    def read_diamond():
        query = """
            SELECT rowid, *
            FROM diamonds 
            WHERE rowid = ?;
        """
        body = request.get_json()
        db = get_db()
        cur = db.execute(query, (body['id'], ))
        rvs = cur.fetchall()
        cur.close()
        if len(rvs) == 0:
            return abort(404, description=f"id {body['id']} not found")
        rec = get_data(rvs)[0]
        return rec, 200, {'Content-Type': 'application/json'}

    @app.get("/diamond/table")
    @validator()
    def table_diamond():
        query = """
            SELECT rowid, *
            FROM diamonds 
        """
        db = get_db()
        cur = db.execute(query)
        rvs = cur.fetchall()
        cur.close()
        recs = get_data(rvs)
        return recs, 200, {'Content-Type': 'application/json'}

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
        values = [body[k] for k in [*Model.features[:7], 'price', *Model.features[7:], 'id'] ]
        db = get_db()
        cur = db.execute(query, values)
        cur.close()
        if cur.rowcount == 0:
            return abort(404, description=f"id {body['id']} not found")
        db.commit()
        return body, 200, {'Content-Type': 'application/json'}

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
        cur.close()
        if cur.rowcount == 0:
            return abort(404, description=f"id {body['id']} not found")
        if not app.config['TESTING']:
            db.commit()
        return body, 200, {'Content-Type': 'application/json'}

    @app.put("/model/update")
    @validator()
    def update_model():
        get_model().save(app.config['BACKUP_MODELS_PATH'], filename=datetime.now().strftime('%y%m%d%H%M%S')) # save current model with datetime in /backup_models
        query = """
            SELECT *
            FROM diamonds 
        """
        data = pd.read_sql(query, con=get_db())
        new_model = Model.build(data) # build new model with overall data
        new_model.save(app.config['CURRENT_MODEL_PATH']) # overwrite current model file
        g._model = None # next time get_model() execution'll load new model
        return {'msg': 'Model updated.'}, 200, {'Content-Type': 'application/json'}

    @app.get("/model/predict")
    @validator(
        ('carat', float),
        ('cut', str), 
        ('color', str), 
        ('clarity', str), 
        ('depth', float), 
        ('table', float), 
        ('x', float), 
        ('y', float), 
        ('z', float)
    )
    def predict():
        body = request.get_json()
        values = pd.DataFrame([map(body.get, Model.features)], columns=Model.features)
        data = {"price": get_model().predict(values).item()}
        return data, 200, {'Content-Type': 'application/json'}

    @app.teardown_appcontext
    def close_connection(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

    return app
