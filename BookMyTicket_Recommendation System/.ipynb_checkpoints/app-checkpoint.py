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



class Booking(db.Model):
    __tablename__ = 'booking'
    id = Column(Integer, autoincrement=True, primary_key=True)
    user_id = Column(Integer, ForeignKey("user.id"),nullable=False)
    venue_show_id = Column(Integer, ForeignKey("venueshow.id"),nullable=False)
    no_of_ticket = Column(Integer,nullable=False)
    timestamp = Column(String, nullable=False)
    rating = Column(Integer)
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
class Venue(db.Model):
    __tablename__ = 'venue'
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String,nullable=False)
    caption = Column(String,nullable=False)
    capacity = Column(Integer,nullable=False)
    rating = Column(Integer,nullable=False)
    address=Column(String,nullable=False)
    city = Column(String,nullable=False)
    no_of_rating = Column(Integer,nullable=False)    
class Venueshow(db.Model):
    __tablename__='venueshow'
    id = Column(Integer, autoincrement=True, primary_key=True)
    movie_id = Column(Integer, ForeignKey("movie.id"),nullable=False)
    venue_id = Column(Integer, ForeignKey("venue.id"),nullable=False)
    price = Column(Integer,nullable=False)  
    remaining_capacity = Column(Integer,nullable=False) 
    date=Column(String,nullable=False)
    start_time = Column(String,nullable=False) 
    end_time = Column(String,nullable=False) 


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
            return redirect(url_for('movie',venue_id='all'))
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
            return  redirect(url_for('movie',venue_id='all'))
    return redirect(url_for('index'))

@app.route("/signinadmin",methods=['post'])    
def signinadmin():   
    username=request.form.get("username")
    password=request.form.get("password")
    data=User.query.filter_by(username=username).first()
    if not data ==None and username[:5]=="Admin":
        if data.username==username and data.password==password: 
            data.auth=1 
            db.session.commit()
            login_user(data)
            flash('Logged in successfully.')
            return redirect(url_for('home_admin'))
    return redirect(url_for('index'))


#user options


@app.route("/<venue_id>/movie",methods=['GET','post'])  
@login_required
def movie(venue_id):
    data=Movie.query.all()
    if not venue_id =="all":
        query1=[i.movie_id for i in Venueshow.query.filter_by(venue_id=venue_id).all()]
        data=[i for i in data if i.id in query1]
        venue=Venue.query.filter_by(id=venue_id).first()
        venue.id=str(venue.id)
    else:
        venue=Venue(id='all')
    args=request.args.to_dict()
    if 'keyword' in args:
        query=args['keyword']        
        if not query=='':
            try :
                date,month=[i if len(i)==2  else '0'+i for i in query.split('-')[:2]]
                print(f'2023-{month}-{date}')
                show=list(set([i.movie_id for i in Venueshow.query.filter_by(date=f'2023-{month}-{date}').all() if(venue_id=='all' or i.venue_id==venue_id)]))
                print(show)
                data=[i for i in data if i.id in show]       


            except:    
                data=[i for i in data if query in (i.name+i.tags).lower()]       
    image=[]
    for i in data:
        image.append('Image/'+f'movie_{str(i.id)}.jpg')
    movie_list=[i.name for i in data]    
    return render_template('movie.html',data=data,image=image,venue=venue)


@app.route("/<movie_id>/venue/",methods=['GET','POST']) 
@login_required
def venue(movie_id):
    data=Venue.query.all()

    if not movie_id =="all":
        query1=[i.venue_id for i in Venueshow.query.filter_by(movie_id=movie_id).all()]
        data=[i for i in data if i.id in query1]
        movie=Movie.query.filter_by(id=movie_id).first()
        movie.id=str(movie.id)
    else:
        movie=Movie(id='all')
    args=request.args.to_dict()
    if 'keyword' in args:
        query2=args['keyword'].lower()
        if not query2=="":
            data=[i for i in data if query2 in (i.name+i.address+i.city).lower()]


    
    image=[]
    for i in data:
        image.append('Image/'+f'venue_{str(i.id)}.jpg')
    return render_template('venue.html',data=data,image=image,movie=movie)

