from direct.showbase import PythonUtil
import string
import random
import bisect
import types
import math

class DelayedCall:
    """ calls a func after a specified delay """
    def __init__(self, func, name=None, delay=None):
        if name is None:
            name = 'anonymous'
        if delay is None:
            delay = .01
        self._func = func
        self._taskName = 'DelayedCallback-%s' % name
        self._delay = delay
        self._finished = False
        self._addDoLater()
    def destroy(self):
        self._finished = True
        self._removeDoLater()
    def finish(self):
        if not self._finished:
            self._doCallback()
        self.destroy()
    def _addDoLater(self):
        taskMgr.doMethodLater(self._delay, self._doCallback, self._taskName)
    def _removeDoLater(self):
        taskMgr.remove(self._taskName)
    def _doCallback(self, task):
        self._finished = True
        func = self._func
        del self._func
        func()

class FrameDelayedCall:
    """ calls a func after N frames """
    def __init__(self, name, callback, frames=None, cancelFunc=None):
        # checkFunc is optional; called every frame, if returns True, FrameDelay is cancelled
        # and callback is not called
        if frames is None:
            frames = 1
        self._name = name
        self._frames = frames
        self._callback = callback
        self._cancelFunc = cancelFunc
        self._taskName = uniqueName('%s-%s' % (self.__class__.__name__, self._name))
        self._finished = False
        self._startTask()
    def destroy(self):
        self._finished = True
        self._stopTask()
    def finish(self):
        if not self._finished:
            self._finished = True
            self._callback()
        self.destroy()
    def _startTask(self):
        taskMgr.add(self._frameTask, self._taskName)
        self._counter = 0
    def _stopTask(self):
        taskMgr.remove(self._taskName)
    def _frameTask(self, task):
        if self._cancelFunc and self._cancelFunc():
            self.destroy()
            return task.done
        self._counter += 1
        if self._counter >= self._frames:
            self.finish()
            return task.done
        return task.cont

class DelayedFunctor:
    """ Waits for this object to be called, then calls supplied functor after a delay.
    Effectively inserts a time delay between the caller and the functor. """
    def __init__(self, functor, name=None, delay=None):
        self._functor = functor
        self._name = name
        # FunctionInterval requires __name__
        self.__name__ = self._name
        self._delay = delay
    def _callFunctor(self):
        cb = Functor(self._functor, *self._args, **self._kwArgs)
        del self._functor
        del self._name
        del self._delay
        del self._args
        del self._kwArgs
        del self._delayedCall
        del self.__name__
        cb()
    def __call__(self, *args, **kwArgs):
        self._args = args
        self._kwArgs = kwArgs
        self._delayedCall = DelayedCall(self._callFunctor, self._name, self._delay)


def sameElements(a, b):
    if len(a) != len(b):
        return 0
    for elem in a:
        if elem not in b:
            return 0
    for elem in b:
        if elem not in a:
            return 0
    return 1

def makeList(x):
    """returns x, converted to a list"""
    if type(x) is types.ListType:
        return x
    elif type(x) is types.TupleType:
        return list(x)
    else:
        return [x,]

def makeTuple(x):
    """returns x, converted to a tuple"""
    if type(x) is types.ListType:
        return tuple(x)
    elif type(x) is types.TupleType:
        return x
    else:
        return (x,)

def average(*args):
    """ returns simple average of list of values """
    val = 0.
    for arg in args:
        val += arg
    return val / len(args)

class Averager:
    def __init__(self, name):
        self._name = name
        self.reset()
    def reset(self):
        self._total = 0.
        self._count = 0
    def addValue(self, value):
        self._total += value
        self._count += 1
    def getAverage(self):
        return self._total / self._count
    def getCount(self):
        return self._count

def addListsByValue(a, b):
    """
    returns a new array containing the sums of the two array arguments
    (c[0] = a[0 + b[0], etc.)
    """
    c = []
    for x, y in zip(a, b):
        c.append(x + y)
    return c

def boolEqual(a, b):
    """
    returns true if a and b are both true or both false.
    returns false otherwise
    (a.k.a. xnor -- eXclusive Not OR).
    """
    return (a and b) or not (a or b)

def exceptionLogged(append=True):
    """decorator that outputs the function name and all arguments
    if an exception passes back through the stack frame
    if append is true, string is appended to the __str__ output of
    the exception. if append is false, string is printed to the log
    directly. If the output will take up many lines, it's recommended
    to set append to False so that the exception stack is not hidden
    by the output of this decorator.
    """
    try:
        null = not __dev__
    except:
        null = not __debug__
    if null:
        # if we're not in __dev__, just return the function itself. This
        # results in zero runtime overhead, since decorators are evaluated
        # at module-load.
        def nullDecorator(f):
            return f
        return nullDecorator
    
    def _decoratorFunc(f, append=append):
        global exceptionLoggedNotify
        if exceptionLoggedNotify is None:
            from direct.directnotify.DirectNotifyGlobal import directNotify
            exceptionLoggedNotify = directNotify.newCategory("ExceptionLogged")
        def _exceptionLogged(*args, **kArgs):
            try:
                return f(*args, **kArgs)
            except Exception, e:
                try:
                    s = '%s(' % f.func_name
                    for arg in args:
                        s += '%s, ' % arg
                    for key, value in kArgs.items():
                        s += '%s=%s, ' % (key, value)
                    if len(args) or len(kArgs):
                        s = s[:-2]
                    s += ')'
                    if append:
                        appendStr(e, '\n%s' % s)
                    else:
                        exceptionLoggedNotify.info(s)
                except:
                    exceptionLoggedNotify.info(
                        '%s: ERROR IN PRINTING' % f.func_name)
                raise
        _exceptionLogged.__doc__ = f.__doc__
        return _exceptionLogged
    return _decoratorFunc

