import os 
from flask import Flask,render_template,request,redirect,jsonify,flash,url_for,make_response
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy
from sqlalchemy import create_engine,Table,Column,Integer,String,ForeignKey
from sqlalchemy.orm import Session
import time
from datetime import datetime,date
import json
from flask_login import LoginManager,login_user,logout_user,current_user,login_required,UserMixin
from flask_restful import Resource,reqparse,Api
from flask import current_app as app
from flask_cors import CORS
from werkzeug.exceptions import HTTPException
import re

from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

app=Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI']= "sqlite:///"+os.path.join(os.getcwd(),'database.sqlite3')
db=SQLAlchemy()
db.init_app(app)
api=Api(app)
app.app_context().push()
login_manager = LoginManager()
login_manager.init_app(app)
#app.secret_key = b'_5#y2L"F4Q8z\n\xec]/'
app.secret_key = b'ajiuhaeiu"4%^&FGG??'
class NotfoundError(HTTPException):
    def __init__(self,status_code):
        self.response=make_response("",status_code)

        
class AlreadyExists(HTTPException):
    def __init__(self,status_code,code):
        self.response=make_response(f"{code} already exist",status_code)

        
class BusinessValidationError(HTTPException):
    def __init__(self,status_code,error_code,error_message):
        message={"error_code":error_code,"error_message":error_message}
        self.response=make_response(jsonify(message),status_code)

class Movie(db.Model):
    __tablename__ = 'movie'
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String,nullable=False)
    caption = Column(String,nullable=False)
    rating = Column(Integer,nullable=False)
    tags = Column(String,nullable=False)
    no_of_rating = Column(Integer,nullable=False)
class User(db.Model,UserMixin):
    __tablename__ = 'user'
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String,nullable=False)
    age = Column(Integer,nullable=False)
    gender = Column(String,nullable=False)
    username = Column(String,unique=True, nullable=False)
    password=Column(String,nullable=False)
    auth=Column(Integer,nullable=False,default=0)
    @property
    def is_authenticated(self):        
        return self.auth==1
    is_active=True
    is_anonymous=False
    def get_id(self):
        return str(self.id)

class User_Movie(db.Model):
    __tablename__ = 'user_movie'
    id = Column(Integer, autoincrement=True, primary_key=True)
    movie_id = Column(Integer,nullable=False)
    user_id = Column(Integer,nullable=False)
    like = Column(Integer,nullable=False)
    cart = Column(Integer,nullable=False)


#Home and users option
@app.route("/",methods=['GET','post'])    
def index():
    user_list=[i.username for i in User.query.all()]
    return render_template('index.html' ,user_list=user_list)


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(id=int(user_id)).first()

@app.route("/signin",methods=['post']) 
def signin():
    username=request.form.get("username")
    password=request.form.get("password")
    data=User.query.filter_by(username=username).first()
    if not data ==None:
        if data.username==username and data.password==password: 
            data.auth=1 
            db.session.commit()
            login_user(data)
            flash('Logged in successfully.')
            return redirect(url_for('movie'))
    return redirect(url_for('index'))

@app.route("/signout")
@login_required
def signout():
    current_user.auth=0
    db.session.commit()
    logout_user()
    return redirect(url_for('index'))

@app.route("/signup",methods=['post'])    
def signup():   
    name=request.form.get("Name")
    age=request.form.get("Age")
    gender=request.form.get("Gender")
    username=request.form.get("Username")
    password=request.form.get("Password")
    image= request.files['image']
    if name=="" or len(name)>30:
        return redirect(url_for('index'))
    if age=='' or (int(age)<15 or int(age)>100):
        return redirect(url_for('index'))
    if gender=="" or gender not in['male','female']:
        return redirect(url_for('index'))
    if username=="" or username in [i.username for i in User.query.all()]:
        return redirect(url_for('index'))
    if password=="" or len(password)<8:
        return redirect(url_for('index'))
    new_user=User(name=name,age=age,gender=gender,username=username,password=password)

    db.session.add(new_user)
    db.session.commit()
    image.save('./static/Image/user_'+str(new_user.id)+'.jpg')
    return redirect(url_for('index'))