@app.route("/<movie_id>/<venue_id>/bookdata",methods=['GET'])  
@login_required 
def bookdata(movie_id,venue_id): 
    data=Venueshow.query.filter_by(movie_id=movie_id,venue_id=venue_id).all()
    data=[[i.id,i.price,i.remaining_capacity,i.date,i.start_time,i.end_time] for i in data]
    print(data)
    return jsonify(data)


@app.route("/bookticket",methods=['GET'])   
@login_required 
def bookticket(): 
    user_id=current_user.id
    args=request.args.to_dict()
    show_id=args['id']
    no_of_ticket=args['nticket']
    show=Venueshow.query.filter_by(id=show_id).first()
    if int(no_of_ticket) >show.remaining_capacity or int(no_of_ticket)<1:
            return  redirect(url_for('movie',venue_id='all'))  
    show.remaining_capacity=show.remaining_capacity-int(no_of_ticket)
    new_book=Booking(user_id=user_id,venue_show_id=show_id,no_of_ticket=no_of_ticket,rating=3,timestamp=time.time())
    db.session.add(new_book)
    db.session.commit()

    return  redirect(url_for('movie',venue_id='all'))  

@app.route("/profile",methods=['GET','post'])   
@login_required 
def profile():
    user_id=current_user.id
    data=User.query.filter_by(id=user_id).first()
    img='Image/'+f'user_{data.id}.jpg'
    table=Booking.query.filter_by(user_id=user_id).all()
    tab=[]
    for i in table:
        try:
            vs=Venueshow.query.filter_by(id=i.venue_show_id).first()
            mname=Movie.query.filter_by(id=vs.movie_id).first().name
            vname=Venue.query.filter_by(id=vs.venue_id).first().name
            dt_object = datetime.fromtimestamp(float(i.timestamp))
            date=str(dt_object).split()[0]
            nticket=i.no_of_ticket
            tab.append([mname,vname,date,nticket,i.rating,i.id])
        except:
            pass    
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
    venue_data=sorted([i.name for i in Venue.query.all()])

    args=request.args.to_dict()
    if 'keyword' in args:
        query=args['keyword'].lower()
        
        if not query=='':
            data=[i for i in data if query in (i.name+i.tags).lower()]       
    image=[]
    for i in data:
        image.append('Image/'+f'movie_{str(i.id)}.jpg')
    movie_list=[i.name for i in data]    
    return render_template('homeadmin.html',data=data,image=image,movie_list=movie_list,venue_data=venue_data)

@app.route("/homeadminvenue",methods=['GET','POST'])    
@login_required
def home_admin_venue():        
    data=Venue.query.all()
    movie_data=sorted([i.name for i in Movie.query.all()])
    args=request.args.to_dict()
    if 'keyword' in args:
        query=args['keyword'].lower()
        if not query =='':
            data=[i for i in data if query in (i.name+i.city+i.address).lower()]

    image=[]
    for i in data:
        image.append('Image/'+f'venue_{str(i.id)}.jpg')
    venue_list=[i.name for i in data]    
    return render_template('homeadminvenue.html',data=data,image=image,venue_list=venue_list,movie_data=movie_data)

@app.route("/homeadminshow",methods=['GET','POST'])    
@login_required
def home_admin_show():
    data=Venueshow.query.all()
    mov={i.id:i.name for i in Movie.query.all()}
    ven={i.id:i.name for i in Venue.query.all()}
    data=[{'id':i.id,'movie_name':mov[i.movie_id],'venue_name':ven[i.venue_id],'price':i.price,'remaining_capacity':i.remaining_capacity,'date':i.date,'start_time':i.start_time,'end_time':i.end_time  } for i in data]
    args=request.args.to_dict()
    if 'keyword' in args:
        query=args['keyword'].lower()
        if not query=='':
            try:
                date,month=[i if len(i)==2  else '0'+i for i in query.split('-')[:2]]
                print(f'2023-{month}-{date}')
                data=[i for i in data if (f'2023-{month}-{date}' == i['date'])]

            except:

                data=[i for i in data if (query in (i['movie_name']+i['venue_name']).lower())]

    return render_template('homeadminshow.html',data=data)


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