# class 'decorator' that records the stack at the time of creation
# be careful with this, it creates a StackTrace, and that can take a
# lot of CPU
def recordCreationStack(cls):
    if not hasattr(cls, '__init__'):
        raise 'recordCreationStack: class \'%s\' must define __init__' % cls.__name__
    cls.__moved_init__ = cls.__init__
    def __recordCreationStack_init__(self, *args, **kArgs):
        self._creationStackTrace = StackTrace(start=1)
        return self.__moved_init__(*args, **kArgs)
    def getCreationStackTrace(self):
        return self._creationStackTrace
    def getCreationStackTraceCompactStr(self):
        return self._creationStackTrace.compact()
    def printCreationStackTrace(self):
        print self._creationStackTrace
    cls.__init__ = __recordCreationStack_init__
    cls.getCreationStackTrace = getCreationStackTrace
    cls.getCreationStackTraceCompactStr = getCreationStackTraceCompactStr
    cls.printCreationStackTrace = printCreationStackTrace
    return cls

# like recordCreationStack but stores the stack as a compact stack list-of-strings
# scales well for memory usage
def recordCreationStackStr(cls):
    if not hasattr(cls, '__init__'):
        raise 'recordCreationStackStr: class \'%s\' must define __init__' % cls.__name__
    cls.__moved_init__ = cls.__init__
    def __recordCreationStackStr_init__(self, *args, **kArgs):
        # store as list of strings to conserve memory
        self._creationStackTraceStrLst = StackTrace(start=1).compact().split(',')
        return self.__moved_init__(*args, **kArgs)
    def getCreationStackTraceCompactStr(self):
        return string.join(self._creationStackTraceStrLst, ',')
    def printCreationStackTrace(self):
        print string.join(self._creationStackTraceStrLst, ',')
    cls.__init__ = __recordCreationStackStr_init__
    cls.getCreationStackTraceCompactStr = getCreationStackTraceCompactStr
    cls.printCreationStackTrace = printCreationStackTrace
    return cls


# class 'decorator' that logs all method calls for a particular class
def logMethodCalls(cls):
    if not hasattr(cls, 'notify'):
        raise 'logMethodCalls: class \'%s\' must have a notify' % cls.__name__
    for name in dir(cls):
        method = getattr(cls, name)
        if hasattr(method, '__call__'):
            def getLoggedMethodCall(method):
                def __logMethodCall__(obj, *args, **kArgs):
                    s = '%s(' % method.__name__
                    for arg in args:
                        try:
                            argStr = repr(arg)
                        except:
                            argStr = 'bad repr: %s' % arg.__class__
                        s += '%s, ' % argStr
                    for karg, value in kArgs.items():
                        s += '%s=%s, ' % (karg, repr(value))
                    if len(args) or len(kArgs):
                        s = s[:-2]
                    s += ')'
                    obj.notify.info(s)
                    return method(obj, *args, **kArgs)
                return __logMethodCall__
            setattr(cls, name, getLoggedMethodCall(method))
    __logMethodCall__ = None
    return cls

class Functor:
    def __init__(self, function, *args, **kargs):
        assert callable(function), "function should be a callable obj"
        self._function = function
        self._args = args
        self._kargs = kargs
        if hasattr(self._function, '__name__'):
            self.__name__ = self._function.__name__
        else:
            self.__name__ = str(itype(self._function))
        if hasattr(self._function, '__doc__'):
            self.__doc__ = self._function.__doc__
        else:
            self.__doc__ = self.__name__

    def destroy(self):
        del self._function
        del self._args
        del self._kargs
        del self.__name__
        del self.__doc__
    
    def _do__call__(self, *args, **kargs):
        _kargs = self._kargs.copy()
        _kargs.update(kargs)
        return self._function(*(self._args + args), **_kargs)

    # this method is used in place of __call__ if we are recording creation stacks
    def _exceptionLoggedCreationStack__call__(self, *args, **kargs):
        try:
            return self._do__call__(*args, **kargs)
        except Exception, e:
            print '-->Functor creation stack (%s): %s' % (
                self.__name__, self.getCreationStackTraceCompactStr())
            raise

    __call__ = _do__call__

    def __repr__(self):
        s = 'Functor(%s' % self._function.__name__
        for arg in self._args:
            try:
                argStr = repr(arg)
            except:
                argStr = 'bad repr: %s' % arg.__class__
            s += ', %s' % argStr
        for karg, value in self._kargs.items():
            s += ', %s=%s' % (karg, repr(value))
        s += ')'
        return s

class Stack:
    def __init__(self):
        self.__list = []
    def push(self, item):
        self.__list.append(item)
    def top(self):
        # return the item on the top of the stack without popping it off
        return self.__list[-1]
    def pop(self):
        return self.__list.pop()
    def clear(self):
        self.__list = []
    def isEmpty(self):
        return len(self.__list) == 0
    def __len__(self):
        return len(self.__list)

class Queue:
    # FIFO queue
    # interface is intentionally identical to Stack (LIFO)
    def __init__(self):
        self.__list = []
    def push(self, item):
        self.__list.append(item)
    def top(self):
        # return the next item at the front of the queue without popping it off
        return self.__list[0]
    def front(self):
        return self.__list[0]
    def back(self):
        return self.__list[-1]
    def pop(self):
        return self.__list.pop(0)
    def clear(self):
        self.__list = []
    def isEmpty(self):
        return len(self.__list) == 0
    def __len__(self):
        return len(self.__list)

if __debug__:
    q = Queue()
    assert q.isEmpty()
    q.clear()
    assert q.isEmpty()
    q.push(10)
    assert not q.isEmpty()
    q.push(20)
    assert not q.isEmpty()
    assert len(q) == 2
    assert q.front() == 10
    assert q.back() == 20
    assert q.top() == 10
    assert q.top() == 10
    assert q.pop() == 10
    assert len(q) == 1
    assert not q.isEmpty()
    assert q.pop() == 20
    assert len(q) == 0
    assert q.isEmpty()

def unique(L1, L2):
    """Return a list containing all items in 'L1' that are not in 'L2'"""
    L2 = dict([(k, None) for k in L2])
    return [item for item in L1 if item not in L2]

def indent(stream, numIndents, str):
    """
    Write str to stream with numIndents in front of it
    """
    # To match emacs, instead of a tab character we will use 4 spaces
    stream.write('    ' * numIndents + str)


def nonRepeatingRandomList(vals, max):
    random.seed(time.time())
    #first generate a set of random values
    valueList=range(max)
    finalVals=[]
    for i in range(vals):
        index=int(random.random()*len(valueList))
        finalVals.append(valueList[index])
        valueList.remove(valueList[index])
    return finalVals



