import sys
import string
import types

_except = 0
if sys.version_info >= (3, 0):
    from panda3d.core import *
    from direct.showbase import DConfig
    try:
        language = DConfig.GetString('language', 'english')
        checkLanguage = DConfig.GetBool('check-language', 0)
    except:
        _except = 1
else:
    from pandac.PandaModules import *
    try:
        language = getConfigExpress().GetString('language', 'english')
        checkLanguage = getConfigExpress().GetBool('check-language', 0)
    except:
        _except = 1

if _except == 1:
    try:
        language = simbase.config.GetString('language', 'english')
        checkLanguage = simbase.config.GetBool('check-language', 0)
    except:
        print("An exception occurred while grabbing language settings.")
        sys.exit(1)


def getLanguage():
    return language


print 'OTPLocalizer: Running in language: %s' % language
if language == 'english':
    _languageModule = 'otp.otpbase.OTPLocalizer' + string.capitalize(language)
else:
    checkLanguage = 1
    _languageModule = 'otp.otpbase.OTPLocalizer_' + language
print 'from ' + _languageModule + ' import *'
from otp.otpbase.OTPLocalizerEnglish import *
if checkLanguage:
    l = {}
    g = {}
    englishModule = __import__('otp.otpbase.OTPLocalizerEnglish', g, l)
    foreignModule = __import__(_languageModule, g, l)
    for key, val in englishModule.__dict__.items():
        if not foreignModule.__dict__.has_key(key):
            print 'WARNING: Foreign module: %s missing key: %s' % (_languageModule, key)
            locals()[key] = val
        elif isinstance(val, types.DictType):
            fval = foreignModule.__dict__.get(key)
            for dkey, dval in val.items():
                if not fval.has_key(dkey):
                    print 'WARNING: Foreign module: %s missing key: %s.%s' % (_languageModule, key, dkey)
                    fval[dkey] = dval

            for dkey in fval.keys():
                if not val.has_key(dkey):
                    print 'WARNING: Foreign module: %s extra key: %s.%s' % (_languageModule, key, dkey)

    for key in foreignModule.__dict__.keys():
        if not englishModule.__dict__.has_key(key):
            print 'WARNING: Foreign module: %s extra key: %s' % (_languageModule, key)
