"""Synchronize the curated canonical documentation; never create internal reports."""
import shutil
from pathlib import Path
DOCS=('REPRODUCIBILITY.md','METHODS_AND_LIMITATIONS.md','EVIDENCE_MAP.md','FIGURES.md')
def refresh_public_docs(root,data=None):
 root=Path(root);out=root/'research_companion/public/docs'
 if out.exists():shutil.rmtree(out)
 out.mkdir(parents=True)
 for name in DOCS:shutil.copyfile(root/'docs'/name,out/name)
