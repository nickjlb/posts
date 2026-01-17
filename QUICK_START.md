# Quick Start Guide

Get your blog up and running in 5 minutes!

## Running the CMS

**Double-click `BlogCMS.exe`**

That's it! Your browser will automatically open to the CMS admin panel at:
```
http://127.0.0.1:5000/cms
```

## Creating Your First Post

### Step 1: Click "New Post"

Look for the green **"+ New Post"** button in the top right.

### Step 2: Add Your Content

**Title** (required)
```
My First Blog Post
```

**Content** (optional)
```
This is my first post! I'm excited to share my photography with the world.
```

**Tags** (optional)
```
photography, travel, sunset
```

> Tip: Separate tags with commas

### Step 3: Add Images

**Drag & Drop:**
1. Drag images from your file explorer
2. Drop them in the upload area
3. Watch them upload!

**Or Click to Browse:**
1. Click the upload area
2. Select one or multiple images
3. Click Open

> Tip: You can upload multiple images at once!

### Step 4: Publish or Save as Draft

**Draft**: Work in progress, not visible on blog
**Published**: Live on your blog

Select your choice and click **"Save Post"**

## Viewing Your Blog

Click the **"View Blog"** button in the top right of the CMS.

Your blog will open in a new tab at:
```
http://127.0.0.1:5000/
```

## Managing Posts

### Edit a Post

1. Go to CMS home (`/cms`)
2. Find your post
3. Click **"Edit"**
4. Make changes
5. Click **"Save Post"**

### Delete a Post

1. Go to CMS home
2. Find your post
3. Click **"Delete"**
4. Confirm deletion

> Warning: This cannot be undone!

### Change Post Status

1. Edit the post
2. Change from Draft to Published (or vice versa)
3. Save

## Using the Blog

### Filter by Tags

At the top of the blog, you'll see all your tags:
- Click **"All"** to see everything
- Click any tag to filter by that tag

### Change Posts Per Page

Use the dropdown in the top right:
- **6 posts** - Fewer, larger images
- **12 posts** - Balanced (default)
- **24 posts** - More posts visible
- **48 posts** - Maximum posts

### View Images

**Click any image** to open the lightbox viewer:
- **ESC** to close
- **Arrow keys** to navigate
- **Click outside** to close

## Pro Tips

### Image Quality
- Upload high-resolution images for best quality
- The CMS automatically handles display sizing
- No need to resize before uploading

### Organizing with Tags
- Use consistent tag names (lowercase recommended)
- Use 3-5 tags per post for best organization
- Popular tags appear more prominently

### Draft Workflow
1. Create post as Draft
2. Add images and content over time
3. Preview by temporarily setting to Published
4. Switch back to Draft if needed
5. Publish when ready!

### Multiple Images
- First image becomes the "featured" image in grid view
- Multiple images create a beautiful collage
- Click any image in the collage to view all images

## Backing Up Your Blog

**Important files:**
- `blog.db` - All your posts and metadata
- `static/uploads/` - All your images

**To backup:**
1. Close BlogCMS.exe
2. Copy both files/folders above
3. Store in a safe location (cloud, external drive, etc.)

**To restore:**
1. Replace the files in the BlogCMS folder
2. Run BlogCMS.exe

## Common Questions

**Q: Can others see my blog?**
A: Only on your local computer. It's running at `127.0.0.1` (localhost).

**Q: How do I share my blog?**
A: Currently, it's local-only. You'd need to deploy to a web server to share publicly.

**Q: Can I change the blog title?**
A: Yes! Edit `templates/blog.html` and change "My Blog" to your title.

**Q: How do I stop the server?**
A: Close the command prompt window that opened when you ran BlogCMS.exe.

**Q: Can I run this on Mac/Linux?**
A: Yes! Use `python app.py` instead of the .exe file.

**Q: What image formats are supported?**
A: All common formats: JPG, PNG, GIF, WebP, etc.

**Q: Is there a file size limit?**
A: Default max is 100MB per image (configurable in `app.py`).

**Q: Can I use markdown in posts?**
A: Currently, content is displayed as plain text. You can add HTML support if needed.

## Next Steps

Now that you've got the basics:

1. **Create 3-5 sample posts** to see how the masonry layout looks
2. **Experiment with different image counts** per post
3. **Try the tag filtering** to organize your content
4. **Customize the colors** in `static/css/style.css` if desired

## Need More Help?

- Read the full **README.md** for detailed features
- Check **INSTALL_WINDOWS.md** for build instructions
- Look at the code comments for customization ideas

---

**Happy blogging!** 📸✨
