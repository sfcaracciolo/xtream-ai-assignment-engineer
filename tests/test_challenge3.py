import pytest
from src.challenge3 import create_app
from src import ROOT_PATH 

@pytest.fixture()
def app():
    app = create_app( config = {
            'TESTING':True,
            'DB_FILE': ROOT_PATH / 'tests_temp' / 'database.sqlite',
            'CURRENT_MODEL_PATH': ROOT_PATH / 'tests_temp' ,
            'BACKUP_MODELS_PATH': ROOT_PATH / 'tests_temp' / 'backup_models'
        }
    )
    yield app

@pytest.fixture()
def client(app):
    return app.test_client()

@pytest.fixture()
def vars():
    FEATURES = {
        'carat' : 1.2,
        'cut' : 'Fair',
        'color' : 'G',
        'clarity' : 'VS2',
        'depth' : 2.,
        'table' : 2.,
        'x' : 2.,
        'y' : 2.,
        'z' : 2.,
    }

    ID = { 'id' : 3 }

    PRICE = { 'price' : 2200. }
    return ID, PRICE, FEATURES 

@pytest.fixture()
def runner(app):
    return app.test_cli_runner()

def test_diamond_create(client, vars):
    ID, PRICE, FEATURES = vars

    res = client.post("/diamond/create", json= PRICE | FEATURES)
    d = res.json.copy()
    assert res.status_code == 201
    assert d.pop('id')
    assert d == PRICE | FEATURES

def test_diamond_read(client, vars):
    ID, PRICE, FEATURES = vars

    res = client.get("/diamond/read", json=ID)
    d = res.json.copy()
    assert res.status_code == 200
    assert res.is_json
    assert d.pop('id') == ID['id']
    assert d.keys() == (PRICE | FEATURES).keys()

def test_diamond_table(client, vars):
    ID, PRICE, FEATURES = vars
    
    res = client.get("/diamond/table", json={})
    assert res.status_code == 200
    assert res.is_json
    for row in res.json:
        assert row.keys() == (ID | FEATURES | PRICE).keys()

def test_diamond_update(client, vars):
    ID, PRICE, FEATURES = vars
    
    res = client.put("/diamond/update", json= ID | PRICE | FEATURES)
    assert res.status_code == 200
    assert res.is_json
    assert res.json == ID | PRICE | FEATURES

def test_diamond_delete(client, vars):
    ID, PRICE, FEATURES = vars
    
    res = client.delete("/diamond/delete", json=ID)
    assert res.status_code == 200
    assert res.is_json
    assert res.json == ID

def test_model_predict(client, vars):
    ID, PRICE, FEATURES = vars
    
    res = client.get("/model/predict", json=FEATURES)
    assert res.status_code == 200
    assert res.is_json
    assert res.json.keys() == PRICE.keys()

def test_model_update(client, vars):
    ID, PRICE, FEATURES = vars
    
    res = client.put("/model/update", json={})
    assert res.status_code == 200
    assert res.is_json
    assert res.json == {'msg': 'Model updated.'}

def test_json_application(client, vars):
    """
    API returns 415 if content-type isn't json/application
    
    """
    ID, PRICE, FEATURES = vars
    
    assert client.post("/diamond/create", data={}).status_code == 415
    assert client.get("/diamond/table", data={}).status_code == 415
    assert client.get("/diamond/read", data={}).status_code == 415
    assert client.put("/diamond/update", data={}).status_code == 415
    assert client.delete("/diamond/delete", data={}).status_code == 415
    assert client.get("/model/predict", data={}).status_code == 415
    assert client.put("/model/update", data={}).status_code == 415

def test_missing_key(client, vars):
    """
    API returns 400 if any json key is missing
    
    """
    ID, PRICE, FEATURES = vars
    
    assert client.post("/diamond/create", json={}).status_code == 400
    assert client.get("/diamond/read", json={}).status_code == 400
    assert client.put("/diamond/update", json={}).status_code == 400
    assert client.delete("/diamond/delete", json={}).status_code == 400
    assert client.get("/model/predict", json={}).status_code == 400

def test_json_types(client, vars):
    """
    API returns 400 if any type is incorrect
    
    """
    ID, PRICE, FEATURES = vars
    
    PRICE['price'] = 'string' # bad type
    assert client.post("/diamond/create", json=PRICE | FEATURES).status_code == 400
    assert client.put("/diamond/update", json=ID | PRICE | FEATURES).status_code == 400

    ID['id'] = 3.3 # bad type
    assert client.get("/diamond/read", json=ID).status_code == 400
    assert client.delete("/diamond/delete", json=ID).status_code == 400

    FEATURES['cut'] = 123 # bad type
    assert client.get("/model/predict", json=FEATURES).status_code == 400


def test_missing_id(client, vars):
    """
    API returns 404 if id is not found.
    
    """
    ID, PRICE, FEATURES = vars
    
    ID['id'] = 6000 # id out of db
    assert client.get("/diamond/read", json=ID).status_code == 404
    assert client.put("/diamond/update", json= ID | PRICE | FEATURES).status_code == 404
    assert client.delete("/diamond/delete", json=ID).status_code == 404