"""Reject manuscript content, internal reports and broken public evidence links."""
import io,json,re,zipfile
from pathlib import Path
from urllib.parse import unquote,urlsplit
from verify_publication import files
from sync_public import DOCS
FIGURE_PDFS={'fig_cascade.pdf','fig_remediation_plan_failures.pdf','fig_margin_companion.pdf'}

def verify_curated(root):
 root=Path(root)
 assert {p.name for p in (root/'docs').iterdir()}==set(DOCS)|{'figure-references.json'}
 assert not (root/'reproducibility_artifact/docs').exists()
 pdfs=[];archives=[]
 def inspect(name,data):
  parts=Path(name).parts
  assert 'paper' not in parts and 'qa' not in parts,'Removed public content: '+name
  if name.lower().endswith('.pdf') or data.startswith(b'%PDF'):
   assert Path(name).name in FIGURE_PDFS and 'figures' in parts,'Manuscript or unapproved PDF: '+name
   pdfs.append(name)
  if zipfile.is_zipfile(io.BytesIO(data)):
   archives.append(name)
   with zipfile.ZipFile(io.BytesIO(data)) as archive:
    for member in archive.infolist():
     path=Path(member.filename)
     assert not path.is_absolute() and '..' not in path.parts
     assert not {'.git','node_modules','raw_data','outputs'}&set(path.parts)
     if 'docs' in path.parts:assert path.name in set(DOCS)|{'figure-references.json'},'Uncurated archive document: '+name+'::'+member.filename
     inspect(name+'::'+member.filename,archive.read(member))
 for path in files(root):
  relative=str(path.relative_to(root));inspect(relative,path.read_bytes())
 for folder in ['research_companion/public/docs','site/docs']:
  assert {p.name for p in (root/folder).iterdir()}==set(DOCS),folder
 for name in ['BASELINE_MANIFEST.json','LICENSE_DECISION_REQUIRED.md','reproducibility_artifact/data/checks.json','reproducibility_artifact/data/implementation-files.json']:
  assert not (root/name).exists(),'Removed internal record: '+name
 research=json.loads((root/'reproducibility_artifact/data/research.json').read_text())
 assert not {'manuscript','paper_available','discrepancies'}&set(research)
 assert all('manuscript_sha256' not in entry for entry in research['manifest'])
 return {'status':'passed','approved_figure_PDFs':len(pdfs),'archives_checked':len(archives),'manuscripts':0}

def verify_links(root):
 root=Path(root).resolve();count=0
 def check(path,target):
  nonlocal count
  target=unquote(target.strip('<>'));url=urlsplit(target)
  if url.scheme or url.netloc or not url.path:return
  destination=(path.parent/url.path).resolve()
  assert destination.is_relative_to(root) and destination.exists(),'Broken public link: '+str(path.relative_to(root))+' -> '+target
  count+=1
 for path in files(root):
  if path.suffix=='.md':
   for target in re.findall(r'!?\[[^\]]*\]\(([^\s)]+)(?:\s+"[^"]*")?\)',path.read_text()):check(path,target)
 public=root/'research_companion/public'
 for path in (root/'research_companion/src').rglob('*.tsx'):
  if path.name.endswith('.test.tsx'):continue
  for target in re.findall(r'resource\("([^"\n]+)"\)',path.read_text()):
   if urlsplit(target).scheme:continue
   base=root if target.lstrip('/').startswith('downloads/') else public
   assert (base/target.lstrip('/')).is_file(),'Missing UI resource: '+target
   count+=1
 research=json.loads((root/'reproducibility_artifact/data/research.json').read_text())
 for entry in research['manifest']:
  for key in ['included_dataset_url','script_download_url','figure_download_url']:
   if entry.get(key):assert (public/entry[key].lstrip('/')).is_file(),(entry['id'],key);count+=1
 return {'status':'passed','local_links_checked':count}
