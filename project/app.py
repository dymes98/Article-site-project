from flask import Flask,render_template,session, request, flash,redirect,url_for,logging
from flask_wtf import FlaskForm
from os import stat
from wtforms import form,StringField,TextAreaField,PasswordField,validators
from sqlalchemy.orm import sessionmaker
from functools import wraps
import datetime, time
import sqlite3

app = Flask(__name__)

conn=sqlite3.connect('DataBase.db')
c=conn.cursor()
c.execute('CREATE TABLE IF NOT EXISTS Users (id INTEGER PRIMARY KEY AUTOINCREMENT,name NVARCHAR(20) , email TEXT , username TEXT , password TEXT)')
c.execute('SELECT * FROM  Users')
if len(c.fetchall())==0 :
    c.execute('INSERT INTO  Users (name,email,username,password) VALUES ("Habiballah Khosravi","habiballah_khosravi@yahoo.com","admin","admin")')
c.execute('CREATE TABLE IF NOT EXISTS Articles(id INTEGER PRIMARY KEY AUTOINCREMENT,title NVARCHAR(100),id_creat INTEGER,writer NVARCHAR(20),body NVARCHAR(100000),create_date TEXT)')

c.execute('CREATE TABLE IF NOT EXISTS Comments (id INTEGER PRIMARY KEY AUTOINCREMENT,id_article INTEGER,comment NVARCHAR(30),id_user INTEGER,username TEXT , create_date TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS Likes (id INTEGER PRIMARY KEY AUTOINCREMENT,id_article INTEGER,id_user INTEGER,username TEXT )')
conn.commit()

create_date='2018-07-05 20:50:27'
title='Structure'
file = open("Explain.dat", "r" )
body=file.read()
file.close()
c.execute('SELECT * FROM  Articles')
if len(c.fetchall())==0 :
    c.execute('INSERT INTO Articles(title,id_creat,body,writer,create_date) VALUES(? , ? , ? , ? , ?)',(title,1,body,'admin',create_date))
conn.commit()
c.close()
conn.close()

@app.route('/')
def home():
    return render_template ('home.html')

@app.route('/about')
def about():
    return render_template ('about.html')

@app.route('/articles')
def articles():
    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    c.execute('SELECT * FROM Articles')

    articles=[dict(id=row[0],
                    title=row[1],
                    writer=row[3],
                    body=row[4],
                    username=row[5]) for row in c.fetchall()]
    result_article = len(articles)
    conn.commit()
    if session.get('logged_in') == True :
        id_user=session['id']
        c.execute('SELECT * FROM Likes WHERE id_user=?',[id_user])
        likes=[dict(id=row[0],
                        id_article=row[1],
                        id_user=row[2],
                        username=row[3]) for row in c.fetchall()]
        result_like = len(likes)
        if result_article > 0 :
            return render_template('articles.html' , articles=articles ,likes=likes , result_like=result_like )
        else:
            msg = 'NO Articles Found'
            return render_template('articles.html' , msg=msg)
        conn.commit()
        c.close()
        conn.close()
    elif result_article == 0 :
        error = 'Dont Login'
        msg = 'NO Articles Found'
        return render_template('articles.html' , error=error , msg=msg)
    else:
        error = 'Dont Login'
        return render_template('articles.html' , articles=articles ,error=error)

@app.route('/article/<string:id>/' , methods=['GET','POST'])
def article(id):

    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()

    c.execute('SELECT * FROM Articles WHERE id = ?',[id])
    for row in c.fetchall() :
        id_article=row[0]
        title=row[1]
        writer=row[3]
        body=row[4]
        create_date=row[5]

    c.execute('SELECT * FROM Likes WHERE id_article=?',[id])
    likes=[dict(id=row[0],
                    id_article=row[1],
                    id_user=row[2],
                    username=row[3]) for row in c.fetchall()]
                    
    c.execute('SELECT * FROM Comments WHERE id_article = ?',(id))
    comments=[dict(id=row[0],
                    id_article=row[1],
                    comment=row[2],
                    id_user=row[3],
                    username=row[4],
                    create_date=row[5]) for row in c.fetchall()]

    if session.get('logged_in') == True :
        id_user=session['id']
        username=session['username']

        c.execute('SELECT * FROM Likes WHERE id_article=? AND id_user=?',[id,id_user])
        liked=len(c.fetchall())

        if request.method == 'POST' :
            comment=request.form['comment']
            unix=time.time()
            create_date=str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
            c.execute('INSERT INTO Comments (id_article,comment,id_user,username,create_date) VALUES (?,?,?,?,?)',(id,comment,id_user,username,create_date))
            conn.commit()
            c.execute('SELECT * FROM Comments WHERE id_article = ?',(id))
            comments=[dict(id=row[0],
                    id_article=row[1],
                    comment=row[2],
                    id_user=row[3],
                    username=row[4],
                    create_date=row[5]) for row in c.fetchall()]
        c.close()
        conn.close()   
        return render_template ('article.html', liked=liked ,likes=likes, id_article=id_article , id_user=id_user , title=title , writer=writer , body=body , create_date=create_date , comments=comments)
    else :
        return render_template ('article.html',likes=likes, id_article=id_article , title=title , writer=writer , body=body , create_date=create_date , comments=comments)

