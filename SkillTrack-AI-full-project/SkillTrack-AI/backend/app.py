import os,json,requests,jwt
from datetime import datetime,timedelta
from functools import wraps
from dotenv import load_dotenv
from flask import Flask,request,jsonify,g
from flask_cors import CORS
from werkzeug.security import generate_password_hash,check_password_hash
from database import get_db,init_db,seed_demo_data
load_dotenv(); app=Flask(__name__); CORS(app)
SECRET=os.getenv('JWT_SECRET','dev-secret-change-me'); OR_KEY=os.getenv('OPENROUTER_API_KEY',''); OR_MODEL=os.getenv('OPENROUTER_MODEL','openai/gpt-4o-mini')
def token(u): return jwt.encode({'user_id':u['id'],'role':u['role'],'exp':datetime.utcnow()+timedelta(hours=12)},SECRET,algorithm='HS256')
def auth(role=None):
 def deco(fn):
  @wraps(fn)
  def w(*a,**kw):
   h=request.headers.get('Authorization','')
   if not h.startswith('Bearer '): return jsonify(error='Authentication required'),401
   try: p=jwt.decode(h[7:],SECRET,algorithms=['HS256'])
   except jwt.PyJWTError: return jsonify(error='Invalid or expired token'),401
   u=get_db().execute('SELECT id,name,email,role FROM users WHERE id=?',(p['user_id'],)).fetchone()
   if not u or (role and u['role']!=role): return jsonify(error='Access denied'),403
   g.user=dict(u); return fn(*a,**kw)
  return w
 return deco
@app.get('/api/health')
def health(): return jsonify(status='ok')
@app.post('/api/auth/register')
def register():
 d=request.get_json() or {}; name=d.get('name','').strip(); email=d.get('email','').strip().lower(); pw=d.get('password','')
 if not name or not email or len(pw)<6:return jsonify(error='Name, email and 6+ character password required'),400
 db=get_db()
 if db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone():return jsonify(error='Email already registered'),409
 i=db.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',(name,email,generate_password_hash(pw),'student')).lastrowid;db.commit();u={'id':i,'name':name,'email':email,'role':'student'};return jsonify(token=token(u),user=u),201
@app.post('/api/auth/login')
def login():
 d=request.get_json() or {};u=get_db().execute('SELECT * FROM users WHERE email=?',(d.get('email','').lower(),)).fetchone()
 if not u or not check_password_hash(u['password_hash'],d.get('password','')):return jsonify(error='Invalid email or password'),401
 x={'id':u['id'],'name':u['name'],'email':u['email'],'role':u['role']};return jsonify(token=token(x),user=x)
@app.get('/api/courses')
@auth()
def courses():
 r=get_db().execute('''SELECT c.*,COUNT(DISTINCT e.id) students,COUNT(DISTINCT q.id) quizzes FROM courses c LEFT JOIN enrollments e ON e.course_id=c.id LEFT JOIN quizzes q ON q.course_id=c.id GROUP BY c.id ORDER BY c.id DESC''').fetchall();return jsonify([dict(x) for x in r])
@app.post('/api/courses')
@auth('admin')
def add_course():
 d=request.get_json() or {};db=get_db();i=db.execute('INSERT INTO courses(name,description,total_classes,quiz_interval,level) VALUES(?,?,?,?,?)',(d['name'],d['description'],int(d['total_classes']),int(d.get('quiz_interval',5)),d.get('level','Beginner'))).lastrowid;db.commit();return jsonify(id=i),201
@app.post('/api/courses/<int:cid>/enroll')
@auth()
def enroll(cid):
 db=get_db()
 if db.execute('SELECT id FROM enrollments WHERE student_id=? AND course_id=?',(g.user['id'],cid)).fetchone():return jsonify(error='Already enrolled'),409
 db.execute('INSERT INTO enrollments(student_id,course_id) VALUES(?,?)',(g.user['id'],cid));db.commit();return jsonify(message='Enrolled'),201
@app.get('/api/my-courses')
@auth()
def mycourses():
 r=get_db().execute('''SELECT c.*, (SELECT COUNT(*) FROM attendance a JOIN classes cl ON cl.id=a.class_id WHERE a.student_id=? AND cl.course_id=c.id AND a.status='Present') completed_classes FROM courses c JOIN enrollments e ON e.course_id=c.id AND e.student_id=?''',(g.user['id'],g.user['id'])).fetchall();return jsonify([dict(x) for x in r])
