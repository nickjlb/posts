import os
import sys
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
from pathlib import Path

# Get the base directory (works for both script and exe)
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path(os.path.dirname(sys.executable))
else:
    BASE_DIR = Path(__file__).parent
    DATA_DIR = BASE_DIR

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-change-this'
app.config['UPLOAD_FOLDER'] = DATA_DIR / 'static' / 'uploads'
app.config['DATABASE'] = DATA_DIR / 'blog.db'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Database initialization
def init_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    cursor = conn.cursor()

    # Create posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            content TEXT,
            status TEXT DEFAULT 'draft',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Create images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            filename TEXT NOT NULL,
            order_index INTEGER DEFAULT 0,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
    ''')

    # Create tags table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    ''')

    # Create post_tags junction table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS post_tags (
            post_id INTEGER,
            tag_id INTEGER,
            PRIMARY KEY (post_id, tag_id),
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE,
            FOREIGN KEY (tag_id) REFERENCES tags (id) ON DELETE CASCADE
        )
    ''')

    # Create settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    ''')

    # Set default blog title if not exists
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('blog_title', 'My Blog')")

    conn.commit()
    conn.close()

def get_setting(key, default=None):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result['value'] if result else default

def set_setting(key, value):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)', (key, value))
    conn.commit()
    conn.close()

def get_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn

# Routes
@app.route('/')
def blog():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    tag_filter = request.args.get('tag', None)
    view_mode = request.args.get('view', 'masonry')  # masonry or grid

    conn = get_db()
    cursor = conn.cursor()

    # Build query based on tag filter
    if tag_filter:
        query = '''
            SELECT DISTINCT p.* FROM posts p
            JOIN post_tags pt ON p.id = pt.post_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE p.status = 'published' AND t.name = ?
            ORDER BY p.created_at DESC
        '''
        cursor.execute(query, (tag_filter,))
    else:
        cursor.execute('''
            SELECT * FROM posts
            WHERE status = 'published'
            ORDER BY created_at DESC
        ''')

    all_posts = cursor.fetchall()
    total_posts = len(all_posts)
    total_pages = (total_posts + per_page - 1) // per_page

    # Paginate
    start = (page - 1) * per_page
    end = start + per_page
    posts = all_posts[start:end]

    # Get images and tags for each post
    posts_data = []
    for post in posts:
        cursor.execute('SELECT * FROM images WHERE post_id = ? ORDER BY order_index', (post['id'],))
        images = cursor.fetchall()

        cursor.execute('''
            SELECT t.name FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            WHERE pt.post_id = ?
        ''', (post['id'],))
        tags = [row['name'] for row in cursor.fetchall()]

        posts_data.append({
            'id': post['id'],
            'title': post['title'],
            'content': post['content'],
            'images': [dict(img) for img in images],
            'tags': tags,
            'created_at': post['created_at']
        })

    # Get all tags for filter
    cursor.execute('SELECT DISTINCT name FROM tags ORDER BY name')
    all_tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    blog_title = get_setting('blog_title', 'My Blog')

    return render_template('blog.html',
                         posts=posts_data,
                         page=page,
                         per_page=per_page,
                         total_pages=total_pages,
                         tag_filter=tag_filter,
                         all_tags=all_tags,
                         blog_title=blog_title,
                         view_mode=view_mode)