@app.route('/article/<string:id>/like_article/' , methods=['GET','POST'])
def like_article(id):

    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    id_user=session['id']
    username=session['username']
    c.execute('INSERT INTO Likes (id_article,id_user,username) VALUES (?, ? , ?)',(id,id_user,username))
    conn.commit()
    c.close()
    conn.close() 

    return redirect(url_for('article', id=id))


@app.route('/article/<string:id>/dislike_article/' , methods=['GET','POST'])
def dislike_article(id):

    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    id_user=session['id']
    c.execute('DELETE FROM Likes WHERE id_article =? AND id_user=?',(id,id_user))
    conn.commit()
    c.close()
    conn.close() 

    return redirect(url_for('article', id=id))


class RegisterForm(form.Form):
    name=StringField(u'Name',validators=[validators.Length(min=1 , max=20)])
    email=StringField(u'Email',validators=[validators.Length(min=6 , max=30)])
    username = StringField(u'Username',validators=[validators.Length(min=4 , max=25)])
    password=PasswordField(u'Password', validators=[validators.DataRequired()])
    confrim=PasswordField(u'Confrim Password')

@app.route('/register', methods=['GET','POST'])
def register():
    form=RegisterForm(request.form)
    if request.method == 'POST' and form.validate() :
       name=form.name.data
       email=form.email.data
       username=form.username.data
       password=form.password.data
       confrim=form.confrim.data
       if confrim!=password :
           error='Passwords do not match'
           return render_template('register.html' , error=error , form=form)   
       else:
            conn=sqlite3.connect('DataBase.db')
            c=conn.cursor()
            c.execute('SELECT * FROM Users WHERE username = ?',[username])
            result=c.fetchall()
            if len(result)==0 :
                    c.execute('INSERT INTO Users (name,email,username,password) VALUES (? ,? ,? ,?)',(name,email,username,password))
                    flash(str(name) + ' are registered and can log in' , 'success')
            else:
                    error='This username ( '+str(username) + ' ) has been exists'
                    return render_template('register.html' , error=error , form=form)  

            conn.commit()
            c.close()
            conn.close()
            redirect(url_for('login'))
            

    return render_template('register.html' , form=form)




@app.route('/profile', methods=['GET','POST'])
def profile():
    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    c.execute('SELECT * FROM Users WHERE id = ?',[session['id']])

    for row in c.fetchall() :
       user_name=row[1]
       user_email=row[2]
       user_username=row[3]
       user_password=row[4]

    form=RegisterForm(request.form)

    form.name.data=user_name
    form.email.data=user_email
    form.username.data=user_username
    form.password.data=user_password

    if request.method == 'POST' and form.validate() :
        
        form.name.data=request.form['name']
        form.email.data=request.form['email']
        form.username.data=request.form['username']
        form.password.data=request.form['password']
        form.confrim.data=request.form['confrim']

        name=request.form['name']
        email=request.form['email']
        username=request.form['username']
        password=request.form['password']
        confrim=request.form['confrim']
        if form.validate() :
            c.execute('SELECT * FROM Users WHERE username=? And NOT(id = ?)',[username,session['id']])
            result=len(c.fetchall())
            if result==0 :
                if confrim==password :
                    c.execute('UPDATE Users SET name=?, email=?, username=? , password=?  WHERE id= ?',[name,email,username,password,session['id']])
                    conn.commit()
                    msg='Profile Updated'
                    return render_template('home.html' , msg=msg )     
                else :
                    error='Passwords do not match'
                    return render_template('profile.html' , error=error , form=form)
            else:
                error='This username ( '+str(username) + ' ) has been exists'
                return render_template('profile.html' , error=error , form=form) 
            conn.commit()
            c.close()
            conn.close()

    return render_template('profile.html' , form=form)