#@app.route("/signin",methods=['post'])    
#def signin():   

    username=request.form.get("username")
    password=request.form.get("password")
    data=User.query.filter_by(username=username).first()
    
    if not data ==None:
        if data.username==username and data.password==password:
            print(data.password)
            return  redirect(url_for('movie'))
    return redirect(url_for('index'))

@app.route("/signinadmin",methods=['post'])    
def signinadmin():   
    username=request.form.get("username")
    password=request.form.get("password")
    data=User.query.filter_by(username=username).first()
    if not data == None and username[:5]=="admin":
        if data.username==username and data.password==password: 
            data.auth=1 
            db.session.commit()
            login_user(data)
            flash('Logged in successfully.')
            return redirect(url_for('home_admin'))
    return redirect(url_for('index'))


#user options


@app.route("/movie",methods=['GET','post'])  
@login_required
def movie():
    data=Movie.query.all()
    args=request.args.to_dict()
    if 'keyword' in args:
        query=args['keyword']        
        if not query=='':
            data=[i for i in data if query in (i.name+i.tags).lower()]      
    #data = sorted(data,key = lambda) 
    tdata = User_Movie.query.filter_by(user_id=current_user.id).all()
    if len(tdata) == 0:
        for i in data:
            d = User_Movie(user_id=current_user.id,movie_id = i.id,like = 0,cart = 0)
            db.session.add(d)
            db.session.commit()
    tdata = User_Movie.query.filter_by(user_id=current_user.id).all()
    tdata = { i.movie_id:(i.like,i.cart) for i in tdata}


    movie_tags = {}
    for i in data:
        st = f" {i.tags}"
        pattern = r'\b[a-zA-Z]+\b|\b\d{4}\b'
        tl = re.findall(pattern, st)
        tl = [i.lower() for i in tl ] 
        movie_tags[i.name] = tl

    tags = sorted(set(tag for tags_list in movie_tags.values() for tag in tags_list))
    user_likes = [ i.name for i in data if tdata[i.id][0] == 1 ]
    if len(user_likes) == 0:
        user_likes = list(movie_tags.keys())
    tag_matrix = np.zeros((len(movie_tags), len(tags)))
    for i, movie_id in enumerate(movie_tags.keys()):
        for tag in movie_tags[movie_id]:
            j = tags.index(tag)
            tag_matrix[i, j] = 1
    liked_indices = [list(movie_tags.keys()).index(movie_id) for movie_id in user_likes]
    liked_vector = tag_matrix[liked_indices]
    liked_vector = liked_vector.reshape(1, -1)
    similarity_scores = cosine_similarity(tag_matrix, liked_vector.reshape(len(user_likes),len(tags)))
    similarity_scores = similarity_scores.sum(axis=1)
    ml = list(movie_tags.keys())
    for i in range(len(ml)):
        data[i].score = similarity_scores[i]
    data = sorted(data,key = lambda x : -x.score)
    #ml = [(ml[i],similarity_scores[i]) for i in range(len(ml))]
    #sorted(ml,key = lambda x : -x[1])


    #data = [ i for i in data if tdata[i.id][1] == 1 ] + [ i for i in data if tdata[i.id][1] == 0 ]
    for i in data:
        if tdata[i.id][1] == 1:
            i.cart = "T"
        else:
            i.cart = "F"


    for i in data:
        if tdata[i.id][0] == 1:
            i.like = "T"
        else:
            i.like = "F"
    image=[]
    for i in data:
        image.append('Image/'+f'movie_{str(i.id)}.jpg')
    movie_list=[i.name for i in data]    
    return render_template('movie.html',data=data,image=image)






@app.route("/profile",methods=['GET','post'])   
@login_required 
def profile():
    user_id=current_user.id
    data=User.query.filter_by(id=user_id).first()
    img='Image/'+f'user_{data.id}.jpg'
    tab=[]
    return render_template('profile.html',data=data,image=img,tab=tab)

