# 📚 MD Books Library

A full-featured web application for publishing, reading, and managing books written in Markdown format. Built with Django, it provides a complete platform for authors to publish their work and readers to discover, read, and review content.

---

## 🚀 Features

### For Readers
- 📖 **Browse & Discover** — Explore books by category, tags, popularity, or search
- 📑 **Markdown Rendering** — Read chapters with beautifully rendered Markdown content
- ⭐ **Reviews & Ratings** — Rate books (1–5 stars) and write detailed reviews
- 🔍 **Search & Filter** — Find books by title, category, tag, or sort by popularity/rating
- 👁️ **View Tracking** — See how popular each book is
- 👤 **Public Profiles** — View author profiles with their published works

### For Authors
- ✍️ **Book Publishing** — Create books with cover images, descriptions, and tags
- 📝 **Chapter Management** — Write chapters in Markdown with ordering support
- 📊 **Statistics** — Track views, likes, ratings, and review counts
- 📁 **Category Requests** — Propose new categories for your books
- 🏷️ **Flexible Tagging** — Tag books with relevant keywords for discovery
- 📋 **Draft System** — Save books and chapters as drafts before publishing

### For Moderators
- ✅ **Category Approval** — Review and approve/reject category requests
- 🎛️ **Django Admin** — Full admin interface with custom actions and dashboards
- 📊 **Bulk Operations** — Publish/unpublish books, approve categories in bulk

### Platform Features
- 🔐 **Authentication** — Login, logout, password reset, and profile management
- 💳 **Donation Tracking** — Stripe and PayPal integration for supporter donations
- 🔗 **Social Profiles** — GitHub, YouTube, Twitter, and website links
- 📱 **Responsive Design** — Bootstrap 5 based responsive UI

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3.11+, Django 5.x |
| **Database** | SQLite (dev) / PostgreSQL (prod) |
| **Frontend** | HTML5, Bootstrap 5, JavaScript |
| **Content** | Markdown (rendered to HTML) |
| **Images** | Pillow, Django ImageField |
| **Admin** | Django Admin (customized) |
| **Auth** | Django built-in authentication |
| **Payments** | Stripe, PayPal (integration ready) |

---

## 📁 Project Structure

```
md-books-library/
├── manage.py
├── requirements.txt
├── README.md
│
├── config/                          # Project configuration
│   ├── __init__.py
│   ├── settings.py                  # Django settings
│   ├── urls.py                      # Root URL configuration
│   ├── asgi.py
│   └── wsgi.py
│
├── accounts/                        # User accounts & profiles
│   ├── __init__.py
│   ├── apps.py                      # AppConfig with signal registration
│   ├── models.py                    # Profile model
│   ├── forms.py                     # UserForm, ProfileForm
│   ├── views.py                     # ProfileView, PublicProfileView
│   ├── urls.py                      # Auth & profile URLs
│   ├── admin.py                     # ProfileAdmin
│   └── signals.py                   # Auto-create Profile on User creation
│
├── books/                           # Core library application
│   ├── __init__.py
│   ├── apps.py                      # AppConfig
│   ├── admin.py                     # Admin for all book models
│   ├── urls.py                      # All book-related URLs
│   │
│   ├── models/                      # Data models
│   │   ├── __init__.py
│   │   ├── category.py              # Category (with approval workflow)
│   │   ├── tag.py                   # Tag (keyword labels)
│   │   ├── book.py                  # Book (main entity)
│   │   ├── chapter.py               # Chapter (Markdown content)
│   │   └── review.py                # Review (ratings & comments)
│   │
│   ├── forms/                       # Form classes
│   │   ├── __init__.py
│   │   ├── book.py                  # BookForm
│   │   ├── category.py              # CategoryForm
│   │   ├── chapter.py               # ChapterForm
│   │   ├── review.py                # ReviewForm
│   │   └── tag.py                   # TagForm
│   │
│   ├── views/                       # View classes (CBV)
│   │   ├── __init__.py
│   │   ├── book.py                  # BookListView, DetailView, Create, Update
│   │   ├── category.py              # Category views with approval workflow
│   │   ├── chapter.py               # Chapter views with Markdown rendering
│   │   ├── review.py                # Review views with duplicate prevention
│   │   └── tag.py                   # Tag views with tag cloud
│   │
│   └── templates/books/             # HTML templates
│       ├── book/
│       ├── category/
│       ├── chapter/
│       ├── review/
│       └── tag/
│
├── core/                            # Core pages
│   ├── __init__.py
│   ├── apps.py
│   ├── views.py                     # HomeView (landing page)
│   ├── urls.py
│   └── templates/core/
│       └── home.html
│
├── templates/                       # Global templates
│   └── base.html                    # Base template with Bootstrap
│
├── static/                          # Static files
│   ├── css/
│   ├── js/
│   └── images/
│
└── media/                           # User-uploaded files
    ├── avatars/                     # Profile pictures
    └── books/                       # Book covers & category images
```

