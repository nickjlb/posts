import os
import sys
import webbrowser
from threading import Timer
from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
from werkzeug.utils import secure_filename
from datetime import datetime
import sqlite3
from pathlib import Path
import re
import json
from PIL import Image, ExifTags
import markdown

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
            slug TEXT UNIQUE,
            status TEXT DEFAULT 'draft',
            featured INTEGER DEFAULT 0,
            category_id INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES categories (id) ON DELETE SET NULL
        )
    ''')

    # Add new columns to existing posts table
    try:
        cursor.execute('ALTER TABLE posts ADD COLUMN slug TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE posts ADD COLUMN featured INTEGER DEFAULT 0')
    except: pass
    try:
        cursor.execute('ALTER TABLE posts ADD COLUMN category_id INTEGER')
    except: pass

    # Create images table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS images (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            post_id INTEGER,
            filename TEXT NOT NULL,
            order_index INTEGER DEFAULT 0,
            caption TEXT,
            alt_text TEXT,
            camera TEXT,
            lens TEXT,
            iso TEXT,
            aperture TEXT,
            shutter_speed TEXT,
            focal_length TEXT,
            FOREIGN KEY (post_id) REFERENCES posts (id) ON DELETE CASCADE
        )
    ''')

    # Add new columns to existing images table
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN caption TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN alt_text TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN camera TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN lens TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN iso TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN aperture TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN shutter_speed TEXT')
    except: pass
    try:
        cursor.execute('ALTER TABLE images ADD COLUMN focal_length TEXT')
    except: pass

    # Create categories table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT
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

    # Set default settings if not exists
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('blog_title', 'My Blog')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('font_headings', 'system')")
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('font_body', 'system')")

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

# Helper functions
def generate_slug(title):
    """Generate URL-friendly slug from title"""
    slug = title.lower()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    return slug.strip('-')

def extract_exif_data(filepath):
    """Extract EXIF data from image"""
    try:
        img = Image.open(filepath)
        exif_data = img._getexif()
        if not exif_data:
            return {}

        exif = {}
        for tag_id, value in exif_data.items():
            tag = ExifTags.TAGS.get(tag_id, tag_id)
            exif[tag] = value

        # Extract useful fields
        result = {}
        result['camera'] = exif.get('Model', '')
        result['lens'] = exif.get('LensModel', '')
        result['iso'] = str(exif.get('ISOSpeedRatings', ''))

        # Format aperture
        if 'FNumber' in exif:
            aperture = exif['FNumber']
            if isinstance(aperture, tuple):
                result['aperture'] = f"f/{aperture[0]/aperture[1]:.1f}"
            else:
                result['aperture'] = f"f/{aperture}"

        # Format shutter speed
        if 'ExposureTime' in exif:
            exposure = exif['ExposureTime']
            if isinstance(exposure, tuple):
                if exposure[0] == 1:
                    result['shutter_speed'] = f"1/{exposure[1]}"
                else:
                    result['shutter_speed'] = f"{exposure[0]/exposure[1]:.2f}s"
            else:
                result['shutter_speed'] = f"{exposure}s"

        # Format focal length
        if 'FocalLength' in exif:
            focal = exif['FocalLength']
            if isinstance(focal, tuple):
                result['focal_length'] = f"{focal[0]/focal[1]:.0f}mm"
            else:
                result['focal_length'] = f"{focal}mm"

        # Extract keywords/tags from EXIF
        keywords = []
        if 'Keywords' in exif:
            keywords = exif['Keywords'] if isinstance(exif['Keywords'], list) else [exif['Keywords']]
        elif 'XPKeywords' in exif:
            # Windows tags
            try:
                kw = exif['XPKeywords'].decode('utf-16').rstrip('\x00')
                keywords = [k.strip() for k in kw.split(';') if k.strip()]
            except:
                pass

        result['keywords'] = keywords
        return result
    except Exception as e:
        print(f"Error extracting EXIF: {e}")
        return {}

def optimize_image(filepath):
    """Optimize and resize image if needed"""
    try:
        img = Image.open(filepath)

        # Convert RGBA to RGB if needed
        if img.mode == 'RGBA':
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[3])
            img = background

        # Resize if too large (max 2000px on longest side)
        max_size = 2000
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)

        # Save optimized
        img.save(filepath, 'JPEG', quality=85, optimize=True)
        return True
    except Exception as e:
        print(f"Error optimizing image: {e}")
        return False

def render_markdown(text):
    """Convert markdown to HTML"""
    if not text:
        return ''
    return markdown.markdown(text, extensions=['nl2br', 'fenced_code'])