def writeFsmTree(instance, indent = 0):
    if hasattr(instance, 'parentFSM'):
        writeFsmTree(instance.parentFSM, indent-2)
    elif hasattr(instance, 'fsm'):
        name = ''
        if hasattr(instance.fsm, 'state'):
            name = instance.fsm.state.name
        print "%s: %s"%(instance.fsm.name, name)




#if __debug__: #RAU accdg to Darren its's ok that StackTrace is not protected by __debug__
# DCR: if somebody ends up using StackTrace in production, either
# A) it will be OK because it hardly ever gets called, or
# B) it will be easy to track it down (grep for StackTrace)
class StackTrace:
    def __init__(self, label="", start=0, limit=None):
        """
        label is a string (or anything that be be a string)
        that is printed as part of the trace back.
        This is just to make it easier to tell what the
        stack trace is referring to.
        start is an integer number of stack frames back
        from the most recent.  (This is automatically
        bumped up by one to skip the __init__ call
        to the StackTrace).
        limit is an integer number of stack frames
        to record (or None for unlimited).
        """
        self.label = label
        if limit is not None:
            self.trace = traceback.extract_stack(sys._getframe(1+start),
                                                 limit=limit)
        else:
            self.trace = traceback.extract_stack(sys._getframe(1+start))
            
    def compact(self):
        r = ''
        comma = ','
        for filename, lineNum, funcName, text in self.trace:
            r += '%s.%s:%s%s' % (filename[:filename.rfind('.py')][filename.rfind('\\')+1:], funcName, lineNum, comma)
        if len(r):
            r = r[:-len(comma)]
        return r

    def reverseCompact(self):
        r = ''
        comma = ','
        for filename, lineNum, funcName, text in self.trace:
            r = '%s.%s:%s%s%s' % (filename[:filename.rfind('.py')][filename.rfind('\\')+1:], funcName, lineNum, comma, r)
        if len(r):
            r = r[:-len(comma)]
        return r

    def __str__(self):
        r = "Debug stack trace of %s (back %s frames):\n"%(
            self.label, len(self.trace),)
        for i in traceback.format_list(self.trace):
            r+=i
        r+="***** NOTE: This is not a crash. This is a debug stack trace. *****"
        return r

def printStack():
    print StackTrace(start=1).compact()
    return True
def printReverseStack():
    print StackTrace(start=1).reverseCompact()
    return True
def printVerboseStack():
    print StackTrace(start=1)
    return True

#-----------------------------------------------------------------------------

def traceFunctionCall(frame):
    """
    return a string that shows the call frame with calling arguments.
    e.g.
    foo(x=234, y=135)
    """
    f = frame
    co = f.f_code
    dict = f.f_locals
    n = co.co_argcount
    if co.co_flags & 4: n = n+1
    if co.co_flags & 8: n = n+1
    r=''
    if 'self' in dict:
        r = '%s.'%(dict['self'].__class__.__name__,)
    r+="%s("%(f.f_code.co_name,)
    comma=0 # formatting, whether we should type a comma.
    for i in range(n):
        name = co.co_varnames[i]
        if name=='self':
            continue
        if comma:
            r+=', '
        else:
            # ok, we skipped the first one, the rest get commas:
            comma=1
        r+=name
        r+='='
        if name in dict:
            v=safeRepr(dict[name])
            if len(v)>2000:
                # r+="<too big for debug>"
                r += (v[:2000] + "...")
            else:
                r+=v
        else: r+="*** undefined ***"
    return r+')'

def traceParentCall():
    return traceFunctionCall(sys._getframe(2))

def printThisCall():
    print traceFunctionCall(sys._getframe(1))
    return 1 # to allow "assert printThisCall()"


if __debug__:
    def lineage(obj, verbose=0, indent=0):
        """
        return instance or class name in as a multiline string.
        Usage: print lineage(foo)
        (Based on getClassLineage())
        """
        r=""
        if type(obj) == types.ListType:
            r+=(" "*indent)+"python list\n"
        elif type(obj) == types.DictionaryType:
            r+=(" "*indent)+"python dictionary\n"
        elif type(obj) == types.ModuleType:
            r+=(" "*indent)+str(obj)+"\n"
        elif type(obj) == types.InstanceType:
            r+=lineage(obj.__class__, verbose, indent)
        elif type(obj) == types.ClassType:
            r+=(" "*indent)
            if verbose:
                r+=obj.__module__+"."
            r+=obj.__name__+"\n"
            for c in obj.__bases__:
                r+=lineage(c, verbose, indent+2)
        return r

def tron():
    sys.settrace(trace)
def trace(frame, event, arg):
    if event == 'line':
        pass
    elif event == 'call':
        print traceFunctionCall(sys._getframe(1))
    elif event == 'return':
        print "returning"
    elif event == 'exception':
        print "exception"
    return trace
def troff():
    sys.settrace(None)

#-----------------------------------------------------------------------------

def formatElapsedSeconds(seconds):
    """
    Returns a string of the form "mm:ss" or "hh:mm:ss" or "n days",
    representing the indicated elapsed time in seconds.
    """
    sign = ''
    if seconds < 0:
        seconds = -seconds
        sign = '-'

    # We use math.floor() instead of casting to an int, so we avoid
    # problems with numbers that are too large to represent as
    # type int.
    seconds = math.floor(seconds)
    hours = math.floor(seconds / (60 * 60))
    if hours > 36:
        days = math.floor((hours + 12) / 24)
        return "%s%d days" % (sign, days)

    seconds -= hours * (60 * 60)
    minutes = (int)(seconds / 60)
    seconds -= minutes * 60
    if hours != 0:
        return "%s%d:%02d:%02d" % (sign, hours, minutes, seconds)
    else:
        return "%s%d:%02d" % (sign, minutes, seconds)

def solveQuadratic(a, b, c):
    # quadratic equation: ax^2 + bx + c = 0
    # quadratic formula:  x = [-b +/- sqrt(b^2 - 4ac)] / 2a
    # returns None, root, or [root1, root2]

    # a cannot be zero.
    if a == 0.:
        return None

    # calculate the determinant (b^2 - 4ac)
    D = (b * b) - (4. * a * c)

    if D < 0:
        # there are no solutions (sqrt(negative number) is undefined)
        return None
    elif D == 0:
        # only one root
        return (-b) / (2. * a)
    else:
        # OK, there are two roots
        sqrtD = math.sqrt(D)
        twoA = 2. * a
        root1 = ((-b) - sqrtD) / twoA
        root2 = ((-b) + sqrtD) / twoA
        return [root1, root2]