---

## 🏗️ Model Relationships

```
User (Django auth)
 │
 └──< Profile (OneToOne)
       │
       ├──< Book (author) ──────────────────┐
       │      │                             │
       │      ├──< Chapter (book)           │
       │      ├──< Review (book, author) ───┤
       │      ├──> Category (FK, nullable)  │
       │      └──<> Tag (M2M)              │
       │                                    │
       ├──< Category (request author) ──────┘
       └──< Category (reviewed_by)
```

| Model | Description | Key Fields |
|-------|-------------|------------|
| **Profile** | Extended user profile | avatar, bio, social links, donations |
| **Book** | A published work | title, slug, description, views, likes |
| **Chapter** | Book section with Markdown | title, content, order, is_published |
| **Category** | Book classification (with approval) | title, status, author, reviewed_by |
| **Tag** | Keyword label | name, slug |
| **Review** | User rating & feedback | rating (1-5), comment |

---

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)
- Git

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/md-books-library.git
cd md-books-library
```

### Step 2: Create Virtual Environment

```bash
# Linux/Mac
python -m venv venv
source venv/bin/activate

# Windows (CMD)
python -m venv venv
venv\Scripts\activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///db.sqlite3
MEDIA_URL=/media/
MEDIA_ROOT=media/
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 7: Collect Static Files

```bash
python manage.py collectstatic
```

### Step 8: Run Development Server

```bash
python manage.py runserver
```

