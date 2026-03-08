# secondhand-book-platform

# 二手书交易平台 📚

一个基于 Flask 的二手书籍交易网站，提供书籍发布、浏览、收藏、留言等功能。

## 项目介绍

本项目是一个 B/S 架构的二手书交易平台，用户可以在平台上发布闲置书籍信息，浏览他人发布的书籍，进行收藏和私信联系。系统采用 Flask 框架开发，使用 MySQL 数据库存储数据，界面简洁易用。

### 技术栈

- **后端框架**: Flask
- **数据库**: MySQL + SQLAlchemy ORM
- **前端**: HTML + CSS
- **用户认证**: Flask-Login
- **图片处理**: Werkzeug

## 环境配置

### 系统要求

- Python 3.7+
- MySQL 5.7+
- Windows/Linux/MacOS

### 依赖安装

1. 安装 Python 依赖包：

```
bash
pip install flask flask-sqlalchemy flask-login pymysql werkzeug
```
2. 创建 MySQL 数据库：

```
sql
CREATE DATABASE second_hand_books CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```
3. 修改数据库配置（在 `app.py` 第 17 行）：

```
python
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://用户名：密码@localhost/second_hand_books'
```
### 目录结构

```

secondhand-book-platform/
├── static/
│   └── css/
│       └── style.css          # 样式文件
├── templates/                  # HTML 模板
│   ├── index.html             # 首页
│   ├── login.html             # 登录页
│   ├── register.html          # 注册页
│   ├── add_book.html          # 发布书籍页
│   ├── book_detail.html       # 书籍详情页
│   ├── edit_book.html         # 编辑书籍页
│   ├── my_books.html          # 我的书籍页
│   ├── my_favorites.html      # 我的收藏页
│   ├── my_messages.html       # 我的消息页
│   ├── profile.html           # 个人中心页
│   ├── edit_profile.html      # 编辑资料页
│   ├── change_pwd.html        # 修改密码页
│   ├── send_message.html      # 发送留言页
│   └── reply_message.html     # 回复留言页
├── static/upload/              # 书籍图片上传目录（自动创建）
└── app.py                      # 主程序入口
```
## 运行步骤

### 1. 启动 MySQL 服务

确保 MySQL 服务正在运行：

```
bash
# Windows
net start MySQL

# Linux/MacOS
sudo service mysql start
```
### 2. 运行应用

```
bash
python app.py
```
首次运行时会自动创建数据库表。

### 3. 访问网站

打开浏览器访问：`http://127.0.0.1:5000/`

### 4. 停止服务

按 `Ctrl+C` 停止开发服务器。

## 功能说明

### 用户系统 🔐

- **注册**: 支持用户名、昵称、邮箱、手机号注册
- **登录/退出**: 用户认证和会话管理
- **个人中心**: 查看和编辑个人信息
- **修改密码**: 独立密码修改功能

### 书籍管理 📖

- **发布书籍**: 
  - 填写书名、作者、价格、描述
  - 支持上传封面图片
  - 自动关联发布者信息
  
- **浏览书籍**: 
  - 首页展示所有书籍（按时间倒序）
  - 支持按书名/作者搜索
  - 书籍详情查看
  
- **编辑书籍**: 
  - 仅发布者可以编辑
  - 可修改所有信息和图片
  
- **删除书籍**: 
  - 仅发布者可以删除
  - 同时删除关联图片

### 收藏功能 ⭐

- **收藏书籍**: 点击收藏感兴趣的书籍
- **取消收藏**: 已收藏的书籍可取消
- **我的收藏**: 统一管理所有收藏

### 消息系统 💬

- **发送留言**: 
  - 向书籍发布者发送私信
  - 禁止给自己留言
  
- **我的消息**: 
  - 查看收到和发出的留言
  - 自动标记已读消息
  
- **回复留言**: 
  - 接收者可回复留言
  - 支持多轮对话

### 安全特性 🔒

- 用户密码加密存储（计划中）
- 登录验证和权限控制
- 操作权限校验（只能编辑/删除自己的书籍）
- Flash 消息提示
- SQL 注入防护（SQLAlchemy ORM）

## 快速上手指南

### 第一步：注册账号
访问首页 → 点击"注册" → 填写用户名和密码 → 完成注册

### 第二步：发布书籍
登录后 → 点击"发布书籍" → 填写书籍信息 → 上传图片 → 提交

### 第三步：浏览购买
- 浏览首页书籍列表
- 使用搜索功能查找特定书籍
- 点击书籍查看详情
- 收藏感兴趣的书籍
- 给卖家发送留言咨询

### 第四步：管理个人内容
- **我的发布**: 查看和管理自己发布的书籍
- **我的收藏**: 查看所有收藏的书籍
- **我的消息**: 查看和回复买家留言
- **个人中心**: 修改个人资料和密码

## 注意事项 ⚠️

1. **开发模式**: 当前使用 `debug=True`，仅限开发环境，生产环境需改为 `False`
2. **密钥安全**: `app.secret_key` 需使用复杂随机字符串
3. **图片上传**: 限制最大 16MB，需确保 `static/upload` 目录有写权限
4. **数据库连接**: 上线时需修改为生产环境数据库配置
5. **密码加密**: 当前版本密码未加密存储，建议启用加密功能

## 后续优化方向 🚀

- [ ] 密码加密存储（使用 generate_password_hash）
- [ ] 图片压缩和缩略图生成
- [ ] 分页功能
- [ ] 用户头像上传
- [ ] 书籍分类标签
- [ ] 站内通知系统
- [ ] 交易评价系统
- [ ] 移动端适配优化

## 常见问题

**Q: 数据库连接失败？**
A: 检查 MySQL 服务是否启动，确认账号密码正确，数据库是否存在。

**Q: 图片上传失败？**
A: 确保 `static/upload` 目录存在且有写权限，检查文件大小不超过 16MB。

**Q: 页面显示异常？**
A: 清除浏览器缓存，检查 CSS 文件路径是否正确。

---

**开发者**: 个人项目  
**版本**: v1.0  
**许可证**: MIT License