@app.route("/addvenue",methods=['post'])    
@login_required
def addvenue():   
    name=request.form.get("Name")
    caption=request.form.get("Caption")
    capacity=request.form.get("Capacity")
    city=request.form.get("City")
    address=request.form.get("Address")
    if name =="" or (name in [i.name for i in Venue.query.all()]) or len(name)>40:
        return redirect(url_for('home_admin_venue'))
    if caption=="" or len(caption)>60:
        return redirect(url_for('home_admin_venue'))
    if int(capacity)=="" or int(capacity)>5000 or int(capacity)<30:
        return redirect(url_for('home_admin_venue'))
    if city =="" or len(city)>20:
        return redirect(url_for('home_admin_venue'))
    if address=="" or len(address)>60:
        return redirect(url_for('home_admin_venue'))

    image= request.files['image']
    new_venue=Venue(name=name,caption=caption,capacity=int(capacity),rating=3,address=address,city=city,no_of_rating=1)
    db.session.add(new_venue)
    db.session.commit()
    image.save('./static/Image/venue_'+str(new_venue.id)+'.jpg')

    return redirect(url_for('home_admin_venue'))

@app.route("/addshow",methods=['post'])    
@login_required
def addshow(): 
    movie_name=request.form.get("Movie")
    venue_name=request.form.get("Venue")
    datavenue=Venue.query.filter_by(name=venue_name).first()    
    datamovie=Movie.query.filter_by(name=movie_name).first()    
    price=request.form.get("Price")
    date_=request.form.get("Date")
    stime=request.form.get("Start")
    etime=request.form.get("End")
    if not movie_name in [i.name for i in Movie.query.all()]:
        return redirect(url_for('home_admin'))
    if not venue_name in [i.name for i in Venue.query.all()]:
        return redirect(url_for('home_admin'))
    if not (int(price)>0 and int(price)<99999):
        return redirect(url_for('home_admin'))
    date_strt, date_end = date(2023, 4, 1), date(2023, 5, 31) 
    a,b,c=([int(i) for i in date_.split('-')])
    date_tmp=date(a,b,c)
    if not ((date_tmp)>=date_strt and (date_tmp)<=date_end):
        return redirect(url_for('home_admin'))
    stime_tmp=[int(i) for i in stime.split(':')]
    etime_tmp=[int(i) for i in  etime.split(':')]
    if not (stime_tmp[0]<24 and stime_tmp[0]>=0 and stime_tmp[1]<60 and stime_tmp[1]>=0):
            return redirect(url_for('home_admin'))
    if not (etime_tmp[0]<24 and etime_tmp[0]>=0 and etime_tmp[1]<60 and etime_tmp[1]>=0):
            return redirect(url_for('home_admin'))
    new_show=Venueshow(movie_id=datamovie.id,venue_id=datavenue.id,price=price,remaining_capacity=datavenue.capacity,date=date_,start_time=stime,end_time=etime)
    db.session.add(new_show)
    db.session.commit()

    return redirect(url_for('home_admin'))  


#remove
@app.route("/<movie_id>/moviedelete",methods=['get','post'])  
@login_required  
def deletemovie(movie_id):   
    show=Venueshow.query.filter_by(movie_id=movie_id).all()
    for i in show:
        db.session.delete(i)
        db.session.commit()
    data=Movie.query.filter_by(id=movie_id).first()
    db.session.delete(data)
    db.session.commit()
    os.remove('./static/Image/movie_'+str(movie_id)+'.jpg')
    return redirect(url_for('home_admin'))


