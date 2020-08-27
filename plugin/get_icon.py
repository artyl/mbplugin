import zlib,requests,io,sys
from PIL import Image
bb=io.BytesIO(requests.get(sys.argv[1]).content)
img = Image.open(bb)
img = img.resize((16,16))
bb=io.BytesIO()
img.save(bb, 'bmp')
bb.getvalue()
print(zlib.compress(bb.getvalue()).hex())
