import sys;sys.dont_write_bytecode = True
import os
print('Remove __pycache__')
path = os.path.abspath(os.path.join(os.path.split(sys.argv[0])[0], '..', '..', 'mbplugin', 'python'))
print(path)
for root, dirs, files in os.walk(path, topdown=False):
    for name in files:
      if os.path.split(root)[-1] == '__pycache__':
        #print(os.path.join(root, name))
        os.remove(os.path.join(root, name))
    for name in dirs:
      if name == '__pycache__':
        #print(os.path.join(root, name))
        os.rmdir(os.path.join(root, name))