@app.route('/delete_comment/<string:id>' , methods=['GET' , 'POST'])
def delete_comment(id):
    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    c.execute('SELECT * FROM Comments WHERE id= ?',[id])
    for row in c.fetchall() :
        id_article=row[1]
    c.execute('DELETE FROM Comments WHERE id=?',[id])

    conn.commit()
    c.close()
    conn.close()
    return redirect(url_for('article', id=id_article))
     



@app.route('/login', methods=['GET','POST'])
def login() :
    if  request.method == 'POST' :

        username=request.form['username']
        password=request.form['password']

        conn=sqlite3.connect('DataBase.db')
        c=conn.cursor()
        c.execute('SELECT * FROM Users')
        userfound=False
        for row in c.fetchall() :
            if username==row[3] :
                userfound=True
                if password==row[4] :
                    session['logged_in'] = True
                    session['username']=username
                    session['id']=row[0]

                    flash('You are now logged in','success')
                    return redirect(url_for('dashboard'))
                    
        c.close()
        conn.close()
        if userfound==True :
            error='Invalid Login'
            return render_template('login.html' , error=error)  

        else :
            error='User Not Found'
            return render_template('login.html' , error=error)  
    return render_template('login.html')


@app.route('/logout')
def logout() :
    session.pop('logged_in', None)
    flash('You are now logged out','success')
    return redirect(url_for('login'))



@app.route('/dashboard')
def dashboard() :
    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    if (session['id']==1) :
        c.execute('SELECT * FROM Articles')
    else :
        c.execute('SELECT * FROM Articles WHERE id_creat = ?',[session['id']])

    articles=[dict(id=row[0],
                    title=row[1],
                    writer=row[3],
                    body=row[4],
                    create_date=row[5]) for row in c.fetchall()]
    result = len(articles)

    if result > 0 :
        return render_template('dashboard.html' , articles=articles)
    else:
        msg = 'No Articles Found'
        return render_template('dashboard.html' , msg=msg)

    conn.commit()
    c.close()
    conn.close()

class ArticleForm(form.Form):
    title= StringField('Title',[validators.Length(min=1 , max=200)])
    body = TextAreaField('Body', [validators.Length(min=1)])


@app.route('/add_article' , methods=['GET' , 'POST'])
def add_article() :
    form=ArticleForm(request.form)
    if request.method=='POST' and form.validate() :
        
        title=form.title.data
        body=form.body.data
        unix=time.time()
        create_date=str(datetime.datetime.fromtimestamp(unix).strftime('%Y-%m-%d %H:%M:%S'))
        conn=sqlite3.connect('DataBase.db')
        c=conn.cursor()
        c.execute('INSERT INTO Articles(title,id_creat,body,writer,create_date) VALUES(? , ? , ? , ? , ?)',(title,session['id'],body,session['username'],create_date))
        conn.commit()
        c.close()
        conn.close()


        flash('Article Created' , 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_article.html' , form=form)



@app.route('/edit_article/<string:id>' , methods=['GET' , 'POST'])
def edit_article(id) :
    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()
    c.execute('SELECT * FROM Articles WHERE id = ?',(id))

    for row in c.fetchall() :
        id_article=row[0]
        article_title=row[1]
        article_body=row[4]


    form=ArticleForm(request.form)
    
    form.title.data=article_title
    form.body.data = article_body

    if request.method=='POST' and form.validate() :
        title=request.form['title']
        body=request.form['body']

        conn=sqlite3.connect('DataBase.db')
        c=conn.cursor()

        c.execute('UPDATE Articles SET title=?, body=? WHERE id= ?',(title,body,id))
        conn.commit()
        c.close()
        conn.close()

        flash('Article Updated' , 'success')

        return redirect(url_for('dashboard'))

    return render_template('edit_article.html', id_article=id_article  , form=form )


@app.route('/delete_article/<string:id>' , methods=['GET' , 'POST'])
def delete_article(id):
    conn=sqlite3.connect('DataBase.db')
    c=conn.cursor()

    c.execute('DELETE FROM articles WHERE id=?',(id))
    c.execute('DELETE FROM Comments WHERE id_article=?',(id))
    c.execute('DELETE FROM Likes WHERE id_article=?',(id))

    conn.commit()
    c.close()
    conn.close()

    flash('Article Deleted' , 'success')

    return redirect(url_for('dashboard'))


if __name__=='__main__':
    app.secret_key='secret123'
    app.run(debug=True)
