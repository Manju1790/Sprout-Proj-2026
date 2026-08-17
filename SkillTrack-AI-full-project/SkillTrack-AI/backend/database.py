import os, sqlite3
from flask import g
DB_PATH=os.getenv('DATABASE_PATH','skilltrack.db')
def get_db():
    if 'db' not in g:
        g.db=sqlite3.connect(DB_PATH); g.db.row_factory=sqlite3.Row; g.db.execute('PRAGMA foreign_keys=ON')
    return g.db
def init_db():
    get_db().executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,email TEXT UNIQUE NOT NULL,password_hash TEXT NOT NULL,role TEXT NOT NULL DEFAULT 'student');
    CREATE TABLE IF NOT EXISTS courses(id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL,description TEXT NOT NULL,total_classes INTEGER NOT NULL,quiz_interval INTEGER NOT NULL DEFAULT 5,level TEXT NOT NULL DEFAULT 'Beginner');
    CREATE TABLE IF NOT EXISTS enrollments(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,course_id INTEGER,registered_at TEXT DEFAULT CURRENT_TIMESTAMP,UNIQUE(student_id,course_id),FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS classes(id INTEGER PRIMARY KEY AUTOINCREMENT,course_id INTEGER,class_number INTEGER,title TEXT,topic TEXT,FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS attendance(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,class_id INTEGER,status TEXT,UNIQUE(student_id,class_id),FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(class_id) REFERENCES classes(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS quizzes(id INTEGER PRIMARY KEY AUTOINCREMENT,course_id INTEGER,title TEXT,unlock_after_classes INTEGER DEFAULT 5,duration_minutes INTEGER DEFAULT 10,pass_percentage INTEGER DEFAULT 50,FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS questions(id INTEGER PRIMARY KEY AUTOINCREMENT,quiz_id INTEGER,question TEXT,option_a TEXT,option_b TEXT,option_c TEXT,option_d TEXT,correct_answer TEXT,marks INTEGER DEFAULT 1,difficulty TEXT DEFAULT 'Medium',topic TEXT DEFAULT 'General',FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS quiz_attempts(id INTEGER PRIMARY KEY AUTOINCREMENT,student_id INTEGER,quiz_id INTEGER,score INTEGER,total_marks INTEGER,percentage REAL,created_at TEXT DEFAULT CURRENT_TIMESTAMP,FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,FOREIGN KEY(quiz_id) REFERENCES quizzes(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS answers(id INTEGER PRIMARY KEY AUTOINCREMENT,attempt_id INTEGER,question_id INTEGER,selected_answer TEXT,is_correct INTEGER,FOREIGN KEY(attempt_id) REFERENCES quiz_attempts(id) ON DELETE CASCADE,FOREIGN KEY(question_id) REFERENCES questions(id) ON DELETE CASCADE);
    '''); get_db().commit()
def seed_demo_data():
    from werkzeug.security import generate_password_hash
    db=get_db()
    if db.execute('SELECT COUNT(*) n FROM users').fetchone()['n']==0:
        db.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',('Admin','admin@skilltrack.com',generate_password_hash('admin123'),'admin'))
        db.execute('INSERT INTO users(name,email,password_hash,role) VALUES(?,?,?,?)',('Demo Student','student@skilltrack.com',generate_password_hash('student123'),'student'))
    if db.execute('SELECT COUNT(*) n FROM courses').fetchone()['n']==0:
        cid=db.execute('INSERT INTO courses(name,description,total_classes,quiz_interval,level) VALUES(?,?,?,?,?)',('Python Programming','Practical Python from basics to functions and collections.',15,5,'Beginner')).lastrowid
        topics=['Basics','Variables','Operators','Input','Control Flow','Strings','Lists','Tuples','Sets','Dictionaries','Functions','Modules','Files','Exceptions','Mini Project']
        for i,t in enumerate(topics,1): db.execute('INSERT INTO classes(course_id,class_number,title,topic) VALUES(?,?,?,?)',(cid,i,f'Class {i}: {t}',t))
        q1=db.execute('INSERT INTO quizzes(course_id,title,unlock_after_classes) VALUES(?,?,?)',(cid,'Python Quiz 1',5)).lastrowid
        qs=[('Which keyword defines a function?','func','def','function','define','B','Basics'),('Which collection is mutable and ordered?','tuple','set','list','string','C','Lists'),('Which operator is exponentiation?','^','**','//','%%','B','Operators'),('Which statement makes a decision?','if','for','import','print','A','Control Flow'),('Which method adds to a list?','add()','append()','push()','insertEnd()','B','Lists')]
        for q,a,b,c,d,ans,topic in qs: db.execute('INSERT INTO questions(quiz_id,question,option_a,option_b,option_c,option_d,correct_answer,topic) VALUES(?,?,?,?,?,?,?,?)',(q1,q,a,b,c,d,ans,topic))
        q2=db.execute('INSERT INTO quizzes(course_id,title,unlock_after_classes) VALUES(?,?,?)',(cid,'Python Quiz 2',10)).lastrowid
        qs2=[('Which keyword returns a value?','send','return','back','yieldValue','B','Functions'),('Which collection stores unique values?','list','tuple','set','dict','C','Sets'),('Which dictionary method avoids KeyError?','get()','read()','value()','fetch()','A','Dictionaries'),('Which block handles exceptions?','catch','except','error','handle','B','Exceptions'),('Which module reads CSV?','csv','table','datafile','excel','A','Modules')]
        for q,a,b,c,d,ans,topic in qs2: db.execute('INSERT INTO questions(quiz_id,question,option_a,option_b,option_c,option_d,correct_answer,topic) VALUES(?,?,?,?,?,?,?,?)',(q2,q,a,b,c,d,ans,topic))
        sid=db.execute("SELECT id FROM users WHERE email='student@skilltrack.com'").fetchone()['id']; db.execute('INSERT OR IGNORE INTO enrollments(student_id,course_id) VALUES(?,?)',(sid,cid))
    db.commit()
