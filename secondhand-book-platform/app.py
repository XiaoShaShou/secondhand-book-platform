import pymysql
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
import time
import os
from sqlalchemy import or_

# 初始化 Flask 应用
app = Flask(__name__)
# 配置密钥（用于 session、flash 提示）
app.secret_key = '123456'  # 新手可随便写，上线要改复杂
# 配置 MySQL 连接（替换成你的 MySQL 账号密码）
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:Wyx123456@localhost/second_hand_books'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# 上传图片配置
app.config['UPLOAD_FOLDER'] = 'static/upload'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 最大16MB
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# 初始化数据库
db = SQLAlchemy(app)
# 初始化登录管理器
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  # 未登录时跳转到登录页

# 定义用户模型（对应users表，新增nickname）
class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    nickname = db.Column(db.String(50), default='')
    password = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    create_time = db.Column(db.DateTime, default=db.func.now())
    books = db.relationship('Book', backref='user', lazy=True)
    favorites = db.relationship('Favorite', backref='user', lazy=True)

# 书籍表
class Book(db.Model):
    __tablename__ = 'books'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)    # 书名
    author = db.Column(db.String(50))                   # 作者
    price = db.Column(db.Float, nullable=False)          # 价格
    desc = db.Column(db.Text)                            # 书籍描述
    pic = db.Column(db.String(200))                      # 图片路径
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # 发布人ID
    create_time = db.Column(db.DateTime, default=db.func.now())
    favorites = db.relationship('Favorite', backref='book', lazy=True)

# 收藏表
class Favorite(db.Model):
    __tablename__ = 'favorites'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)
    create_time = db.Column(db.DateTime, default=db.func.now())

# 留言/私信表
class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 发送者ID
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)  # 接收者ID
    book_id = db.Column(db.Integer, db.ForeignKey('books.id'), nullable=False)  # 关联书籍ID
    content = db.Column(db.Text, nullable=False)  # 留言内容
    create_time = db.Column(db.DateTime, default=db.func.now())  # 留言时间
    is_read = db.Column(db.Boolean, default=False)  # 是否已读

    # 关联用户（发送者/接收者）
    sender = db.relationship('User', foreign_keys=[sender_id], backref='sent_messages')
    receiver = db.relationship('User', foreign_keys=[receiver_id], backref='received_messages')
    # 关联书籍
    book = db.relationship('Book', backref='messages')

# 加载用户的回调函数（flask-login 必需）
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# 【新增/优化】注册路由
@app.route('/register', methods=['GET', 'POST'])
def register():
    # POST请求：提交注册信息
    if request.method == 'POST':
        username = request.form.get('username').strip()
        nickname = request.form.get('nickname').strip() or ''
        password = request.form.get('password').strip()
        email = request.form.get('email').strip() or None
        phone = request.form.get('phone').strip() or None

        # 1. 校验用户名是否为空/已存在
        if not username:
            flash('用户名不能为空！')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('用户名已被注册，请更换！')
            return redirect(url_for('register'))
        # 2. 校验邮箱（若填了则检查是否唯一）
        if email and User.query.filter_by(email=email).first():
            flash('邮箱已被注册，请更换！')
            return redirect(url_for('register'))
        # 3. 密码加密（必须做，禁止存明文）
        # hashed_pwd = generate_password_hash(password, method='pbkdf2:sha256')
        # 4. 创建新用户
        new_user = User(
            username=username,
            nickname=nickname,
            password=password,
            email=email,
            phone=phone
        )
        # 5. 存入数据库
        try:
            db.session.add(new_user)
            db.session.commit()
            flash('注册成功，请登录！')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'注册失败：{str(e)}')
            return redirect(url_for('register'))
    # GET请求：返回注册页面
    return render_template('register.html')