def stackEntryInfo(depth=0, baseFileName=1):
    """
    returns the sourcefilename, line number, and function name of
    an entry in the stack.
    'depth' is how far back to go in the stack; 0 is the caller of this
    function, 1 is the function that called the caller of this function, etc.
    by default, strips off the path of the filename; override with baseFileName
    returns (fileName, lineNum, funcName) --> (string, int, string)
    returns (None, None, None) on error
    """
    try:
        stack = None
        frame = None
        try:
            stack = inspect.stack()
            # add one to skip the frame associated with this function
            frame = stack[depth+1]
            filename = frame[1]
            if baseFileName:
                filename = os.path.basename(filename)
            lineNum = frame[2]
            funcName = frame[3]
            result = (filename, lineNum, funcName)
        finally:
            del stack
            del frame
    except:
        result = (None, None, None)

    return result

def lineInfo(baseFileName=1):
    """
    returns the sourcefilename, line number, and function name of the
    code that called this function
    (answers the question: 'hey lineInfo, where am I in the codebase?')
    see stackEntryInfo, above, for info on 'baseFileName' and return types
    """
    return stackEntryInfo(1, baseFileName)

def callerInfo(baseFileName=1, howFarBack=0):
    """
    returns the sourcefilename, line number, and function name of the
    caller of the function that called this function
    (answers the question: 'hey callerInfo, who called me?')
    see stackEntryInfo, above, for info on 'baseFileName' and return types
    """
    return stackEntryInfo(2+howFarBack, baseFileName)

def lineTag(baseFileName=1, verbose=0, separator=':'):
    """
    returns a string containing the sourcefilename and line number
    of the code that called this function
    (equivalent to lineInfo, above, with different return type)
    see stackEntryInfo, above, for info on 'baseFileName'
    if 'verbose' is false, returns a compact string of the form
    'fileName:lineNum:funcName'
    if 'verbose' is true, returns a longer string that matches the
    format of Python stack trace dumps
    returns empty string on error
    """
    fileName, lineNum, funcName = callerInfo(baseFileName)
    if fileName is None:
        return ''
    if verbose:
        return 'File "%s", line %s, in %s' % (fileName, lineNum, funcName)
    else:
        return '%s%s%s%s%s' % (fileName, separator, lineNum, separator,
                               funcName)

def describeException(backTrace = 4):
    # When called in an exception handler, returns a string describing
    # the current exception.

    def byteOffsetToLineno(code, byte):
        # Returns the source line number corresponding to the given byte
        # offset into the indicated Python code module.

        import array
        lnotab = array.array('B', code.co_lnotab)

        line   = code.co_firstlineno
        for i in range(0, len(lnotab), 2):
            byte -= lnotab[i]
            if byte <= 0:
                return line
            line += lnotab[i+1]

        return line

    infoArr = sys.exc_info()
    exception = infoArr[0]
    exceptionName = getattr(exception, '__name__', None)
    extraInfo = infoArr[1]
    trace = infoArr[2]

    stack = []
    while trace.tb_next:
        # We need to call byteOffsetToLineno to determine the true
        # line number at which the exception occurred, even though we
        # have both trace.tb_lineno and frame.f_lineno, which return
        # the correct line number only in non-optimized mode.
        frame = trace.tb_frame
        module = frame.f_globals.get('__name__', None)
        lineno = byteOffsetToLineno(frame.f_code, frame.f_lasti)
        stack.append("%s:%s, " % (module, lineno))
        trace = trace.tb_next

    frame = trace.tb_frame
    module = frame.f_globals.get('__name__', None)
    lineno = byteOffsetToLineno(frame.f_code, frame.f_lasti)
    stack.append("%s:%s, " % (module, lineno))

    description = ""
    for i in range(len(stack) - 1, max(len(stack) - backTrace, 0) - 1, -1):
        description += stack[i]

    description += "%s: %s" % (exceptionName, extraInfo)
    return description

def mostDerivedLast(classList):
    """pass in list of classes. sorts list in-place, with derived classes
    appearing after their bases"""
    def compare(a, b):
        if issubclass(a, b):
            result=1
        elif issubclass(b, a):
            result=-1
        else:
            result=0
        #print a, b, result
        return result
    classList.sort(compare)

def clampScalar(value, a, b):
    # calling this ought to be faster than calling both min and max
    if a < b:
        if value < a:
            return a
        elif value > b:
            return b
        else:
            return value
    else:
        if value < b:
            return b
        elif value > a:
            return a
        else:
            return value

def pivotScalar(scalar, pivot):
    # reflect scalar about pivot; see tests below
    return pivot + (pivot - scalar)

if __debug__:
    assert pivotScalar(1, 0) == -1
    assert pivotScalar(-1, 0) == 1
    assert pivotScalar(3, 5) == 7
    assert pivotScalar(10, 1) == -8

def weightedChoice(choiceList, rng=random.random, sum=None):
    """given a list of (weight, item) pairs, chooses an item based on the
    weights. rng must return 0..1. if you happen to have the sum of the
    weights, pass it in 'sum'."""
    # TODO: add support for dicts
    if sum is None:
        sum = 0.
        for weight, item in choiceList:
            sum += weight

    rand = rng()
    accum = rand * sum
    for weight, item in choiceList:
        accum -= weight
        if accum <= 0.:
            return item
    # rand is ~1., and floating-point error prevented accum from hitting 0.
    # Or you passed in a 'sum' that was was too large.
    # Return the last item.
    return item