@app.get('/api/courses/<int:cid>/classes')
@auth()
def classes(cid):
 db=get_db();rows=db.execute('SELECT * FROM classes WHERE course_id=? ORDER BY class_number',(cid,)).fetchall();out=[]
 for x in rows:
  y=dict(x);y['completed']=bool(db.execute("SELECT id FROM attendance WHERE student_id=? AND class_id=? AND status='Present'",(g.user['id'],x['id'])).fetchone());out.append(y)
 return jsonify(out)
@app.post('/api/classes/<int:class_id>/complete')
@auth()
def complete(class_id):
 db=get_db();x=db.execute('SELECT * FROM classes WHERE id=?',(class_id,)).fetchone()
 if not x:return jsonify(error='Class not found'),404
 db.execute("INSERT INTO attendance(student_id,class_id,status) VALUES(?,?,'Present') ON CONFLICT(student_id,class_id) DO UPDATE SET status='Present'",(g.user['id'],class_id));db.commit();return jsonify(message='Completed')
@app.get('/api/quizzes')
@auth()
def quizzes():
 db=get_db();rows=db.execute('SELECT q.*,c.name course_name,(SELECT COUNT(*) FROM questions WHERE quiz_id=q.id) question_count FROM quizzes q JOIN courses c ON c.id=q.course_id').fetchall();out=[]
 for q in rows:
  n=db.execute("SELECT COUNT(*) n FROM attendance a JOIN classes cl ON cl.id=a.class_id WHERE a.student_id=? AND cl.course_id=? AND a.status='Present'",(g.user['id'],q['course_id'])).fetchone()['n']; last=db.execute('SELECT percentage FROM quiz_attempts WHERE student_id=? AND quiz_id=? ORDER BY id DESC LIMIT 1',(g.user['id'],q['id'])).fetchone();x=dict(q);x['unlocked']=n>=q['unlock_after_classes'];x['previous_score']=last['percentage'] if last else None;out.append(x)
 return jsonify(out)
@app.post('/api/quizzes')
@auth('admin')
def add_quiz():
 d=request.get_json() or {};db=get_db();i=db.execute('INSERT INTO quizzes(course_id,title,unlock_after_classes,duration_minutes,pass_percentage) VALUES(?,?,?,?,?)',(int(d['course_id']),d['title'],int(d.get('unlock_after_classes',5)),int(d.get('duration_minutes',10)),int(d.get('pass_percentage',50)))).lastrowid;db.commit();return jsonify(id=i),201
@app.post('/api/quizzes/<int:qid>/questions')
@auth('admin')
def add_question(qid):
 d=request.get_json() or {};db=get_db();i=db.execute('INSERT INTO questions(quiz_id,question,option_a,option_b,option_c,option_d,correct_answer,marks,difficulty,topic) VALUES(?,?,?,?,?,?,?,?,?,?)',(qid,d['question'],d['option_a'],d['option_b'],d['option_c'],d['option_d'],d['correct_answer'],int(d.get('marks',1)),d.get('difficulty','Medium'),d.get('topic','General'))).lastrowid;db.commit();return jsonify(id=i),201
@app.get('/api/quizzes/<int:qid>')
@auth()
def quiz(qid):
 db=get_db();q=db.execute('SELECT q.*,c.name course_name FROM quizzes q JOIN courses c ON c.id=q.course_id WHERE q.id=?',(qid,)).fetchone()
 if not q:return jsonify(error='Quiz not found'),404
 n=db.execute("SELECT COUNT(*) n FROM attendance a JOIN classes cl ON cl.id=a.class_id WHERE a.student_id=? AND cl.course_id=? AND a.status='Present'",(g.user['id'],q['course_id'])).fetchone()['n']
 if g.user['role']!='admin' and n<q['unlock_after_classes']:return jsonify(error=f"Complete {q['unlock_after_classes']} classes first"),403
 qs=db.execute('SELECT id,question,option_a,option_b,option_c,option_d,marks,difficulty,topic FROM questions WHERE quiz_id=?',(qid,)).fetchall();x=dict(q);x['questions']=[dict(z) for z in qs];return jsonify(x)
