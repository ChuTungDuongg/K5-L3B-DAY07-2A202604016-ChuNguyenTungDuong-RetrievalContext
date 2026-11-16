"""Native extraction and pixel provenance, without benchmark-specific selection."""
import hashlib
import json
import re
from pathlib import Path

from .budget import save

ROOT=Path(__file__).resolve().parents[1]
DATA=ROOT/'advanced/data'
SOURCE_URL='https://documents1.worldbank.org/curated/en/248201616598597113/pdf/World-Development-Report-2021-Data-for-Better-Lives.pdf'
PDF_HASH='606c8452c8b23c01d81919c3974972bebeb1e60348a56ea40cc3ae841e301616'
PDF=DATA/'source.pdf'


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def clean_text(text):
    text=text.replace('\r\n','\n').replace('\r','\n').replace('\xad','').replace('\ufffe','')
    return re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]','',text).strip()


def split_text(text,size=350,overlap=50):
    if size<1 or overlap<0 or overlap>=size: raise ValueError('Invalid chunk size/overlap')
    rows=[];start=0
    while start<len(text):
        end=min(start+size,len(text));rows.append({'start':start,'end':end,'text':text[start:end]})
        if end==len(text): break
        start=end-overlap
    return rows


def render_page(number,long_edge=1800):
    import pypdfium2 as pdfium
    if digest(PDF)!=PDF_HASH: raise ValueError('Source PDF checksum mismatch')
    out=DATA/'pages'/f'p{number:03}.jpg'
    manifest=DATA/'render-manifest.json'
    if out.exists():
        if manifest.exists():
            expected=json.loads(manifest.read_text(encoding='utf-8'))['pages'][str(number)]
            if digest(out)!=expected: raise ValueError('Rendered source image changed after freeze')
        return out
    out.parent.mkdir(parents=True,exist_ok=True)
    doc=pdfium.PdfDocument(PDF)
    if type(number) is not int or not 1<=number<=len(doc): raise ValueError('Invalid source page')
    page=doc[number-1]
    page.render(scale=long_edge/max(page.get_size())).to_pil().convert('RGB').save(out,quality=92)
    doc.close()
    return out


def finalize_images():
    import importlib.metadata
    files={str(p):digest(render_page(p)) for p in range(1,351)}
    save(DATA/'render-manifest.json',{'pdf_sha256':PDF_HASH,'long_edge':1800,'jpeg_quality':92,
                                    'versions':{name:importlib.metadata.version(name) for name in ('pypdfium2','Pillow')},
                                    'pages':files})


def extract():
    import pypdfium2 as pdfium
    if digest(PDF)!=PDF_HASH: raise ValueError('Source PDF checksum mismatch')
    doc=pdfium.PdfDocument(PDF);pages=[];chunks=[]
    for i in range(len(doc)):
        page=doc[i];number=i+1
        text=clean_text(page.get_textpage().get_text_range())
        labels=list(dict.fromkeys(re.findall(r'\b(?:Figure|Table|Map)\s+(?:[A-Z]\d?\.)?\d+(?:\.\d+)*',text)))
        images=[]
        for obj in page.get_objects():
            if isinstance(obj,pdfium.PdfImage):
                x0,y0,x1,y1=obj.get_bounds();w,h=page.get_size()
                if (x1-x0)*(y1-y0)/(w*h)>.015:
                    images.append([round(x0/w,5),round(1-y1/h,5),round(x1/w,5),round(1-y0/h,5)])
        record={'page':number,'printed_page':str(number-20) if number>20 else 'front matter',
                'width':page.get_width(),'height':page.get_height(),'text':text,
                'labels':labels,'image_regions':images,'needs_vision':number>20 and bool(labels or images),
                'text_status':'extracted' if text else 'empty_native_text',
                'image_path':f'advanced/data/pages/p{number:03}.jpg','image_bbox':[0,0,1,1]}
        pages.append(record)
        for part in split_text(text):
            chunks.append({'id':f"wdr2021:p{number:03}:text:{part['start']}",'source_id':'wdr2021',
                           'source':SOURCE_URL,'page':number,'text':part['text'],
                           'metadata':{'kind':'text','start':part['start'],'end':part['end'],
                                       'bbox':[0,0,1,1],'printed_page':record['printed_page']}})
    doc.close()
    save(DATA/'pages.json',pages);save(DATA/'native-chunks.json',chunks)
    manifest={'source_id':'wdr2021','title':'World Development Report 2021: Data for Better Lives',
              'source_url':SOURCE_URL,'pdf_sha256':PDF_HASH,'physical_pages':len(pages),
              'native_chunks':len(chunks),'vision_candidate_pages':[p['page'] for p in pages if p['needs_vision']],
              'empty_text_pages':[p['page'] for p in pages if not p['text']],
              'license':'CC BY 3.0 IGO; see original page 4 and third-party component conditions',
              'coverage':'All pages retained as native text and reproducible page images. Named visuals and substantial raster images receive additional descriptions. No benchmark file is read.',
              'limitations':['Native text reading order and chart glyphs can be imperfect; original pixels are retained.',
                             'Front matter captions are not treated as actual visuals. Small decorative images are not described separately.']}
    save(DATA/'manifest.json',manifest)
    print(f"Extracted {len(pages)} pages, {len(chunks)} native chunks, {len(manifest['vision_candidate_pages'])} visual candidate pages",flush=True)


if __name__=='__main__':
    extract()
    finalize_images()
