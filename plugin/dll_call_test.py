import rlcompleter, readline;readline.parse_and_bind('tab:complete')
import os, sys, platform, ctypes

def dll_call(plugin, cmd, login, password):
    dllpath = f"..\\dllplugin\\{plugin}.dll"
    if not os.path.exists(dllpath):
        return f'{dllpath} not found'
    if platform.architecture()[0] != '32bit':
        return f'You are use python not a 32bit: {platform.architecture()[0]}'
    dll = ctypes.CDLL(dllpath)
    request = f'''<?xml version="1.0" encoding="windows-1251" ?>\n
    <Request>\n
        <ParentWindow>007F09DA</ParentWindow>\n
        <Login>{login}</Login>\n
        <Password>{password}</Password>\n
    </Request>'''

    buf = ctypes.create_string_buffer(1024)
    dll.IssaPlugin.argtypes = [ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_long]
    dll.IssaPlugin.restype = None
    dll.IssaPlugin(ctypes.c_char_p(cmd.encode('cp1251')),ctypes.c_char_p(request.encode('cp1251')),buf,len(buf))

    return buf.value.decode('cp1251')

if __name__ == '__main__':

    if len(sys.argv) != 1 + 4:
        print(f'usage: {sys.argv[0]} plugin cmd(Info or Execute) login passw')
        sys.exit()
    plugin = sys.argv[1]
    cmd = sys.argv[2]
    login = sys.argv[3]
    password = sys.argv[4]

    print(dll_call(plugin, cmd, login, password))