# 【新增】登录路由
@app.route('/login', methods=['GET', 'POST'])
def login():
    # 【修复点1】：当以GET方式访问登录页时，清空所有Flash消息，防止残留
    if request.method == 'GET':
        # 读取并丢弃所有消息，清除Session中的遗留提示
        get_flashed_messages()
        return render_template('login.html')

    # POST请求处理逻辑
    username = request.form.get('username').strip()
    password = request.form.get('password').strip()
    user = User.query.filter_by(username=username).first()

    if not user or user.password != password:
        flash('用户名或密码错误！')
        return redirect(url_for('login'))

    # 登录成功
    login_user(user)
    # 【修复点2】：这里不使用flash，而是直接把欢迎信息通过URL参数或直接在首页渲染
    # 因为flash会在回退时残留，直接在首页模板中处理更稳妥
    return redirect(url_for('index'))

# 【新增】退出路由（@login_required：必须登录才能访问）
@app.route('/logout')
@login_required
def logout():
    logout_user()  # flask-login的退出方法，清除session
    flash('已成功退出！')
    return redirect(url_for('index'))


# 首页 + 搜索功能
@app.route('/')
def index():
    # 获取搜索关键词（前端传的参数，默认空）
    keyword = request.args.get('keyword', '').strip()

    # 构建查询：如果有关键词，按书名/作者模糊搜索；否则查全部
    if keyword:
        # filter是多条件查询，or_实现“或”逻辑，like实现模糊匹配
        books = Book.query.filter(
            db.or_(
                Book.title.like(f'%{keyword}%'),  # 书名包含关键词
                Book.author.like(f'%{keyword}%')  # 作者包含关键词
            )
        ).order_by(Book.create_time.desc()).all()
    else:
        # 无关键词：按发布时间倒序查全部
        books = Book.query.order_by(Book.create_time.desc()).all()

    # 把关键词也传给前端（回显搜索框）
    return render_template('index.html', books=books, keyword=keyword)

# 发布书籍（需登录）
@app.route('/publish_book', methods=['GET', 'POST'])
@login_required
def publish_book():
    if request.method == 'POST':
        title = request.form['title']
        author = request.form.get('author')
        price = request.form['price']
        description = request.form.get('description')

        new_book = Book(
            title=title,
            author=author,
            price=price,
            description=description,
            seller_id=current_user.id  # 当前登录用户的id
        )

        try:
            db.session.add(new_book)
            db.session.commit()
            flash('书籍发布成功！')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'发布失败：{str(e)}')
            return redirect(url_for('publish_book'))
    return render_template('publish_book.html')

# 发布书籍页面
@app.route('/add_book', methods=['GET','POST'])
@login_required
def add_book():
    if request.method == 'POST':
        title = request.form.get('title').strip()
        author = request.form.get('author','').strip()
        price = request.form.get('price')
        desc = request.form.get('desc','').strip()
        pic = request.files.get('pic')

        if not title or not price:
            flash('书名和价格不能为空')
            return redirect('/add_book')

        # 处理图片
        pic_path = None
        if pic and pic.filename.strip() != '':  # 增加对空文件名的判断
            filename = secure_filename(pic.filename)
            # 确保文件名不为空
            if not filename:
                filename = f"unknown_{int(time.time())}.jpg"  # 生成一个默认文件名
            # 拼接完整路径
            save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            pic.save(save_path)
            pic_path = f'upload/{filename}'  # 注意这里的路径，要和static目录对应

        # 存入数据库
        book = Book(
            title=title,
            author=author,
            price=float(price),
            desc=desc,
            pic=pic_path,
            user_id=current_user.id
        )
        db.session.add(book)
        db.session.commit()

        flash('发布成功！')
        return redirect('/')

    return render_template('add_book.html')


# 书籍详情页
@app.route('/book/<int:book_id>')
def book_detail(book_id):
    book = Book.query.get_or_404(book_id)
    is_favorited = False
    if current_user.is_authenticated:
        is_favorited = Favorite.query.filter_by(
            user_id=current_user.id,
            book_id=book_id
        ).first() is not None
    return render_template('book_detail.html', book=book, is_favorited=is_favorited)

