import os,tempfile
os.environ['DATABASE_PATH']=tempfile.mktemp('.db')
from app import app
from database import init_db,seed_demo_data

def login(c,e,p): return c.post('/api/auth/login',json={'email':e,'password':p}).get_json()['token']
def test_health():
 with app.test_client() as c: assert c.get('/api/health').status_code==200
def test_student():
 with app.app_context(): init_db();seed_demo_data()
 with app.test_client() as c:
  t=login(c,'student@skilltrack.com','student123');r=c.get('/api/courses',headers={'Authorization':f'Bearer {t}'});assert r.status_code==200 and len(r.json)>0
def test_admin():
 with app.app_context(): init_db();seed_demo_data()
 with app.test_client() as c:
  t=login(c,'admin@skilltrack.com','admin123');r=c.post('/api/courses',headers={'Authorization':f'Bearer {t}'},json={'name':'React','description':'React course','total_classes':12,'quiz_interval':4});assert r.status_code==201
