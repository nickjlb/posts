# Blog CMS - Image-Focused Blog Content Management System

A beautiful, dark-themed, image-focused blog CMS with an intuitive interface. Perfect for photographers, artists, and visual storytellers.

## Features

- **Image-Focused**: Multiple images per post with drag-and-drop upload
- **Beautiful Dark Theme**: Easy on the eyes with a modern dark design
- **Masonry Layout**: Pinterest-style responsive grid layout
- **Image Lightbox**: Click to expand and navigate through images
- **Tag System**: Organize posts with tags and filter by tag
- **Draft/Published**: Work on drafts before publishing
- **Pagination**: Configurable posts per page (6, 12, 24, 48)
- **Responsive Design**: Works perfectly on desktop, tablet, and mobile
- **No Installation**: Single executable file - just run and go!

## Quick Start for Windows

### Option 1: Download Pre-built Executable (Easiest)

1. Download `BlogCMS.exe`
2. Double-click to run
3. Your browser will open automatically to the CMS
4. Start creating posts!

### Option 2: Build from Source

**Prerequisites:**
- Python 3.8 or higher
- pip (Python package manager)

**Steps:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Build the executable:**
   ```bash
   build.bat
   ```

3. **Find your executable:**
   - The file will be in `dist/BlogCMS.exe`
   - Move it anywhere you like - it's completely portable!

## Usage

### Starting the CMS

1. Double-click `BlogCMS.exe`
2. Your default browser will open to the CMS admin page
3. The app runs locally on your computer (no internet required)

### Creating Your First Post

1. Click **"+ New Post"**
2. Add a title
3. Write your content
4. Drag & drop or click to upload images
5. Add tags (comma-separated): `travel, photography, nature`
6. Choose **Draft** or **Published**
7. Click **Save Post**

### Managing Images

- **Upload**: Drag & drop multiple images or click to browse
- **Delete**: Hover over an image and click the × button
- **Reorder**: Images are displayed in upload order

### Publishing Workflow

1. Create posts as **Draft** while working on them
2. Switch to **Published** when ready to share
3. Only published posts appear on the blog

### Viewing Your Blog

- Click **"View Blog"** in the CMS to see your public blog
- Blog URL: `http://127.0.0.1:5000/`
- CMS URL: `http://127.0.0.1:5000/cms`

### Filtering by Tags

1. Go to the blog view
2. Click any tag at the top to filter posts
3. Click "All" to show all posts

### Pagination

1. Use the dropdown at the top right to change posts per page
2. Navigate with Previous/Next buttons at the bottom

## File Storage

All your data is stored in the same folder as `BlogCMS.exe`:

- **blog.db** - SQLite database (posts, tags, metadata)
- **static/uploads/** - Uploaded images

**Backup**: Copy `blog.db` and the `static/uploads/` folder to backup your entire blog!

## Keyboard Shortcuts (Lightbox)

When viewing images in the lightbox:
- **ESC** - Close lightbox
- **←** - Previous image
- **→** - Next image

## Development Mode

If you want to run in development mode:

```bash
python app.py
```

Then visit:
- CMS: http://127.0.0.1:5000/cms
- Blog: http://127.0.0.1:5000/

## Customization

### Change the Blog Title

Edit `templates/blog.html` and change:
```html
<h1 class="blog-title">My Blog</h1>
```

### Adjust Colors

Edit `static/css/style.css` and modify the CSS variables at the top:
```css
:root {
    --bg-primary: #1a1d29;
    --accent-primary: #818cf8;
    /* ... etc */
}
```

### Change Port

Edit `app.py` and modify the last line:
```python
app.run(debug=False, port=5000)  # Change 5000 to your preferred port
```

## Troubleshooting

**App won't start:**
- Make sure no other app is using port 5000
- Check Windows Firewall isn't blocking it
- Try running as Administrator

**Images won't upload:**
- Check file size (max 100MB per image)
- Ensure the static/uploads folder exists
- Verify disk space is available

**Database errors:**
- Delete `blog.db` to start fresh (you'll lose all data!)
- Make sure the file isn't read-only

**Browser doesn't open:**
- Manually navigate to `http://127.0.0.1:5000/cms`

## Technical Details

- **Backend**: Python + Flask
- **Database**: SQLite (single file, no setup needed)
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Styling**: Custom CSS with CSS Grid and Flexbox

## License

Free to use and modify for personal and commercial projects.

## Support

For issues or questions, check the troubleshooting section above.

---

**Happy Blogging!** 📝✨