@app.route("/<venue_id>/venuedelete",methods=['get','post'])  
@login_required  
def deletevenue(venue_id):   
    show=Venueshow.query.filter_by(venue_id=venue_id).all()
    for i in show:
        db.session.delete(i)
        db.session.commit()
    data=Venue.query.filter_by(id=venue_id).first()
    db.session.delete(data)
    db.session.commit()   
    os.remove('./static/Image/venue_'+str(venue_id)+'.jpg')
    return redirect(url_for('home_admin_venue'))

@app.route("/<show_id>/deleteshow",methods=['get','post'])   
@login_required 
def deleteshow(show_id):   
    show=Venueshow.query.filter_by(id=show_id).first()
    db.session.delete(show)
    db.session.commit() 
    return redirect(url_for('home_admin_show'))

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

@app.route("/venueupdate",methods=['post'])    
@login_required
def updatevenue():   
    venue_id=request.form.get('id')
    name=request.form.get("name")
    caption=request.form.get("caption")
    capacity=request.form.get("capacity")
    city=request.form.get("city")
    address=request.form.get("address")
    image= request.files['image']
    venue=Venue.query.filter_by(id=venue_id).first()
    if name =="" or ( not name==venue.name and (name in [i.name for i in Venue.query.all()] or len(name)>40)):
        return redirect(url_for('home_admin_venue'))
    if caption=="" or len(caption)>60:
        return redirect(url_for('home_admin_venue'))
    if int(capacity)=="" or int(capacity)>5000 or int(capacity)<30:
        return redirect(url_for('home_admin_venue'))
    if city =="" or len(city)>20:
        return redirect(url_for('home_admin_venue'))
    if address=="" or len(address)>60:
        return redirect(url_for('home_admin_venue'))
    venue.name=name
    venue.caption=caption
    venue.capacity=capacity
    venue.city=city
    venue.address=address
    db.session.commit()
    if not image.filename=='':
        image.save('./static/Image/venue_'+str(venue_id)+'.jpg') 
    
    return redirect(url_for('home_admin_venue'))

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

class VenueAPI(Resource):
    def get(self,id):
        data=Venue.query.filter_by(id=id).first()
        if data==None:
            raise NotfoundError(status_code=404)

        return ({'name':data.name,'caption':data.caption,'capacity':data.capacity,'address':data.address,'city':data.city})  
    def put(self,id):
        parser=reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('caption')
        parser.add_argument('capacity')
        parser.add_argument('address')
        parser.add_argument('city')

        data=parser.parse_args()
        
        if data.get('name')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue001",error_message="Venue Name is required")
        if data.get('caption')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue002",error_message="Venue Caption is required")
        if data.get('capacity')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue003",error_message="Venue Capacity is required")
        if data.get('address')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue004",error_message="Venue Address is required")
        if data.get('city')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue005",error_message="Venue City is required")
        venue=Venue.query.filter_by(id=id).first()
        if venue==None:
            raise NotfoundError(status_code=404)
        
        venue.name=data.get('name')
        venue.caption=data.get('caption')
        venue.capacity=data.get('capacity')
        venue.address=data.get('address')
        venue.city=data.get('city')

        db.session.commit()

        return ({"id": venue.id,"caption":venue.caption,"name":venue.name,"capacity": venue.capacity,"address":venue.address,"city":venue.city})
    def delete(self,id):
        venue=Venue.query.filter_by(id=id).first()
        if venue==None:
            raise NotfoundError(status_code=404)
        db.session.delete(venue)
        db.session.commit()
        show=Venueshow.query.filter_by(venue_id=id).all()
        for i in show:
            db.session.delete(i)
            db.session.commit()
                
        return "Successfully Deleted",200
    def post(self):
        parser=reqparse.RequestParser()
        parser.add_argument('name')
        parser.add_argument('caption')
        parser.add_argument('capacity')
        parser.add_argument('address')
        parser.add_argument('city')

        data=parser.parse_args()

        if data.get('name')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue001",error_message="Venue Name is required")
        if data.get('caption')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue002",error_message="Venue Caption is required")
        if data.get('capacity')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue003",error_message="Venue Capacity is required")
        if data.get('address')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue004",error_message="Venue Address is required")
        if data.get('city')==None:
            raise BusinessValidationError(status_code=400,error_code="Venue005",error_message="Venue City is required")

        venue=Venue.query.filter_by(name=data.get('name')).first()

        if not venue==None:
            raise AlreadyExists(code=data.get('name'),status_code=409)
        new_Venue=Venue(name=data.get('name'),caption=data.get('caption'),capacity=data.get('capacity'),address=data.get('address'),city=data.get('city'),no_of_rating=1,rating=3)
        db.session.add(new_Venue)
        db.session.commit()
        return ({"id": new_Venue.id,"caption":new_Venue.caption,"name":new_Venue.name,"capacity": new_Venue.capacity,"address":new_Venue.address,"city":new_Venue.city})
    