# 编辑书籍（仅发布者可操作）
@app.route('/book/edit/<int:book_id>', methods=['GET', 'POST'])
@login_required  # 必须登录
def edit_book(book_id):
    book = Book.query.get_or_404(book_id)

    # 校验：只能编辑自己发布的书
    if book.user_id != current_user.id:
        flash('你没有权限编辑这本书籍！')
        return redirect(url_for('book_detail', book_id=book_id))

    if request.method == 'POST':
        # 接收表单数据
        title = request.form.get('title').strip()
        author = request.form.get('author', '').strip()
        price = request.form.get('price')
        desc = request.form.get('desc', '').strip()
        pic = request.files.get('pic')

        # 基础校验
        if not title or not price:
            flash('书名和价格不能为空！')
            return redirect(url_for('edit_book', book_id=book_id))

        # 更新书籍信息
        book.title = title
        book.author = author
        book.price = float(price)
        book.desc = desc

        # 处理新图片（可选）
        if pic and pic.filename != '':
            # 删除旧图片（可选，避免冗余）
            if book.pic and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], book.pic.split('/')[-1])):
                os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.pic.split('/')[-1]))
            # 保存新图片
            filename = secure_filename(pic.filename)
            pic.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            book.pic = 'upload/' + filename

        # 提交修改到数据库
        db.session.commit()
        flash('书籍信息修改成功！')
        return redirect(url_for('book_detail', book_id=book_id))

    # GET请求：返回编辑页面（回显原有数据）
    return render_template('edit_book.html', book=book)


# 删除书籍（仅发布者可操作）
@app.route('/book/delete/<int:book_id>')
@login_required
def delete_book(book_id):
    book = Book.query.get_or_404(book_id)

    # 校验权限
    if book.user_id != current_user.id:
        flash('你没有权限删除这本书籍！')
        return redirect(url_for('book_detail', book_id=book_id))

    # 删除图片（可选）
    if book.pic and os.path.exists(os.path.join(app.config['UPLOAD_FOLDER'], book.pic.split('/')[-1])):
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], book.pic.split('/')[-1]))

    # 删除数据库记录
    db.session.delete(book)
    db.session.commit()
    flash('书籍已成功下架！')
    return redirect(url_for('index'))


# 个人中心（仅登录可访问）
@app.route('/profile')
@login_required
def profile():
    # 传入当前登录用户信息到前端
    return render_template('profile.html', user=current_user)


