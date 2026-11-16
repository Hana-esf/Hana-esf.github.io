# hana-esf.github.io

Personal website of Hana Esfandiar, hosted on GitHub Pages.

## Files

- `index.html` holds the whole site: every page, the styles and the scripts.
- `assets/hero-light.webp` and `assets/hero-dark.webp` are the homepage photo in its light and dark versions.
- `assets/drug-confusion.webp` is the figure on the drug review project page.
- `assets/cv.pdf` is the CV that the CV page links to.

## Blog posts

The Blog pages show the full text of each post. `scripts/import_posts.py` runs every time the site is published, fetches each post from Substack and saves it to `posts/<slug>.html`. If a post cannot be fetched, its page shows a link to Substack instead.

To add a post, add its slug to `SLUGS` in `scripts/import_posts.py` and add an entry to `POSTS` in `index.html`.

## Editing content

Open `index.html` and search for the text you want to change.

- Posts and projects are listed near the bottom of the file, in the `POSTS` and `PROJECTS` lists. Copy an entry to add a new one.
- The journey timeline is plain HTML under the `JOURNEY` comment.
- To update the CV, replace `assets/cv.pdf` with a new file of the same name.

## Publishing

Commit the files to the `main` branch. GitHub Pages rebuilds the site within a minute or two.