@app.post('/api/quizzes/<int:qid>/submit')
@auth()
def submit(qid):
 d=request.get_json() or {};db=get_db();qs=db.execute('SELECT * FROM questions WHERE quiz_id=?',(qid,)).fetchall();total=sum(x['marks'] for x in qs);score=0;ans=[]
 for q in qs:
  s=d.get('answers',{}).get(str(q['id']));ok=s==q['correct_answer'];score+=q['marks'] if ok else 0;ans.append((q['id'],s or '',int(ok)))
 pct=round(score*100/total,2) if total else 0;i=db.execute('INSERT INTO quiz_attempts(student_id,quiz_id,score,total_marks,percentage) VALUES(?,?,?,?,?)',(g.user['id'],qid,score,total,pct)).lastrowid
 for qid2,s,ok in ans:db.execute('INSERT INTO answers(attempt_id,question_id,selected_answer,is_correct) VALUES(?,?,?,?)',(i,qid2,s,ok))
 db.commit();return jsonify(attempt_id=i,score=score,total_marks=total,percentage=pct)
@app.get('/api/leaderboard/<int:cid>')
@auth()
def leaderboard(cid):
 r=get_db().execute('''SELECT u.name,ROUND(AVG(a.percentage),2) average_score,COUNT(a.id) attempts FROM quiz_attempts a JOIN users u ON u.id=a.student_id JOIN quizzes q ON q.id=a.quiz_id WHERE q.course_id=? GROUP BY a.student_id ORDER BY average_score DESC LIMIT 50''',(cid,)).fetchall();return jsonify([dict(x,rank=i) for i,x in enumerate(r,1)])
@app.get('/api/analytics/me')
@auth()
def analytics():
 db=get_db();s=db.execute('SELECT q.title,a.percentage FROM quiz_attempts a JOIN quizzes q ON q.id=a.quiz_id WHERE a.student_id=? ORDER BY a.id',(g.user['id'],)).fetchall();t=db.execute('SELECT q.topic,ROUND(AVG(CASE WHEN a.is_correct=1 THEN 100.0 ELSE 0 END),2) score FROM answers a JOIN questions q ON q.id=a.question_id JOIN quiz_attempts x ON x.id=a.attempt_id WHERE x.student_id=? GROUP BY q.topic',(g.user['id'],)).fetchall();return jsonify(quiz_scores=[dict(x) for x in s],topic_scores=[dict(x) for x in t])
@app.get('/api/admin/analytics')
@auth('admin')
def admin_analytics():
 db=get_db();counts={k:db.execute(q).fetchone()['n'] for k,q in {'students':"SELECT COUNT(*) n FROM users WHERE role='student'",'courses':'SELECT COUNT(*) n FROM courses','quizzes':'SELECT COUNT(*) n FROM quizzes','questions':'SELECT COUNT(*) n FROM questions','attempts':'SELECT COUNT(*) n FROM quiz_attempts'}.items()};rows=db.execute('''SELECT c.name,ROUND(AVG(a.percentage),2) average_score FROM courses c LEFT JOIN quizzes q ON q.course_id=c.id LEFT JOIN quiz_attempts a ON a.quiz_id=q.id GROUP BY c.id''').fetchall();return jsonify(counts=counts,courses=[dict(x) for x in rows])
def openrouter(prompt):
 if not OR_KEY: return None
 r=requests.post('https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':f'Bearer {OR_KEY}','Content-Type':'application/json','X-Title':'SkillTrack AI'},json={'model':OR_MODEL,'messages':[{'role':'user','content':prompt}]},timeout=60);r.raise_for_status();return r.json()['choices'][0]['message']['content']
@app.post('/api/ai/coach')
@auth()
def coach():
 a=analytics().get_json();x=openrouter(f'You are an educational coach. Analyze quiz scores {a["quiz_scores"]} and topic scores {a["topic_scores"]}. Give strong topics, weak topics, and 3 practical next actions.')
 return jsonify(message=x or 'AI is not configured. Add OPENROUTER_API_KEY to backend/.env.')
@app.post('/api/ai/generate-questions')
@auth('admin')
def generate():
 d=request.get_json() or {};n=min(max(int(d.get('count',5)),1),20);topic=d.get('topic','Python');x=openrouter(f'Generate {n} MCQs on {topic}. Return ONLY JSON array. Fields: question, option_a, option_b, option_c, option_d, correct_answer (A/B/C/D), topic.')
 if not x:return jsonify(error='Configure OPENROUTER_API_KEY first'),400
 try:return jsonify(questions=json.loads(x.replace('```json','').replace('```','').strip()))
 except Exception:return jsonify(error='AI returned invalid JSON',raw=x),502
@app.teardown_appcontext
def close(e=None):
 if hasattr(g,'db'):g.db.close()
if __name__=='__main__':
 with app.app_context():init_db();seed_demo_data()
 app.run(debug=True,port=5000)
