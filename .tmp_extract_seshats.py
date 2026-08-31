import zipfile
from pathlib import Path
zip_path = Path(r"C:\Users\doliv\Documents\MORE Help Canter Files\wai_institute\Supervisor files\Seshats Hub.zip")
assert zip_path.exists(), zip_path
out = Path('.tmp_seshats')
if out.exists():
    import shutil
    shutil.rmtree(out)
with zipfile.ZipFile(zip_path, 'r') as z:
    z.extractall(out)
    for info in z.infolist()[:30]:
        print(info.filename, info.file_size)