def normalDistrib(a, b, gauss=random.gauss):
    """
    NOTE: assumes a < b
    Returns random number between a and b, using gaussian distribution, with
    mean=avg(a, b), and a standard deviation that fits ~99.7% of the curve
    between a and b.
    For ease of use, outlying results are re-computed until result is in [a, b]
    This should fit the remaining .3% of the curve that lies outside [a, b]
    uniformly onto the curve inside [a, b]
    ------------------------------------------------------------------------
    http://www-stat.stanford.edu/~naras/jsm/NormalDensity/NormalDensity.html
    The 68-95-99.7% Rule
    ====================
    All normal density curves satisfy the following property which is often
      referred to as the Empirical Rule:
    68% of the observations fall within 1 standard deviation of the mean.
    95% of the observations fall within 2 standard deviations of the mean.
    99.7% of the observations fall within 3 standard deviations of the mean.
    Thus, for a normal distribution, almost all values lie within 3 standard
      deviations of the mean.
    ------------------------------------------------------------------------
    In calculating our standard deviation, we divide (b-a) by 6, since the
    99.7% figure includes 3 standard deviations _on_either_side_ of the mean.
    """
    while True:
        r = gauss((a+b)*.5, (b-a)/6.)
        if (r >= a) and (r <= b):
            return r

def weightedRand(valDict, rng=random.random):
    """
    pass in a dictionary with a selection -> weight mapping.  Eg.
    {"Choice 1": 10,
     "Choice 2": 30,
     "bear":     100}
    -Weights need not add up to any particular value.
    -The actual selection will be returned.
    """
    selections = valDict.keys()
    weights = valDict.values()

    totalWeight = 0
    for weight in weights:
        totalWeight += weight

    # get a random value between 0 and the total of the weights
    randomWeight = rng() * totalWeight

    # find the index that corresponds with this weight
    for i in range(len(weights)):
        totalWeight -= weights[i]
        if totalWeight <= randomWeight:
            return selections[i]

    assert True, "Should never get here"
    return selections[-1]

def randUint31(rng=random.random):
    """returns a random integer in [0..2^31).
    rng must return float in [0..1]"""
    return int(rng() * 0x7FFFFFFF)

def randInt32(rng=random.random):
    """returns a random integer in [-2147483648..2147483647].
    rng must return float in [0..1]
    """
    i = int(rng() * 0x7FFFFFFF)
    if rng() < .5:
        i *= -1
    return i

def randUint32(rng=random.random):
    """returns a random integer in [0..2^32).
    rng must return float in [0..1]"""
    return long(rng() * 0xFFFFFFFF)

class SerialNumGen:
    """generates serial numbers"""
    def __init__(self, start=None):
        if start is None:
            start = 0
        self.__counter = start-1
    def next(self):
        self.__counter += 1
        return self.__counter

class SerialMaskedGen(SerialNumGen):
    def __init__(self, mask, start=None):
        self._mask = mask
        SerialNumGen.__init__(self, start)
    def next(self):
        v = SerialNumGen.next(self)
        return v & self._mask

_serialGen = SerialNumGen()
def serialNum():
    global _serialGen
    return _serialGen.next()
def uniqueName(name):
    global _serialGen
    return '%s-%s' % (name, _serialGen.next())

class EnumIter:
    def __init__(self, enum):
        self._values = enum._stringTable.keys()
        self._index = 0
    def __iter__(self):
        return self
    def next(self):
        if self._index >= len(self._values):
            raise StopIteration
        self._index += 1
        return self._values[self._index-1]

class Enum:
    """Pass in list of strings or string of comma-separated strings.
    Items are accessible as instance.item, and are assigned unique,
    increasing integer values. Pass in integer for 'start' to override
    starting value.
    Example:
    >>> colors = Enum('red, green, blue')
    >>> colors.red
    0
    >>> colors.green
    1
    >>> colors.blue
    2
    >>> colors.getString(colors.red)
    'red'
    """

    if __debug__:
        # chars that cannot appear within an item string.
        InvalidChars = string.whitespace
        def _checkValidIdentifier(item):
            invalidChars = string.whitespace+string.punctuation
            invalidChars = invalidChars.replace('_','')
            invalidFirstChars = invalidChars+string.digits
            if item[0] in invalidFirstChars:
                raise SyntaxError, ("Enum '%s' contains invalid first char" %
                                    item)
            if not disjoint(item, invalidChars):
                for char in item:
                    if char in invalidChars:
                        raise SyntaxError, (
                            "Enum\n'%s'\ncontains illegal char '%s'" %
                            (item, char))
            return 1
        _checkValidIdentifier = staticmethod(_checkValidIdentifier)

    def __init__(self, items, start=0):
        if type(items) == types.StringType:
            items = items.split(',')

        self._stringTable = {}

        # make sure we don't overwrite an existing element of the class
        assert self._checkExistingMembers(items)
        assert uniqueElements(items)

        i = start
        for item in items:
            # remove leading/trailing whitespace
            item = string.strip(item)
            # is there anything left?
            if len(item) == 0:
                continue
            # make sure there are no invalid characters
            assert Enum._checkValidIdentifier(item)
            self.__dict__[item] = i
            self._stringTable[i] = item
            i += 1

    def __iter__(self):
        return EnumIter(self)

    def hasString(self, string):
        return string in set(self._stringTable.values())

    def fromString(self, string):
        if self.hasString(string):
            return self.__dict__[string]
        # throw an error
        {}[string]

    def getString(self, value):
        return self._stringTable[value]

    def __contains__(self, value):
        return value in self._stringTable

    def __len__(self):
        return len(self._stringTable)

    def copyTo(self, obj):
        # copies all members onto obj
        for name, value in self._stringTable:
            setattr(obj, name, value)

    if __debug__:
        def _checkExistingMembers(self, items):
            for item in items:
                if hasattr(self, item):
                    return 0
            return 1

def list2dict(L, value=None):
    """creates dict using elements of list, all assigned to same value"""
    return dict([(k, value) for k in L])

def listToIndex2item(L):
    """converts list to dict of list index->list item"""
    d = {}
    for i, item in enumerate(L):
        d[i] = item
    return d

assert listToIndex2item(['a','b']) == {0: 'a', 1: 'b',}
    
def listToItem2index(L):
    """converts list to dict of list item->list index
    This is lossy if there are duplicate list items"""
    d = {}
    for i, item in enumerate(L):
        d[item] = i
    return d

assert listToItem2index(['a','b']) == {'a': 0, 'b': 1,}