@app.route("/rate",methods=['GET'])
@login_required
def rate():
    args=request.args.to_dict()
    id=args['id']
    rate=args['rate']
    booking=Booking.query.filter_by(id=id).first()
    booking.rating=rate
    vs=Venueshow.query.filter_by(id=booking.venue_show_id).first()
    movie=Movie.query.filter_by(id=vs.movie_id).first()
    movie.rating=(movie.rating*movie.no_of_rating+int(rate))/(movie.no_of_rating+1)
    movie.no_of_rating=movie.no_of_rating+1
    db.session.commit()
    return redirect(url_for('profile'))

@app.route("/profileupdate",methods=['post'])  
@login_required  
def profileupdate():   
    id=request.form.get("Id")
    name=request.form.get("Name")
    age=request.form.get("Age")
    gender=request.form.get("Gender")
    username=request.form.get("Username")
    password=request.form.get("Password")
    image= request.files['image']
    user=User.query.filter_by(id=id).first()

    if not image.filename=='':
        image.save('./static/Image/user_'+str(id)+'.jpg')
    if name=="" or len(name)>30:
        return redirect(url_for('profile'))
    if age=='' or (int(age)<15 or int(age)>100):
        return redirect(url_for('profile'))
    if gender=="" or gender not in['male','female']:
        return redirect(url_for('profile'))
    if username==""  or (not username==user.username and username in [i.username for i in User.query.all()]):
        return redirect(url_for('profile'))
    
    user.name=name
    user.age=age
    user.gender=gender
    user.username=username
    user.password=password
    db.session.commit()
    
    return redirect(url_for('profile'))



#admin options

#basic views
@app.route("/homeadmin",methods=['POST','GET'])    
@login_required
def home_admin():
    data=Movie.query.all()
    args=request.args.to_dict()
    if 'keyword' in args:
        query=args['keyword'].lower()
        
        if not query=='':
            data=[i for i in data if query in (i.name+i.tags).lower()]       
    image=[]
    for i in data:
        image.append('Image/'+f'movie_{str(i.id)}.jpg')
    movie_list=[i.name for i in data]    
    return render_template('homeadmin.html',data=data,image=image,movie_list=movie_list)





#add 
@app.route("/addmovie",methods=['post'])    
@login_required
def addmovie():   
    name=request.form.get("Name")
    caption=request.form.get("Caption")
    tags=request.form.get("Tags")
    image= request.files['image']
    if name =="" or (name in [i.name for i in Movie.query.all()]) or len(name)>40:
        return redirect(url_for('home_admin'))
    if caption=="" or len(caption)>110:
        return redirect(url_for('home_admin'))
    if tags=="" or len(tags)>60:
        return redirect(url_for('home_admin'))
    

    new_movie=Movie(name=name,caption=caption,rating=3,tags=tags,no_of_rating=1)
    db.session.add(new_movie)
    db.session.commit()
    image.save('./static/Image/movie_'+str(new_movie.id)+'.jpg')

    return redirect(url_for('home_admin'))




#remove
@app.route("/<movie_id>/moviedelete",methods=['get','post'])  
@login_required  
def deletemovie(movie_id):   
    data=Movie.query.filter_by(id=movie_id).first()
    db.session.delete(data)
    db.session.commit()
    os.remove('./static/Image/movie_'+str(movie_id)+'.jpg')
    return redirect(url_for('home_admin'))

@app.route("/<movie_id>/likeit",methods=['get','post'])  
@login_required  
def likeit(movie_id):  

    tdata = User_Movie.query.filter_by(user_id=current_user.id,movie_id = movie_id)[0]
    if tdata.like == 1:
        tdata.like = 0
    else:
        tdata.like = 1
    db.session.commit()
    return redirect(url_for('movie'))

@app.route("/<movie_id>/cart",methods=['get','post'])  
@login_required  
def cart(movie_id):  
    tdata = User_Movie.query.filter_by(user_id=current_user.id,movie_id = movie_id)[0]
    if tdata.cart == 1:
        tdata.cart = 0
    else:
        tdata.cart = 1
    db.session.commit()
    return redirect(url_for('movie'))