class VenueshowAPI(Resource):
    def get(self,mname,vname):
        mid=Movie.query.filter_by(name=mname).first()
        vid=Venue.query.filter_by(name=vname).first()
        if mid==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow001",error_message="Movie does not exist")
        if vid==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow001",error_message="Venue does not exist")

        datas=Venueshow.query.filter_by(movie_id=mid.id,venue_id=vid.id).all()
        if datas==None:
            raise NotfoundError(status_code=404)
        
        
        return ([{'id':data.id,'movie_name':mname,'venue_name':vname,'price':data.price,'remaining_capacity':data.remaining_capacity,'date':data.date,'start_time':data.start_time,'end_time':data.end_time} for data in datas])  
    def delete(self,id):
        venueshow=Venueshow.query.filter_by(id=id).first()
        if venueshow==None:
            raise NotfoundError(status_code=404)
        db.session.delete(venueshow)
        db.session.commit()
                
        return "Successfully Deleted",200
    def post(self):
        parser=reqparse.RequestParser()
        parser.add_argument('mname')
        parser.add_argument('vname')
        parser.add_argument('price')
        parser.add_argument('date')
        parser.add_argument('start_time')
        parser.add_argument('end_time')
        data=parser.parse_args()
        
        movie=Movie.query.filter_by(name=data.get('mname')).first()
        venue=Venue.query.filter_by(name=data.get('vname')).first()

        
        if data.get('mname')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow007",error_message="Movie name is required")
        if data.get('vname')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow008",error_message="Venue name is required")
        if data.get('price')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow003",error_message="Price is required")
        if data.get('date')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow004",error_message="Date is required")
        if data.get('price')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow003",error_message="Price is required")
        if data.get('date')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow004",error_message="Date is required")
        if data.get('start_time')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow005",error_message="Start Time is required")
        if data.get('end_time')==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow006",error_message="End Time is required")
        if movie==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow001",error_message="Movie does not exist")
        if venue==None:
            raise BusinessValidationError(status_code=400,error_code="Venueshow002",error_message="Venue does not exist")
        
        new_show=Venueshow(movie_id=movie.id,venue_id=venue.id,price=data['price'],remaining_capacity=venue.capacity,date=data['date'],start_time=data['start_time'],end_time=data['end_time'])
        db.session.add(new_show)
        db.session.commit()
        return ({'id':new_show.id,'movie_name':movie.name,'venue_name':venue.name,'price':data['price'],'remaining_capacity':venue.capacity,'date':data['date'],'start_time':data['start_time'],'end_time':data['end_time']})


api.add_resource(MovieAPI,  "/api/movie","/api/movie/<int:id>")
api.add_resource(VenueAPI,"/api/venue","/api/venue/<int:id>")
api.add_resource(VenueshowAPI,"/api/show","/api/show/<int:id>","/api/show/<mname>/<vname>")




if __name__=='__main__':
    app.run(port=8080,debug=True)