def invertDict(D, lossy=False):
    """creates a dictionary by 'inverting' D; keys are placed in the new
    dictionary under their corresponding value in the old dictionary.
    It is an error if D contains any duplicate values.
    >>> old = {'key1':1, 'key2':2}
    >>> invertDict(old)
    {1: 'key1', 2: 'key2'}
    """
    n = {}
    for key, value in D.items():
        if not lossy and value in n:
            raise 'duplicate key in invertDict: %s' % value
        n[value] = key
    return n

def invertDictLossless(D):
    """similar to invertDict, but values of new dict are lists of keys from
    old dict. No information is lost.
    >>> old = {'key1':1, 'key2':2, 'keyA':2}
    >>> invertDictLossless(old)
    {1: ['key1'], 2: ['key2', 'keyA']}
    """
    n = {}
    for key, value in D.items():
        n.setdefault(value, [])
        n[value].append(key)
    return n

def uniqueElements(L):
    """are all elements of list unique?"""
    return len(L) == len(list2dict(L))

def notNone(A, B):
    # returns A if not None, B otherwise
    if A is None:
        return B
    return A

def disjoint(L1, L2):
    """returns non-zero if L1 and L2 have no common elements"""
    used = dict([(k, None) for k in L1])
    for k in L2:
        if k in used:
            return 0
    return 1

def contains(whole, sub):
    """
    Return 1 if whole contains sub, 0 otherwise
    """
    if (whole == sub):
        return 1
    for elem in sub:
        # The first item you find not in whole, return 0
        if elem not in whole:
            return 0
    # If you got here, whole must contain sub
    return 1

def replace(list, old, new, all=0):
    """
    replace 'old' with 'new' in 'list'
    if all == 0, replace first occurrence
    otherwise replace all occurrences
    returns the number of items replaced
    """
    if old not in list:
        return 0

    if not all:
        i = list.index(old)
        list[i] = new
        return 1
    else:
        numReplaced = 0
        for i in xrange(len(list)):
            if list[i] == old:
                numReplaced += 1
                list[i] = new
        return numReplaced

rad90 = math.pi / 2.
rad180 = math.pi
rad270 = 1.5 * math.pi
rad360 = 2. * math.pi

def reduceAngle(deg):
    """
    Reduces an angle (in degrees) to a value in [-180..180)
    """
    return (((deg + 180.) % 360.) - 180.)

def fitSrcAngle2Dest(src, dest):
    """
    given a src and destination angle, returns an equivalent src angle
    that is within [-180..180) of dest
    examples:
    fitSrcAngle2Dest(30, 60) == 30
    fitSrcAngle2Dest(60, 30) == 60
    fitSrcAngle2Dest(0, 180) == 0
    fitSrcAngle2Dest(-1, 180) == 359
    fitSrcAngle2Dest(-180, 180) == 180
    """
    return dest + reduceAngle(src - dest)

def fitDestAngle2Src(src, dest):
    """
    given a src and destination angle, returns an equivalent dest angle
    that is within [-180..180) of src
    examples:
    fitDestAngle2Src(30, 60) == 60
    fitDestAngle2Src(60, 30) == 30
    fitDestAngle2Src(0, 180) == -180
    fitDestAngle2Src(1, 180) == 180
    """
    return src + (reduceAngle(dest - src))

def closestDestAngle2(src, dest):
    # The function above didn't seem to do what I wanted. So I hacked
    # this one together. I can't really say I understand it. It's more
    # from impirical observation... GRW
    diff = src - dest
    if diff > 180:
        # if the difference is greater that 180 it's shorter to go the other way
        return dest - 360
    elif diff < -180:
        # or perhaps the OTHER other way...
        return dest + 360
    else:
        # otherwise just go to the original destination
        return dest

def closestDestAngle(src, dest):
    # The function above didn't seem to do what I wanted. So I hacked
    # this one together. I can't really say I understand it. It's more
    # from impirical observation... GRW
    diff = src - dest
    if diff > 180:
        # if the difference is greater that 180 it's shorter to go the other way
        return src - (diff - 360)
    elif diff < -180:
        # or perhaps the OTHER other way...
        return src - (360 + diff)
    else:
        # otherwise just go to the original destination
        return dest


def binaryRepr(number, max_length = 32):
    # This will only work reliably for relatively small numbers.
    # Increase the value of max_length if you think you're going
    # to use long integers
    assert number < 2L << max_length
    shifts = map (operator.rshift, max_length * [number], \
                  range (max_length - 1, -1, -1))
    digits = map (operator.mod, shifts, max_length * [2])
    if not digits.count (1): return 0
    digits = digits [digits.index (1):]
    return string.join (map (repr, digits), '')

class StdoutCapture:
    # redirects stdout to a string
    def __init__(self):
        self._oldStdout = sys.stdout
        sys.stdout = self
        self._string = ''
    def destroy(self):
        sys.stdout = self._oldStdout
        del self._oldStdout

    def getString(self):
        return self._string

    # internal
    def write(self, string):
        self._string = ''.join([self._string, string])

class StdoutPassthrough(StdoutCapture):
    # like StdoutCapture but also allows output to go through to the OS as normal

    # internal
    def write(self, string):
        self._string = ''.join([self._string, string])
        self._oldStdout.write(string)

class StdoutPassthrough(StdoutCapture):
    # like StdoutCapture but also allows output to go through to the OS as normal

    # internal
    def write(self, string):
        self._string = ''.join([self._string, string])
        self._oldStdout.write(string)

# constant profile defaults
PyUtilProfileDefaultFilename = 'profiledata'
PyUtilProfileDefaultLines = 80
PyUtilProfileDefaultSorts = ['cumulative', 'time', 'calls']

_ProfileResultStr = ''

def getProfileResultString():
    # if you called profile with 'log' not set to True,
    # you can call this function to get the results as
    # a string
    global _ProfileResultStr
    return _ProfileResultStr