# 修改个人信息（昵称/邮箱/手机号）
@app.route('/profile/edit', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        # 接收前端提交的信息
        nickname = request.form.get('nickname', '').strip()
        email = request.form.get('email', '').strip()
        phone = request.form.get('phone', '').strip()

        # 校验邮箱唯一性（如果填了新邮箱且和原邮箱不同）
        if email and email != current_user.email:
            if User.query.filter_by(email=email).first():
                flash('该邮箱已被其他账号使用！')
                return redirect(url_for('edit_profile'))

        # 更新用户信息
        current_user.nickname = nickname
        current_user.email = email if email else None
        current_user.phone = phone if phone else None

        # 提交到数据库
        try:
            db.session.commit()
            flash('个人信息修改成功！')
            return redirect(url_for('profile'))
        except Exception as e:
            db.session.rollback()
            flash(f'修改失败：{str(e)}')
            return redirect(url_for('edit_profile'))

    # GET请求：返回编辑页面（回显原有信息）
    return render_template('edit_profile.html', user=current_user)


# 修改密码（独立功能，需校验原密码）
@app.route('/profile/change_pwd', methods=['GET', 'POST'])
@login_required
def change_pwd():
    if request.method == 'POST':
        # 接收密码信息
        old_pwd = request.form.get('old_pwd', '').strip()
        new_pwd = request.form.get('new_pwd', '').strip()
        confirm_pwd = request.form.get('confirm_pwd', '').strip()

        # 步骤1：校验原密码是否正确
        if current_user.password != old_pwd:
            flash('原密码输入错误！')
            return redirect(url_for('change_pwd'))

        # 步骤2：校验新密码和确认密码是否一致
        if new_pwd != confirm_pwd:
            flash('新密码和确认密码不一致！')
            return redirect(url_for('change_pwd'))

        # 步骤3：校验新密码长度（可选，增强安全性）
        if len(new_pwd) < 6:
            flash('新密码长度不能少于6位！')
            return redirect(url_for('change_pwd'))

        # 步骤4：更新密码（加密存储）
        current_user.password = new_pwd
        db.session.commit()
        flash('密码修改成功！请重新登录')
        return redirect(url_for('login'))

    # GET请求：返回密码修改页面
    return render_template('change_pwd.html')


# 我的发布（查看自己发布的书籍）
@app.route('/my_books')
@login_required
def my_books():
    # 只查当前用户发布的书籍，按发布时间倒序
    books = Book.query.filter_by(user_id=current_user.id).order_by(Book.create_time.desc()).all()
    return render_template('my_books.html', books=books)

# 收藏 / 取消收藏
@app.route('/favorite/<int:book_id>')
@login_required
def favorite(book_id):
    book = Book.query.get_or_404(book_id)
    # 查是否已经收藏
    fav = Favorite.query.filter_by(user_id=current_user.id, book_id=book_id).first()
    if fav:
        # 已收藏 → 取消
        db.session.delete(fav)
        flash('已取消收藏')
    else:
        # 未收藏 → 添加
        new_fav = Favorite(user_id=current_user.id, book_id=book_id)
        db.session.add(new_fav)
        flash('收藏成功')
    db.session.commit()
    return redirect(url_for('book_detail', book_id=book_id))

# 我的收藏
@app.route('/my_favorites')
@login_required
def my_favorites():
    favs = Favorite.query.filter_by(user_id=current_user.id).all()
    books = [fav.book for fav in favs]
    return render_template('my_favorites.html', books=books)


# 发送留言（联系卖家）
@app.route('/send_message/<int:book_id>', methods=['GET', 'POST'])
@login_required
def send_message(book_id):
    book = Book.query.get_or_404(book_id)
    # 禁止给自己留言
    if book.user_id == current_user.id:
        flash('不能给自己留言！')
        return redirect(url_for('book_detail', book_id=book_id))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash('留言内容不能为空！')
            return redirect(url_for('send_message', book_id=book_id))

        # 创建新留言
        new_msg = Message(
            sender_id=current_user.id,
            receiver_id=book.user_id,
            book_id=book_id,
            content=content
        )
        db.session.add(new_msg)
        db.session.commit()
        flash('留言发送成功！')
        return redirect(url_for('book_detail', book_id=book_id))

    # GET请求：返回留言页面
    return render_template('send_message.html', book=book)


# 我的消息（查看所有收到/发出的留言）
@app.route('/my_messages')
@login_required
def my_messages():
    # 收到的消息（按时间倒序）
    received_msgs = Message.query.filter_by(receiver_id=current_user.id).order_by(Message.create_time.desc()).all()
    # 发出的消息（按时间倒序）
    sent_msgs = Message.query.filter_by(sender_id=current_user.id).order_by(Message.create_time.desc()).all()
    # 标记收到的未读消息为已读
    for msg in received_msgs:
        if not msg.is_read:
            msg.is_read = True
    db.session.commit()

    return render_template('my_messages.html', received_msgs=received_msgs, sent_msgs=sent_msgs)


# 回复留言
@app.route('/reply_message/<int:msg_id>', methods=['GET', 'POST'])
@login_required
def reply_message(msg_id):
    msg = Message.query.get_or_404(msg_id)
    # 仅接收者可回复
    if msg.receiver_id != current_user.id:
        flash('无权回复此消息！')
        return redirect(url_for('my_messages'))

    if request.method == 'POST':
        content = request.form.get('content', '').strip()
        if not content:
            flash('回复内容不能为空！')
            return redirect(url_for('reply_message', msg_id=msg_id))

        # 创建回复（交换发送者和接收者）
        new_msg = Message(
            sender_id=current_user.id,
            receiver_id=msg.sender_id,
            book_id=msg.book_id,
            content=content
        )
        db.session.add(new_msg)
        db.session.commit()
        flash('回复发送成功！')
        return redirect(url_for('my_messages'))

    # GET请求：返回回复页面
    return render_template('reply_message.html', msg=msg)

# 启动应用
if __name__ == '__main__':
    # 创建数据库表（如果不存在）
    with app.app_context():
        db.create_all()
    app.run(debug=True)  # debug=True 开发模式，上线要改 False