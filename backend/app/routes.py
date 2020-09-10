from app import app, mongo, login_manager
from flask import Flask, render_template, url_for, redirect, request, flash
from app.forms import LoginForm, RegistrationForm, UpdateForm
from app.user_models import User
from flask_pymongo import PyMongo
from flask_login import LoginManager, current_user, login_user, logout_user, login_required
from werkzeug.security import generate_password_hash
from functools import wraps
from app.tables import UserTable
from bson.objectid import ObjectId



#-------------------------------------------
#     User pages
#-------------------------------------------

@app.route('/')
@app.route('/index')
def index():
    return render_template('user-pages/index.html')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        find_user = mongo.db.Users.find_one({"email": email})
        print("find_user: ", find_user)
        if User.login_valid(email, password):
            loguser = User(find_user['email'], find_user['password'], find_user['first_name'], find_user['last_name'], find_user['role'], find_user['_id'])
            login_user(loguser, remember=form.remember_me.data)
            # login_user(find_user, remember=form.remember_me.data)
            flash('You have been logged in!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login Unsuccessful. Please check email and password', 'danger')
            return "Login Unsuccessful"
    return render_template('user-pages/login.html', form = form)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        email = form.email.data
        first_name = form.first_name.data
        last_name = form.last_name.data
        password = generate_password_hash(form.password.data)
        find_user =  User.get_by_email(email)
        if find_user is None:
            User.register(email, password, first_name, last_name, "Admin")
            flash(f'Account created for {form.email.data}!', 'success')
            return redirect(url_for('index'))
        else:
            flash(f'Account already exists for {form.email.data}!', 'success')
    return render_template('user-pages/register.html', title='Register', form=form)


@app.route('/library')
def library():
    #get urls for images, they are supposed to be retrieved from the db
    dungeons_pic = url_for('static', filename='img/games/dungeons.jpg')
    stars_pic = url_for('static', filename='img/games/stars-without-number.jpg')
    pulp_pic = url_for('static', filename='img/games/pulp-cthulhu.jpg')
    #pass them to the rendering page
    return render_template('user-pages/library.html', dungeons_pic=dungeons_pic, stars_pic=stars_pic, pulp_pic=pulp_pic)

@app.route('/events')
def events():
    return render_template('user-pages/events.html')

@app.route('/join')
def join():
    return render_template('user-pages/join.html')

@app.route('/committee')
def committee():
    return render_template('user-pages/committee.html')

@app.route('/lifeMembers')
def lifeMembers():
    return render_template('user-pages/lifeMembers.html')

@app.route('/constitution')
def constitution():
    return render_template('user-pages/constitution.html')

@app.route('/operations')
def operations():
    return render_template('user-pages/operations.html')
	
@app.route('/forbidden')
def forbidden():
	return render_template('user-pages/forbidden.html')
		
@login_manager.unauthorized_handler
def unauthorized():
	if not current_user.is_authenticated:
		return redirect(url_for('login'))
	if ((current_user.role != "Admin")):
		return redirect(url_for('forbidden'))
	return 'Page not found 404.'

def login_required(role="ANY"):
	def wrapper(fn):
		@wraps(fn)
		def decorated_view(*args, **kwargs):
			if not current_user.is_authenticated:
				return login_manager.unauthorized()
			if ((current_user.role != role) and (role != "ANY")):
				return login_manager.unauthorized()
			return fn(*args, **kwargs)
		return decorated_view
	return wrapper


#-------------------------------------------
#     Admin pages
#-------------------------------------------
@app.route('/admin')
@login_required(role="Admin")
def admin():
	
	return render_template('admin-pages/home.html')
	
@app.route('/admin/users', methods=['GET', 'POST'])
@login_required(role="Admin")
def adminusers():
	items = mongo.db.Users.find()
	table = UserTable(items)
	table.border = True
	return render_template('admin-pages/users.html', table=table)
	
@app.route('/admin/users/<string:id>', methods=['GET', 'POST'])
def edit(id):
    searcheduser = mongo.db.Users.find_one({'_id': id})

    if searcheduser:
        form = UpdateForm(**searcheduser)
        name = searcheduser['first_name']
        if request.method == 'POST' and form.validate():
            mongo.db.Users.update_one({"_id": id},
                  { "$set": {
                             "first_name": form.first_name.data,
                              "last_name": form.last_name.data,
                              "email": form.email.data,
                              "role": form.role.data,
                             }
                 })
            flash('User updated successfully!')
            return redirect('/admin/users')
        return render_template('admin-pages/edit.html', form=form, name=name)
    else:
        return 'Error loading #{id}'.format(id=id)

@app.route('/admin/lib')
def lib():
    return render_template('admin-pages/lib.html')


#-------------------------------------------
#   Error pages, can be futher implemented
#-------------------------------------------
@app.errorhandler(404)
def page_not_found(e):
    return 'Page not found 404.'

@app.errorhandler(500)
def page_not_found(e):
    return 'Page not found 500.'

if __name__=='__main__':
    app.run(debug=True)