def profileFunc(callback, name, terse, log=True):
    global _ProfileResultStr
    if 'globalProfileFunc' in __builtin__.__dict__:
        # rats. Python profiler is not re-entrant...
        base.notify.warning(
            'PythonUtil.profileStart(%s): aborted, already profiling %s'
            #'\nStack Trace:\n%s'
            % (name, __builtin__.globalProfileFunc,
            #StackTrace()
            ))
        return
    __builtin__.globalProfileFunc = callback
    __builtin__.globalProfileResult = [None]
    prefix = '***** START PROFILE: %s *****' % name
    if log:
        print prefix
    startProfile(cmd='globalProfileResult[0]=globalProfileFunc()', callInfo=(not terse), silent=not log)
    suffix = '***** END PROFILE: %s *****' % name
    if log:
        print suffix
    else:
        _ProfileResultStr = '%s\n%s\n%s' % (prefix, _ProfileResultStr, suffix)
    result = globalProfileResult[0]
    del __builtin__.__dict__['globalProfileFunc']
    del __builtin__.__dict__['globalProfileResult']
    return result

def profiled(category=None, terse=False):
    """ decorator for profiling functions
    turn categories on and off via "want-profile-categoryName 1"
    
    e.g.
    @profiled('particles')
    def loadParticles():
        ...
    want-profile-particles 1
    """
    assert type(category) in (types.StringType, types.NoneType), "must provide a category name for @profiled"

    # allow profiling in published versions
    """
    try:
        null = not __dev__
    except:
        null = not __debug__
    if null:
        # if we're not in __dev__, just return the function itself. This
        # results in zero runtime overhead, since decorators are evaluated
        # at module-load.
        def nullDecorator(f):
            return f
        return nullDecorator
    """

    def profileDecorator(f):
        def _profiled(*args, **kArgs):
            name = '(%s) %s from %s' % (category, f.func_name, f.__module__)

            # showbase might not be loaded yet, so don't use
            # base.config.  Instead, query the ConfigVariableBool.
            if (category is None) or ConfigVariableBool('want-profile-%s' % category, 0).getValue():
                return profileFunc(Functor(f, *args, **kArgs), name, terse)
            else:
                return f(*args, **kArgs)
        _profiled.__doc__ = f.__doc__
        return _profiled
    return profileDecorator

# intercept profile-related file operations to avoid disk access
movedOpenFuncs = []
movedDumpFuncs = []
movedLoadFuncs = []
profileFilenames = set()
profileFilenameList = Stack()
profileFilename2file = {}
profileFilename2marshalData = {}

def _profileOpen(filename, *args, **kArgs):
    # this is a replacement for the file open() builtin function
    # for use during profiling, to intercept the file open
    # operation used by the Python profiler and profile stats
    # systems
    if filename in profileFilenames:
        # if this is a file related to profiling, create an
        # in-RAM file object
        if filename not in profileFilename2file:
            file = StringIO()
            file._profFilename = filename
            profileFilename2file[filename] = file
        else:
            file = profileFilename2file[filename]
    else:
        file = movedOpenFuncs[-1](filename, *args, **kArgs)
    return file

def _profileMarshalDump(data, file):
    # marshal.dump doesn't work with StringIO objects
    # simulate it
    if isinstance(file, StringIO) and hasattr(file, '_profFilename'):
        if file._profFilename in profileFilenames:
            profileFilename2marshalData[file._profFilename] = data
            return None
    return movedDumpFuncs[-1](data, file)

def _profileMarshalLoad(file):
    # marshal.load doesn't work with StringIO objects
    # simulate it
    if isinstance(file, StringIO) and hasattr(file, '_profFilename'):
        if file._profFilename in profileFilenames:
            return profileFilename2marshalData[file._profFilename]
    return movedLoadFuncs[-1](file)

def _installProfileCustomFuncs(filename):
    assert filename not in profileFilenames
    profileFilenames.add(filename)
    profileFilenameList.push(filename)
    movedOpenFuncs.append(__builtin__.open)
    __builtin__.open = _profileOpen
    movedDumpFuncs.append(marshal.dump)
    marshal.dump = _profileMarshalDump
    movedLoadFuncs.append(marshal.load)
    marshal.load = _profileMarshalLoad

def _getProfileResultFileInfo(filename):
    return (profileFilename2file.get(filename, None),
            profileFilename2marshalData.get(filename, None))

def _setProfileResultsFileInfo(filename, info):
    f, m = info
    if f:
        profileFilename2file[filename] = f
    if m:
        profileFilename2marshalData[filename] = m

def _clearProfileResultFileInfo(filename):
    profileFilename2file.pop(filename, None)
    profileFilename2marshalData.pop(filename, None)

def _removeProfileCustomFuncs(filename):
    assert profileFilenameList.top() == filename
    marshal.load = movedLoadFuncs.pop()
    marshal.dump = movedDumpFuncs.pop()
    __builtin__.open = movedOpenFuncs.pop()
    profileFilenames.remove(filename)
    profileFilenameList.pop()
    profileFilename2file.pop(filename, None)
    # don't let marshalled data pile up
    profileFilename2marshalData.pop(filename, None)


# call this from the prompt, and break back out to the prompt
# to stop profiling
#
# OR to do inline profiling, you must make a globally-visible
# function to be profiled, i.e. to profile 'self.load()', do
# something like this:
#
#        def func(self=self):
#            self.load()
#        import __builtin__
#        __builtin__.func = func
#        PythonUtil.startProfile(cmd='func()', filename='profileData')
#        del __builtin__.func
#
def _profileWithoutGarbageLeak(cmd, filename):
    # The profile module isn't necessarily installed on every Python
    # installation, so we import it here, instead of in the module
    # scope.
    import profile
    # this is necessary because the profile module creates a memory leak
    Profile = profile.Profile
    statement = cmd
    sort = -1
    retVal = None
    #### COPIED FROM profile.run ####
    prof = Profile()
    try:
        prof = prof.run(statement)
    except SystemExit:
        pass
    if filename is not None:
        prof.dump_stats(filename)
    else:
        #return prof.print_stats(sort)  #DCR
        retVal = prof.print_stats(sort) #DCR
    #################################
    # eliminate the garbage leak
    del prof.dispatcher
    return retVal
    
def startProfile(filename=PyUtilProfileDefaultFilename,
                 lines=PyUtilProfileDefaultLines,
                 sorts=PyUtilProfileDefaultSorts,
                 silent=0,
                 callInfo=1,
                 useDisk=False,
                 cmd='run()'):
    # uniquify the filename to allow multiple processes to profile simultaneously
    filename = '%s.%s%s' % (filename, randUint31(), randUint31())
    if not useDisk:
        # use a RAM file
        _installProfileCustomFuncs(filename)
    _profileWithoutGarbageLeak(cmd, filename)
    if silent:
        extractProfile(filename, lines, sorts, callInfo)
    else:
        printProfile(filename, lines, sorts, callInfo)
    if not useDisk:
        # discard the RAM file
        _removeProfileCustomFuncs(filename)
    else:
        os.remove(filename)