@app.route('/post/<int:post_id>')
def view_post(post_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM posts WHERE id = ? AND status = "published"', (post_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return "Post not found", 404

    cursor.execute('SELECT * FROM images WHERE post_id = ? ORDER BY order_index', (post_id,))
    images = cursor.fetchall()

    cursor.execute('''
        SELECT t.name FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        WHERE pt.post_id = ?
    ''', (post_id,))
    tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    post_data = {
        'id': post['id'],
        'title': post['title'],
        'content': post['content'],
        'images': [dict(img) for img in images],
        'tags': tags,
        'created_at': post['created_at']
    }

    return render_template('post.html', post=post_data)

@app.route('/cms')
def cms():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = cursor.fetchall()

    posts_data = []
    for post in posts:
        cursor.execute('SELECT COUNT(*) as count FROM images WHERE post_id = ?', (post['id'],))
        image_count = cursor.fetchone()['count']

        cursor.execute('''
            SELECT t.name FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            WHERE pt.post_id = ?
        ''', (post['id'],))
        tags = [row['name'] for row in cursor.fetchall()]

        posts_data.append({
            'id': post['id'],
            'title': post['title'],
            'status': post['status'],
            'image_count': image_count,
            'tags': tags,
            'created_at': post['created_at']
        })

    conn.close()

    return render_template('cms.html', posts=posts_data)

@app.route('/cms/images')
def cms_images():
    tag_filter = request.args.get('tag', None)

    conn = get_db()
    cursor = conn.cursor()

    # Get all images with their post information
    if tag_filter:
        query = '''
            SELECT DISTINCT i.*, p.title as post_title, p.id as post_id
            FROM images i
            JOIN posts p ON i.post_id = p.id
            JOIN post_tags pt ON p.id = pt.post_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE t.name = ?
            ORDER BY i.id DESC
        '''
        cursor.execute(query, (tag_filter,))
    else:
        cursor.execute('''
            SELECT i.*, p.title as post_title, p.id as post_id
            FROM images i
            JOIN posts p ON i.post_id = p.id
            ORDER BY i.id DESC
        ''')

    images = cursor.fetchall()

    # Get all tags from posts that have images
    cursor.execute('''
        SELECT DISTINCT t.name
        FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        JOIN posts p ON pt.post_id = p.id
        JOIN images i ON p.id = i.post_id
        ORDER BY t.name
    ''')
    all_tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    images_data = [dict(img) for img in images]

    return render_template('images.html',
                         images=images_data,
                         tag_filter=tag_filter,
                         all_tags=all_tags)

@app.route('/images')
def blog_images():
    tag_filter = request.args.get('tag', None)

    conn = get_db()
    cursor = conn.cursor()

    # Get all images with their post information (published posts only)
    if tag_filter:
        query = '''
            SELECT DISTINCT i.*, p.title as post_title, p.id as post_id
            FROM images i
            JOIN posts p ON i.post_id = p.id
            JOIN post_tags pt ON p.id = pt.post_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE p.status = 'published' AND t.name = ?
            ORDER BY i.id DESC
        '''
        cursor.execute(query, (tag_filter,))
    else:
        cursor.execute('''
            SELECT i.*, p.title as post_title, p.id as post_id
            FROM images i
            JOIN posts p ON i.post_id = p.id
            WHERE p.status = 'published'
            ORDER BY i.id DESC
        ''')

    images = cursor.fetchall()

    # Get all tags from published posts that have images
    cursor.execute('''
        SELECT DISTINCT t.name
        FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        JOIN posts p ON pt.post_id = p.id
        JOIN images i ON p.id = i.post_id
        WHERE p.status = 'published'
        ORDER BY t.name
    ''')
    all_tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    images_data = [dict(img) for img in images]
    blog_title = get_setting('blog_title', 'My Blog')

    return render_template('blog_images.html',
                         images=images_data,
                         tag_filter=tag_filter,
                         all_tags=all_tags,
                         blog_title=blog_title)

@app.route('/cms/settings', methods=['GET', 'POST'])
def cms_settings():
    if request.method == 'POST':
        blog_title = request.form.get('blog_title', 'My Blog')
        set_setting('blog_title', blog_title)
        return redirect(url_for('cms'))

    blog_title = get_setting('blog_title', 'My Blog')
    return render_template('settings.html', blog_title=blog_title)

@app.route('/cms/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        return save_post()
    return render_template('edit_post.html', post=None)

@app.route('/cms/post/<int:post_id>/edit', methods=['GET', 'POST'])
def edit_post(post_id):
    if request.method == 'POST':
        return save_post(post_id)

    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM posts WHERE id = ?', (post_id,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return "Post not found", 404

    cursor.execute('SELECT * FROM images WHERE post_id = ? ORDER BY order_index', (post_id,))
    images = cursor.fetchall()

    cursor.execute('''
        SELECT t.name FROM tags t
        JOIN post_tags pt ON t.id = pt.tag_id
        WHERE pt.post_id = ?
    ''', (post_id,))
    tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    post_data = {
        'id': post['id'],
        'title': post['title'],
        'content': post['content'],
        'status': post['status'],
        'images': [dict(img) for img in images],
        'tags': tags
    }

    return render_template('edit_post.html', post=post_data)

def save_post(post_id=None):
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    status = request.form.get('status', 'draft')
    tags_input = request.form.get('tags', '')
    pending_images = request.form.get('pending_images', '')

    conn = get_db()
    cursor = conn.cursor()

    if post_id:
        # Update existing post
        cursor.execute('''
            UPDATE posts
            SET title = ?, content = ?, status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, content, status, post_id))
    else:
        # Create new post
        cursor.execute('''
            INSERT INTO posts (title, content, status)
            VALUES (?, ?, ?)
        ''', (title, content, status))
        post_id = cursor.lastrowid

        # Associate pending images with the new post
        if pending_images:
            filenames = [f.strip() for f in pending_images.split(',') if f.strip()]
            for index, filename in enumerate(filenames):
                cursor.execute('''
                    INSERT INTO images (post_id, filename, order_index)
                    VALUES (?, ?, ?)
                ''', (post_id, filename, index))

    # Handle tags
    cursor.execute('DELETE FROM post_tags WHERE post_id = ?', (post_id,))

    if tags_input:
        tag_names = [tag.strip() for tag in tags_input.split(',') if tag.strip()]
        for tag_name in tag_names:
            cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (tag_name,))
            cursor.execute('SELECT id FROM tags WHERE name = ?', (tag_name,))
            tag_id = cursor.fetchone()['id']
            cursor.execute('INSERT INTO post_tags (post_id, tag_id) VALUES (?, ?)', (post_id, tag_id))

    conn.commit()
    conn.close()

    return redirect(url_for('cms'))

@app.route('/cms/post/<int:post_id>/delete', methods=['POST'])
def delete_post(post_id):
    conn = get_db()
    cursor = conn.cursor()

    # Get images to delete files
    cursor.execute('SELECT filename FROM images WHERE post_id = ?', (post_id,))
    images = cursor.fetchall()

    for img in images:
        try:
            os.remove(app.config['UPLOAD_FOLDER'] / img['filename'])
        except:
            pass

    # Delete post (cascade will handle images, tags)
    cursor.execute('DELETE FROM posts WHERE id = ?', (post_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('cms'))

@app.route('/cms/upload', methods=['POST'])
def upload_image():
    if 'file' not in request.files:
        return jsonify({'error': 'No file'}), 400

    file = request.files['file']
    post_id = request.form.get('post_id', type=int)

    if file.filename == '':
        return jsonify({'error': 'No filename'}), 400

    if file:
        filename = secure_filename(file.filename)
        # Add timestamp to avoid conflicts
        name, ext = os.path.splitext(filename)
        filename = f"{name}_{int(datetime.now().timestamp())}{ext}"

        filepath = app.config['UPLOAD_FOLDER'] / filename
        file.save(filepath)

        if post_id:
            conn = get_db()
            cursor = conn.cursor()

            # Get max order_index
            cursor.execute('SELECT MAX(order_index) as max_order FROM images WHERE post_id = ?', (post_id,))
            result = cursor.fetchone()
            order_index = (result['max_order'] or -1) + 1

            cursor.execute('''
                INSERT INTO images (post_id, filename, order_index)
                VALUES (?, ?, ?)
            ''', (post_id, filename, order_index))

            conn.commit()
            conn.close()

        return jsonify({'filename': filename, 'url': url_for('static', filename=f'uploads/{filename}')})

    return jsonify({'error': 'Upload failed'}), 400

@app.route('/cms/image/<int:image_id>/delete', methods=['POST'])
def delete_image(image_id):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT filename FROM images WHERE id = ?', (image_id,))
    image = cursor.fetchone()

    if image:
        try:
            os.remove(app.config['UPLOAD_FOLDER'] / image['filename'])
        except:
            pass

        cursor.execute('DELETE FROM images WHERE id = ?', (image_id,))
        conn.commit()

    conn.close()

    return jsonify({'success': True})

@app.route('/cms/image/delete-file/<filename>', methods=['POST'])
def delete_image_file(filename):
    # Delete a pending image file (not yet associated with a post)
    try:
        # Security: only allow deleting from uploads folder
        filepath = app.config['UPLOAD_FOLDER'] / secure_filename(filename)
        if filepath.exists():
            os.remove(filepath)
        return jsonify({'success': True})
    except:
        return jsonify({'success': False}), 500

@app.route('/static/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def open_browser():
    webbrowser.open('http://127.0.0.1:5000/cms')

if __name__ == '__main__':
    init_db()

    # Open browser after a short delay
    if not os.environ.get('WERKZEUG_RUN_MAIN'):
        Timer(1.5, open_browser).start()

    print("=" * 60)
    print("🌟 Blog CMS is starting...")
    print("=" * 60)
    print("\n📝 CMS Admin: http://127.0.0.1:5000/cms")
    print("🌐 Blog View:  http://127.0.0.1:5000/")
    print("\n💡 Press CTRL+C to stop the server")
    print("=" * 60)

    app.run(debug=False, port=5000)