Visit [http://127.0.0.1:8000/](http://127.0.0.1:8000/) to see the application.

---

## 🔗 URL Routes

### Core

| URL | View | Description |
|-----|------|-------------|
| `/` | `HomeView` | Landing page with featured content |

### Accounts (`/accounts/`)

| URL | View | Access |
|-----|------|--------|
| `/accounts/login/` | `LoginView` | Public |
| `/accounts/logout/` | `LogoutView` | Authenticated |
| `/accounts/profile/` | `ProfileView` | Authenticated |
| `/accounts/profile/<username>/` | `PublicProfileView` | Authenticated |
| `/accounts/password/change/` | `PasswordChangeView` | Authenticated |
| `/accounts/password/reset/` | `PasswordResetView` | Public |

### Books (`/books/`)

| URL | View | Access |
|-----|------|--------|
| `/books/` | `BookListView` | Public |
| `/books/book/<slug>/` | `BookDetailView` | Public |
| `/books/book/create/` | `BookCreateView` | Authenticated |
| `/books/book/<slug>/edit/` | `BookUpdateView` | Author only |

### Categories

| URL | View | Access |
|-----|------|--------|
| `/books/categories/` | `CategoryListView` | Public |
| `/books/category/<slug>/` | `CategoryDetailView` | Public |
| `/books/category/create/` | `CategoryCreateView` | Authenticated |
| `/books/category/<slug>/edit/` | `CategoryUpdateView` | Author (pending only) |

### Chapters

| URL | View | Access |
|-----|------|--------|
| `/books/book/<book_slug>/chapters/` | `ChapterListView` | Public |
| `/books/book/<book_slug>/chapter/<slug>/` | `ChapterDetailView` | Public |
| `/books/book/<book_slug>/chapter/create/` | `ChapterCreateView` | Book author |
| `/books/book/<book_slug>/chapter/<slug>/edit/` | `ChapterUpdateView` | Book author |

### Reviews

| URL | View | Access |
|-----|------|--------|
| `/books/reviews/` | `ReviewListView` | Public |
| `/books/review/<pk>/` | `ReviewDetailView` | Public |
| `/books/book/<book_slug>/review/create/` | `ReviewCreateView` | Authenticated |
| `/books/review/<pk>/edit/` | `ReviewUpdateView` | Review author |

### Tags

| URL | View | Access |
|-----|------|--------|
| `/books/tags/` | `TagListView` | Public |
| `/books/tag/<slug>/` | `TagDetailView` | Public |
| `/books/tag/create/` | `TagCreateView` | Authenticated |
| `/books/tag/<slug>/edit/` | `TagUpdateView` | Staff only |

### Admin

| URL | Access |
|-----|--------|
| `/admin/` | Staff/Superuser |

---

## ⚙️ Configuration

### Settings (`config/settings.py`)

Key settings to configure:

```python
# Security
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key')
DEBUG = os.environ.get('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['localhost', '127.0.0.1']

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Local apps
    'accounts.apps.AccountsConfig',
    'books.apps.BooksConfig',
    'core.apps.CoreConfig',
]

# Media files (user uploads)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### Production Deployment

For production, update these settings:

```python
DEBUG = False
ALLOWED_HOSTS = ['yourdomain.com']

# Use PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'md_books_library',
        'USER': 'db_user',
        'PASSWORD': 'db_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
```

---

## 🎛️ Django Admin

The admin interface is fully customized with:

- **Avatar thumbnails** and **status badges**
- **Inline editing** for chapters and reviews within books
- **Custom actions** for bulk publish/unpublish/approve/reject
- **Query optimization** to prevent N+1 problems
- **Clickable links** between related objects
- **Star ratings** and **formatted statistics**

Access at: [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)

---

## 📝 Development

### Running Tests

```bash
python manage.py test
```

### Code Formatting

```bash
pip install black isort
black .
isort .
```

### Making Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Creating a New Feature

1. Create a new branch:
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. Make your changes

3. Run tests:
   ```bash
   python manage.py test
   ```

4. Commit and push:
   ```bash
   git add .
   git commit -m "Add: your feature description"
   git push origin feature/your-feature-name
   ```

5. Open a Pull Request

---

## 📋 TODO / Roadmap

### High Priority
- [ ] Markdown rendering with syntax highlighting
- [ ] Image optimization with django-imagekit
- [ ] Full-text search with PostgreSQL SearchVector
- [ ] Caching with Redis
- [ ] Email notifications for category approval/rejection

### Medium Priority
- [ ] AJAX tag autocomplete
- [ ] Live Markdown preview in chapter editor
- [ ] User follow system
- [ ] Reading progress tracking
- [ ] Book bookmarks/favorites
- [ ] Category moderation dashboard

### Low Priority
- [ ] REST API with Django REST Framework
- [ ] Social authentication (Google, GitHub)
- [ ] Two-factor authentication
- [ ] Export books as PDF/EPUB
- [ ] Collaborative editing
- [ ] Analytics dashboard

---

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Style

- Follow [PEP 8](https://pep8.org/) guidelines
- Use [Black](https://github.com/psf/black) for code formatting
- Add docstrings to all classes and methods
- Write tests for new features

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Django](https://www.djangoproject.com/) — The web framework for perfectionists with deadlines
- [Bootstrap](https://getbootstrap.com/) — Frontend component library
- [Python-Markdown](https://python-markdown.github.io/) — Markdown to HTML conversion

---

## 📧 Contact

- **Author:** Ivan Levitsky
- **Email:** ivanlevitsky.fourmetrsquared@gmail.com
- **GitHub:** [github.com/fourmetrsquared](https://github.com/fourmetrsquared)

---

<p align="center">Made with ❤️ and Django</p>

Since the project is being thrown together on a whim in spare time, an AI is writing the comments.)))