# call these to see the results again, as a string or in the log
def printProfile(filename=PyUtilProfileDefaultFilename,
                 lines=PyUtilProfileDefaultLines,
                 sorts=PyUtilProfileDefaultSorts,
                 callInfo=1):
    import pstats
    s = pstats.Stats(filename)
    s.strip_dirs()
    for sort in sorts:
        s.sort_stats(sort)
        s.print_stats(lines)
        if callInfo:
            s.print_callees(lines)
            s.print_callers(lines)

# same args as printProfile
def extractProfile(*args, **kArgs):
    global _ProfileResultStr
    # capture print output
    sc = StdoutCapture()
    # print the profile output, redirected to the result string
    printProfile(*args, **kArgs)
    # make a copy of the print output
    _ProfileResultStr = sc.getString()
    # restore stdout to what it was before
    sc.destroy()

def getSetterName(valueName, prefix='set'):
    # getSetterName('color') -> 'setColor'
    # getSetterName('color', 'get') -> 'getColor'
    return '%s%s%s' % (prefix, string.upper(valueName[0]), valueName[1:])
def getSetter(targetObj, valueName, prefix='set'):
    # getSetter(smiley, 'pos') -> smiley.setPos
    return getattr(targetObj, getSetterName(valueName, prefix))

class ScratchPad:
    """empty class to stick values onto"""
    def __init__(self, **kArgs):
        for key, value in kArgs.iteritems():
            setattr(self, key, value)
        self._keys = set(kArgs.keys())
    def add(self, **kArgs):
        for key, value in kArgs.iteritems():
            setattr(self, key, value)
        self._keys.update(kArgs.keys())
    def destroy(self):
        for key in self._keys:
            delattr(self, key)

    # allow dict [] syntax
    def __getitem__(self, itemName):
        return getattr(self, itemName)
    def get(self, itemName, default=None):
        return getattr(self, itemName, default)
    # allow 'in'
    def __contains__(self, itemName):
        return itemName in self._keys

class DestructiveScratchPad(ScratchPad):
    # automatically calls destroy() on elements passed to __init__
    def add(self, **kArgs):
        for key, value in kArgs.iteritems():
            if hasattr(self, key):
                getattr(self, key).destroy()
            setattr(self, key, value)
        self._keys.update(kArgs.keys())
    def destroy(self):
        for key in self._keys:
            getattr(self, key).destroy()
        ScratchPad.destroy(self)

class PriorityCallbacks:
    """ manage a set of prioritized callbacks, and allow them to be invoked in order of priority """
    def __init__(self):
        self._callbacks = []

    def clear(self):
        while self._callbacks:
            self._callbacks.pop()

    def add(self, callback, priority=None):
        if priority is None:
            priority = 0
        item = (priority, callback)
        bisect.insort(self._callbacks, item)
        return item

    def remove(self, item):
        self._callbacks.pop(bisect.bisect_left(self._callbacks, item))

    def __call__(self):
        for priority, callback in self._callbacks:
            callback()

if __debug__:
    l = []
    def a(l=l):
        l.append('a')
    def b(l=l):
        l.append('b')
    def c(l=l):
        l.append('c')
    pc = PriorityCallbacks()
    pc.add(a)
    pc()
    assert l == ['a']
    while len(l):
        l.pop()
    bItem = pc.add(b)
    pc()
    assert 'a' in l
    assert 'b' in l
    assert len(l) == 2
    while len(l):
        l.pop()
    pc.remove(bItem)
    pc()
    assert l == ['a']
    while len(l):
        l.pop()
    pc.add(c, 2)
    bItem = pc.add(b, 10)
    pc()
    assert l == ['a', 'c', 'b']
    while len(l):
        l.pop()
    pc.remove(bItem)
    pc()
    assert l == ['a', 'c']
    while len(l):
        l.pop()
    pc.clear()
    pc()
    assert len(l) == 0
    del l
    del a
    del b
    del c
    del pc
    del bItem

def quantize(value, divisor):
    # returns new value that is multiple of (1. / divisor)
    return float(int(value * int(divisor))) / int(divisor)

def quantizeVec(vec, divisor):
    # in-place
    vec[0] = quantize(vec[0], divisor)
    vec[1] = quantize(vec[1], divisor)
    vec[2] = quantize(vec[2], divisor)

def bound(value, bound1, bound2):
    """
    returns value if value is between bound1 and bound2
    otherwise returns bound that is closer to value
    """
    if bound1 > bound2:
        return min(max(value, bound2), bound1)
    else:
        return min(max(value, bound1), bound2)
clamp = bound

def lerp(v0, v1, t):
    """
    returns a value lerped between v0 and v1, according to t
    t == 0 maps to v0, t == 1 maps to v1
    """
    return v0 + ((v1 - v0) * t)

def randFloat(a, b=0., rng=random.random):
    """returns a random float in [a, b]
    call with single argument to generate random float between arg and zero
    """
    return lerp(a, b, rng())

import __builtin__
__builtin__.Functor = Functor
__builtin__.Stack = Stack
__builtin__.Queue = Queue
__builtin__.Enum = Enum #
__builtin__.SerialNumGen = SerialNumGen # 
__builtin__.SerialMaskedGen = SerialMaskedGen # 
__builtin__.ScratchPad = ScratchPad #
__builtin__.DestructiveScratchPad = DestructiveScratchPad #
__builtin__.uniqueName = uniqueName #
__builtin__.serialNum = serialNum #
__builtin__.clamp = clamp #
__builtin__.lerp = lerp #
__builtin__.notNone = notNone #
__builtin__.clampScalar = clampScalar #
__builtin__.printStack = printStack
__builtin__.printReverseStack = printReverseStack
__builtin__.printVerboseStack = printVerboseStack
__builtin__.invertDict = invertDict #
__builtin__.invertDictLossless = invertDictLossless #