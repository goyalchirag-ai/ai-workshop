"""Copy only browser assets to Vercel's CDN directory."""
from pathlib import Path
from shutil import copyfile

ROOT = Path(__file__).resolve().parent

def build():
    public = ROOT / "public"
    public.mkdir(exist_ok=True)
    for name in ("app.js", "styles.css"):
        copyfile(ROOT / "frontend" / name, public / name)

if __name__ == "__main__":
    build()
    print("Gather browser assets prepared in public/.")