# Routes
@app.route('/')
def blog():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 12, type=int)
    tag_filter = request.args.get('tag', None)
    view_mode = request.args.get('view', 'masonry')  # masonry or grid
    search_query = request.args.get('q', '').strip()

    conn = get_db()
    cursor = conn.cursor()

    # Build query based on filters
    if search_query:
        # Search in title and content
        search_term = f'%{search_query}%'
        cursor.execute('''
            SELECT * FROM posts
            WHERE status = 'published' AND (title LIKE ? OR content LIKE ?)
            ORDER BY featured DESC, created_at DESC
        ''', (search_term, search_term))
    elif tag_filter:
        query = '''
            SELECT DISTINCT p.* FROM posts p
            JOIN post_tags pt ON p.id = pt.post_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE p.status = 'published' AND t.name = ?
            ORDER BY p.featured DESC, p.created_at DESC
        '''
        cursor.execute(query, (tag_filter,))
    else:
        cursor.execute('''
            SELECT * FROM posts
            WHERE status = 'published'
            ORDER BY featured DESC, created_at DESC
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
            'content': render_markdown(post['content']) if post['content'] else '',
            'slug': post['slug'] if 'slug' in post.keys() else '',
            'featured': post['featured'] if 'featured' in post.keys() else 0,
            'images': [dict(img) for img in images],
            'tags': tags,
            'created_at': post['created_at']
        })

    # Get all tags for filter
    cursor.execute('SELECT DISTINCT name FROM tags ORDER BY name')
    all_tags = [row['name'] for row in cursor.fetchall()]

    conn.close()

    blog_title = get_setting('blog_title', 'My Blog')
    blog_logo = get_setting('blog_logo', '')
    blog_font = get_setting('blog_font', 'system')

    return render_template('blog.html',
                         posts=posts_data,
                         page=page,
                         per_page=per_page,
                         total_pages=total_posts,
                         tag_filter=tag_filter,
                         all_tags=all_tags,
                         blog_title=blog_title,
                         blog_logo=blog_logo,
                         blog_font=blog_font,
                         view_mode=view_mode,
                         search_query=search_query)

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

    # Get related posts (posts sharing tags with this one)
    cursor.execute('''
        SELECT DISTINCT p.*, COUNT(DISTINCT pt2.tag_id) as shared_tags
        FROM posts p
        JOIN post_tags pt2 ON p.id = pt2.post_id
        WHERE pt2.tag_id IN (
            SELECT pt.tag_id FROM post_tags pt WHERE pt.post_id = ?
        )
        AND p.id != ?
        AND p.status = 'published'
        GROUP BY p.id
        ORDER BY shared_tags DESC, p.created_at DESC
        LIMIT 3
    ''', (post_id, post_id))
    related_posts = []
    for related in cursor.fetchall():
        # Get first image for each related post
        cursor.execute('SELECT filename FROM images WHERE post_id = ? ORDER BY order_index LIMIT 1', (related['id'],))
        img_row = cursor.fetchone()
        related_posts.append({
            'id': related['id'],
            'title': related['title'],
            'slug': related['slug'] if 'slug' in related.keys() else '',
            'created_at': related['created_at'],
            'image': img_row['filename'] if img_row else None
        })

    conn.close()

    post_data = {
        'id': post['id'],
        'title': post['title'],
        'content': render_markdown(post['content']),
        'images': [dict(img) for img in images],
        'tags': tags,
        'created_at': post['created_at'],
        'slug': post['slug'] if 'slug' in post.keys() else ''
    }

    blog_title = get_setting('blog_title', 'My Blog')
    blog_logo = get_setting('blog_logo', '')
    blog_font = get_setting('blog_font', 'system')

    return render_template('post.html', post=post_data, related_posts=related_posts,
                         blog_title=blog_title, blog_logo=blog_logo, blog_font=blog_font)

@app.route('/p/<slug>')
def view_post_by_slug(slug):
    """View post by slug instead of ID"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM posts WHERE slug = ? AND status = "published"', (slug,))
    post = cursor.fetchone()

    if not post:
        conn.close()
        return "Post not found", 404

    # Use the existing view_post logic
    return view_post(post['id'])

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
    blog_logo = get_setting('blog_logo', '')
    blog_font = get_setting('blog_font', 'system')

    return render_template('blog_images.html',
                         images=images_data,
                         tag_filter=tag_filter,
                         all_tags=all_tags,
                         blog_title=blog_title,
                         blog_logo=blog_logo,
                         blog_font=blog_font)

@app.route('/cms/settings', methods=['GET', 'POST'])
def cms_settings():
    if request.method == 'POST':
        blog_title = request.form.get('blog_title', 'My Blog')
        set_setting('blog_title', blog_title)

        # Handle logo upload
        if 'logo' in request.files:
            logo_file = request.files['logo']
            if logo_file and logo_file.filename:
                # Save old logo path to delete it later
                old_logo = get_setting('blog_logo', '')

                # Generate unique filename
                import uuid
                ext = os.path.splitext(logo_file.filename)[1]
                logo_filename = f"logo_{uuid.uuid4().hex[:8]}{ext}"
                logo_path = os.path.join(UPLOAD_FOLDER, logo_filename)

                # Save new logo
                logo_file.save(logo_path)
                set_setting('blog_logo', logo_filename)

                # Delete old logo if it exists
                if old_logo:
                    old_logo_path = os.path.join(UPLOAD_FOLDER, old_logo)
                    if os.path.exists(old_logo_path):
                        os.remove(old_logo_path)

        # Handle logo removal
        if request.form.get('remove_logo') == '1':
            old_logo = get_setting('blog_logo', '')
            if old_logo:
                old_logo_path = os.path.join(UPLOAD_FOLDER, old_logo)
                if os.path.exists(old_logo_path):
                    os.remove(old_logo_path)
            set_setting('blog_logo', '')

        # Handle font selection
        blog_font = request.form.get('blog_font', 'system')
        set_setting('blog_font', blog_font)

        return redirect(url_for('cms'))

    blog_title = get_setting('blog_title', 'My Blog')
    blog_logo = get_setting('blog_logo', '')
    blog_font = get_setting('blog_font', 'system')
    return render_template('settings.html', blog_title=blog_title, blog_logo=blog_logo, blog_font=blog_font)

@app.route('/cms/categories', methods=['GET', 'POST'])
def cms_categories():
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            name = request.form.get('name', '').strip()
            if name:
                cursor.execute('INSERT INTO categories (name) VALUES (?)', (name,))
                conn.commit()

        elif action == 'edit':
            category_id = request.form.get('category_id', type=int)
            name = request.form.get('name', '').strip()
            if category_id and name:
                cursor.execute('UPDATE categories SET name = ? WHERE id = ?', (name, category_id))
                conn.commit()

        elif action == 'delete':
            category_id = request.form.get('category_id', type=int)
            if category_id:
                # Check if any posts use this category
                cursor.execute('SELECT COUNT(*) as count FROM posts WHERE category_id = ?', (category_id,))
                count = cursor.fetchone()['count']
                if count > 0:
                    conn.close()
                    return f"Cannot delete category: {count} post(s) are using it. Please reassign those posts first.", 400
                cursor.execute('DELETE FROM categories WHERE id = ?', (category_id,))
                conn.commit()

        conn.close()
        return redirect(url_for('cms_categories'))

    # Fetch all categories with post counts
    cursor.execute('''
        SELECT c.*, COUNT(p.id) as post_count
        FROM categories c
        LEFT JOIN posts p ON c.id = p.category_id
        GROUP BY c.id
        ORDER BY c.name
    ''')
    categories = cursor.fetchall()
    conn.close()

    return render_template('categories.html', categories=categories)

@app.route('/cms/export')
def export_data():
    """Export all blog data as JSON for backup"""
    import json
    from datetime import datetime

    conn = get_db()
    cursor = conn.cursor()

    # Export posts with tags
    cursor.execute('SELECT * FROM posts ORDER BY created_at DESC')
    posts = []
    for post_row in cursor.fetchall():
        post = dict(post_row)

        # Get tags for this post
        cursor.execute('''
            SELECT t.name FROM tags t
            JOIN post_tags pt ON t.id = pt.tag_id
            WHERE pt.post_id = ?
        ''', (post['id'],))
        post['tags'] = [row['name'] for row in cursor.fetchall()]

        # Get images for this post
        cursor.execute('SELECT * FROM images WHERE post_id = ? ORDER BY order_index', (post['id'],))
        post['images'] = [dict(img) for img in cursor.fetchall()]

        posts.append(post)

    # Export categories
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = [dict(row) for row in cursor.fetchall()]

    # Export settings
    cursor.execute('SELECT * FROM settings')
    settings = {row['key']: row['value'] for row in cursor.fetchall()}

    conn.close()

    # Create export data
    export = {
        'version': '1.0',
        'exported_at': datetime.now().isoformat(),
        'posts': posts,
        'categories': categories,
        'settings': settings
    }

    # Return as JSON download
    response = jsonify(export)
    response.headers['Content-Disposition'] = f'attachment; filename=blog_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    response.headers['Content-Type'] = 'application/json'
    return response

@app.route('/cms/post/new', methods=['GET', 'POST'])
def new_post():
    if request.method == 'POST':
        return save_post()

    # Fetch all categories
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = cursor.fetchall()
    conn.close()

    return render_template('edit_post.html', post=None, categories=categories)

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

    # Fetch all categories
    cursor.execute('SELECT * FROM categories ORDER BY name')
    categories = cursor.fetchall()

    conn.close()

    post_data = {
        'id': post['id'],
        'title': post['title'],
        'content': post['content'],
        'status': post['status'],
        'slug': post['slug'] if 'slug' in post.keys() else '',
        'featured': post['featured'] if 'featured' in post.keys() else 0,
        'category_id': post['category_id'] if 'category_id' in post.keys() else None,
        'images': [dict(img) for img in images],
        'tags': tags
    }

    return render_template('edit_post.html', post=post_data, categories=categories)

def save_post(post_id=None):
    title = request.form.get('title', '')
    content = request.form.get('content', '')
    status = request.form.get('status', 'draft')
    tags_input = request.form.get('tags', '')
    pending_images = request.form.get('pending_images', '')
    slug = request.form.get('slug', '').strip()
    featured = 1 if request.form.get('featured') == 'on' else 0
    category_id = request.form.get('category_id', type=int)

    # Auto-generate slug if not provided
    if not slug:
        slug = generate_slug(title)

    # Ensure slug is unique
    conn = get_db()
    cursor = conn.cursor()
    original_slug = slug
    counter = 1
    while True:
        cursor.execute('SELECT id FROM posts WHERE slug = ? AND id != ?', (slug, post_id or 0))
        if not cursor.fetchone():
            break
        slug = f"{original_slug}-{counter}"
        counter += 1

    if post_id:
        # Update existing post
        cursor.execute('''
            UPDATE posts
            SET title = ?, content = ?, slug = ?, status = ?, featured = ?, category_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (title, content, slug, status, featured, category_id, post_id))
    else:
        # Create new post
        cursor.execute('''
            INSERT INTO posts (title, content, slug, status, featured, category_id)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, content, slug, status, featured, category_id))
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

    # Update image captions and alt text
    for key in request.form:
        if key.startswith('caption_'):
            image_id = key.replace('caption_', '')
            caption = request.form.get(key, '')
            cursor.execute('UPDATE images SET caption = ? WHERE id = ?', (caption, image_id))
        elif key.startswith('alt_'):
            image_id = key.replace('alt_', '')
            alt_text = request.form.get(key, '')
            cursor.execute('UPDATE images SET alt_text = ? WHERE id = ?', (alt_text, image_id))

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

        # Extract EXIF data
        exif_data = extract_exif_data(filepath)

        # Optimize image
        optimize_image(filepath)

        # Auto-add EXIF keywords as tags to post
        if post_id and exif_data.get('keywords'):
            conn = get_db()
            cursor = conn.cursor()
            for keyword in exif_data['keywords']:
                cursor.execute('INSERT OR IGNORE INTO tags (name) VALUES (?)', (keyword,))
                cursor.execute('SELECT id FROM tags WHERE name = ?', (keyword,))
                tag_id = cursor.fetchone()['id']
                cursor.execute('INSERT OR IGNORE INTO post_tags (post_id, tag_id) VALUES (?, ?)', (post_id, tag_id))
            conn.commit()
            conn.close()

        if post_id:
            conn = get_db()
            cursor = conn.cursor()

            # Get max order_index
            cursor.execute('SELECT MAX(order_index) as max_order FROM images WHERE post_id = ?', (post_id,))
            result = cursor.fetchone()
            order_index = (result['max_order'] or -1) + 1

            cursor.execute('''
                INSERT INTO images (post_id, filename, order_index, camera, lens, iso, aperture, shutter_speed, focal_length)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (post_id, filename, order_index,
                  exif_data.get('camera', ''),
                  exif_data.get('lens', ''),
                  exif_data.get('iso', ''),
                  exif_data.get('aperture', ''),
                  exif_data.get('shutter_speed', ''),
                  exif_data.get('focal_length', '')))

            conn.commit()
            conn.close()

        return jsonify({
            'filename': filename,
            'url': url_for('static', filename=f'uploads/{filename}'),
            'exif': exif_data
        })

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