# update
@app.route("/movieupdate",methods=['post'])    
@login_required
def updatemovie():   
    movie_id=request.form.get("id")

    name=request.form.get("name")
    caption=request.form.get("caption")
    tags=request.form.get("tags")
    image= request.files['image']
    movie=Movie.query.filter_by(id=movie_id).first()
    if name =="" or ( not name==movie.name and (name in [i.name for i in Movie.query.all()] or len(name)>40)):
        return redirect(url_for('home_admin'))
    if caption=="" or len(caption)>110:
        return redirect(url_for('home_admin'))
    if tags=="" or len(tags)>60:
        return redirect(url_for('home_admin'))
    movie.name=name
    movie.caption=caption
    movie.tags=tags
    db.session.commit()
    if not image.filename=='':
        image.save('./static/Image/movie_'+str(movie_id)+'.jpg') 
    
    return redirect(url_for('home_admin'))


@app.route("/summary",methods=['post','get'])    
@login_required
def summary():
    star=len([i for i in Movie.query.all() if i.rating>=4])
    vs=Venueshow.query.all()
    md={}
    vd={}
    hfs=0
    for i in vs:
        md[i.movie_id]=md.get(i.movie_id,0)+1
        vd[i.venue_id]=vd.get(i.venue_id,0)+1
        if i.remaining_capacity==0:
            hfs+=1
    mid = max(md, key= lambda x: md[x])
    movie=Movie.query.filter_by(id=mid).first().name
    vid= max(vd, key= lambda x: vd[x])
    venue=Venue.query.filter_by(id=vid).first().name

    return render_template('summary.html',star=star,hfs=hfs,movie=movie,venue=venue)

class MovieAPI(Resource):
    def get(self,id):
        data=Movie.query.filter_by(id=id).first()
        if data==None:
            raise NotfoundError(status_code=404)

        return ({'name':data.name,'caption':data.caption,'rating':data.rating,'tags':data.tags})
    def put(self,id):
        parser=reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('caption')
        parser.add_argument('rating')
        parser.add_argument('tags')
        data=parser.parse_args()
        
        if data.get('name')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie001",error_message="Movie Name is required")
        if data.get('caption')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie002",error_message="Movie Caption is required")
        if data.get('rating')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie003",error_message="Movie Rating is required")
        if data.get('tags')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie004",error_message="Movie Tags is required")
        movie=Movie.query.filter_by(id=id).first()
        if movie==None:
            raise NotfoundError(status_code=404)
        
        movie.name=data.get('name')
        movie.caption=data.get('caption')
        movie.rating=data.get('rating')
        movie.tags=data.get('tags')

        db.session.commit()

        return ({"id": movie.id,"caption":movie.caption,"name":movie.name,"rating": movie.rating,"tags":movie.tags})
    def delete(self,id):
        movie=Movie.query.filter_by(id=id).first()
        if movie==None:
            raise NotfoundError(status_code=404)
        db.session.delete(movie)
        db.session.commit()
        show=Venueshow.query.filter_by(movie_id=id).all()
        for i in show:
            db.session.delete(i)
            db.session.commit()
                
        return "Successfully Deleted",200
    def post(self):
        parser=reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('caption')
        parser.add_argument('tags')
        parser.add_argument('rating')
        data=parser.parse_args()

        if data.get('name')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie001",error_message="Movie Name is required")
        if data.get('caption')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie002",error_message="Movie Caption is required")
        if data.get('rating')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie003",error_message="Movie Rating is required")
        if data.get('tags')==None:
            raise BusinessValidationError(status_code=400,error_code="Movie004",error_message="Movie Tags is required")

        movie=Movie.query.filter_by(name=data.get('name')).first()
        print(movie)
        if not movie==None:
            raise AlreadyExists(code=data.get('name'),status_code=409)
        new_movie=Movie(name=data.get('name'),caption=data.get('caption'),rating=data.get('rating'),tags=data.get('tags'),no_of_rating=1)
        db.session.add(new_movie)
        db.session.commit()
        return ({"id": new_movie.id,"caption":new_movie.caption,"name":new_movie.name,"rating": new_movie.rating,"tags":new_movie.tags,'no_of_rating':new_movie.no_of_rating})


api.add_resource(MovieAPI,  "/api/movie","/api/movie/<int:id>")
if __name__=='__main__':
    app.run(port=8080,debug=True)