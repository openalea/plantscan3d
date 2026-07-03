from PyQt5 import uic
import os
import sys

def get_uifnames_from(fname):
    uiprefix = os.path.splitext(fname)[0]
    pyfname  = uiprefix + '_ui.py'
    return pyfname
    
def get_rcfnames_from(fname):
    rcprefix = os.path.splitext(fname)[0]
    pyfname  = rcprefix + '_rc.py'
    return pyfname

def compile_ui(uifname):
    """ compile a Ui """
    pyfname = get_uifnames_from(uifname)
    fstream = open(pyfname,'w')
    uic.compileUi(uifname,fstream,from_imports=True)
    fstream.close()

def compile_rc(rcfname):
    """ compile a Resource file """
    pyfname = get_rcfnames_from(rcfname)
    if sys.platform == 'posix':
        exe = 'pyrcc5'
    else:
        exe = os.path.join(sys.prefix,'pyrcc5.bat')
        if not os.path.exists(exe):
            exe = 'pyrcc5'
    cmd = '%s "%s" > "%s"' % (exe,rcfname, pyfname)
    os.system(cmd)

def check_ui_generation(uifname):
    """ check if a py file should regenerated from a ui """
    pyfname = get_uifnames_from(uifname)
    if ( os.path.exists(uifname) and
         ( not os.path.exists(pyfname) or
           (os.access(pyfname,os.F_OK|os.W_OK) and
            os.stat(pyfname).st_mtime < os.stat(uifname).st_mtime ))) :
         print('Generate Ui')
         compile_ui(uifname)

def check_rc_generation(rcfname):
    """ check if a py file should regenerated from a Resource file """
    pyfname = get_rcfnames_from(rcfname)
    if ( os.path.exists(rcfname) and
         ( not os.path.exists(pyfname) or
           (os.access(pyfname,os.F_OK|os.W_OK) and
            os.stat(pyfname).st_mtime < os.stat(rcfname).st_mtime ))) :
        print('Generate Rc')
        compile_rc(rcfname)

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python ui_compiler.py [filename.{ui,rc}]")
        exit(-1)
    i = 1
    while i < len(sys.argv):
        if str(sys.argv[i]).rfind(".ui") >= 0:
            check_ui_generation(sys.argv[i])
        elif str(sys.argv[i]).rfind(".rc") >= 0 or str(sys.argv[i]).rfind(".qrc") >= 0:
            check_rc_generation(sys.argv[i])
        else:
            print(sys.argv[i] + ": not supported")
        i += 1
