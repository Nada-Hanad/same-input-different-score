#!/usr/bin/env python3
"""Public inventory screening. Human binary/identity review remains necessary."""
import argparse,io,json,re,shutil,subprocess,zipfile
from pathlib import Path
from verify_publication import ROOT,files
PATTERNS={
 'home_directory':re.compile(r'/(?:Users|home)/[A-Za-z0-9_.-]+/'),
 'personal_pages_url':re.compile(r'https?://[A-Za-z0-9_.-]+\.github\.io/(?!REPOSITORY/)'),
 'private_key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
 'github_token':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{35,})\b'),
 'aws_key':re.compile(r'\bAKIA[A-Z0-9]{16}\b'),
 'analytics':re.compile(r'(?:google-analytics\.com|googletagmanager\.com|plausible\.io/js|hotjar\.com/c/)'),
}
TEXT={'.md','.txt','.json','.csv','.ts','.tsx','.js','.mjs','.py','.html','.css','.yml','.yaml','.sha256'}
def scan(root=ROOT):
 findings=[];pdfs=[];archives=[];text_count=0
 def inspect(name,data,suffix):
  nonlocal text_count
  if suffix=='.pdf':
   pdfs.append(name)
   if shutil.which('pdftotext'):
    result=subprocess.run(['pdftotext','-','-'],input=data,capture_output=True,check=True);text=result.stdout.decode('utf-8','replace')
    if shutil.which('pdfinfo'):
     metadata=subprocess.run(['pdfinfo','-'],input=data,capture_output=True,check=True).stdout.decode('utf-8','replace');text+='\n'+metadata
   else:return
  elif suffix in TEXT or name.endswith(('Makefile','.gitignore','.nvmrc')):text=data.decode('utf-8','replace');text_count+=1
  else:return
  # Upstream attribution is retained. Exact project identities are screened privately.
  for rule,pattern in PATTERNS.items():
   if pattern.search(text):findings.append({'file':name,'rule':rule})
 for p in files(root):
  name=str(p.relative_to(root));inspect(name,p.read_bytes(),p.suffix)
  if p.suffix=='.zip':
   with zipfile.ZipFile(p) as z:
    archives.append({'file':name,'members':len(z.infolist())})
    for member in z.infolist():
     assert not Path(member.filename).is_absolute() and '..' not in Path(member.filename).parts
     assert not any(x in Path(member.filename).parts for x in ['.git','node_modules','raw_data'])
     inspect(name+'::'+member.filename,z.read(member),Path(member.filename).suffix)
 return {'status':'passed' if not findings else 'review_required','text_files_or_members':text_count,'pdf_files_or_members':len(pdfs),'archives':archives,'findings':findings,'pdf_text_metadata_tool_available':bool(shutil.which('pdftotext')),'boundary':'Pattern screening plus separately recorded human/binary review; not a proof of anonymity.'}
if __name__=='__main__':
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path);a=ap.parse_args();result=scan();payload=json.dumps(result,indent=2)+'\n'
 if a.output:a.output.write_text(payload)
 print(payload,end='');raise SystemExit(bool(result['findings']))
