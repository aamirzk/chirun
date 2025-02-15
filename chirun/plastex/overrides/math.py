from plasTeX import Command, sourceChildren, sourceArguments, Macro, Environment
from plasTeX.Base.LaTeX.Arrays import Array
from plasTeX.Base.LaTeX import Math, Pictures
from plasTeX.Base.TeX import Primitives
from plasTeX.Tokenizer import Token
from plasTeX.Logging import getLogger

log = getLogger()


# Overrive boxcommands inside MathJaX to avoid extra <script type="math/tex">
class BoxCommand(Primitives.BoxCommand):
    class math(Math.math):
        def normalize(self, charsubs=None):
            return Macro.normalize(self, charsubs=None)

        @property
        def source(self):
            if self.hasChildNodes():
                return r'\(%s\)' % sourceChildren(self)
            return r'\('


class hbox(BoxCommand):
    pass


class vbox(BoxCommand):
    pass


class text(BoxCommand):
    args = 'self'


class tag(BoxCommand):
    args = 'self'


class mbox(BoxCommand):
    args = 'self'


class TextCommand(BoxCommand):
    pass

# Overrive math mode in picture env to avoid extra <script type="math/tex">
class picture(Pictures.picture):
    class math(Math.math):
        def normalize(self, charsubs=None):
            return Macro.normalize(self, charsubs=None)

        @property
        def source(self):
            if self.hasChildNodes():
                return r'\(%s\)' % sourceChildren(self)
            return r'\('


# Use <script type="math/tex"> to avoid problems with less than symbol in MathJax
class math(Math.math):
    def normalize(self, charsubs=None):
        return Macro.normalize(self, charsubs=None)

    @property
    def source(self):
        if self.hasChildNodes():
            return r'<script type="math/tex">{}</script>'.format(sourceChildren(self))
        return ''


Math.math = math


class displaymath(Math.displaymath):
    @property
    def source(self):
        return sourceChildren(self).strip()


Math.displaymath = displaymath


class MathEnvironment(Math.Environment):
    mathMode = True

    def normalize(self, charsubs=None):
        return Environment.normalize(self, charsubs=None)

    @property
    def source(self):
        if self.ref:
            return u"\\begin{{{0}}}{1}\\tag{{{2}}}\\end{{{0}}}".format(
                self.tagName,
                sourceChildren(self).strip(),
                self.ref)
        else:
            return u"\\begin{{{0}}}{1}\\end{{{0}}}".format(
                self.tagName,
                sourceChildren(self).strip())


Math.MathEnvironment = MathEnvironment


class equation(MathEnvironment):
    blockType = True
    counter = 'equation'


Math.equation = equation


class EqnarrayStar(Math.EqnarrayStar):
    class ArrayCell(Math.EqnarrayStar.ArrayCell):
        @property
        def source(self):
            return '\\displaystyle {content}'.format(content=sourceChildren(self, par=False).strip())

    class ArrayRow(Array.ArrayRow):
        @property
        def source(self):
            s = []
            argSource = sourceArguments(self.parentNode)
            if not argSource:
                argSource = ' '
            if self.ref:
                s.append(r"\tag{%s}" % self.ref)
            for cell in self:
                s.append(sourceChildren(cell, par=not(self.parentNode.mathMode)))
                if cell.endToken is not None:
                    s.append(cell.endToken.source)
            if self.endToken is not None:
                s.append(self.endToken.source)
            return ''.join(s)


Math.EqnarrayStar = EqnarrayStar


class eqnarray(EqnarrayStar):
    macroName = None
    counter = 'equation'

    class EndRow(Array.EndRow):
        """ End of a row """
        counter = 'equation'

        def invoke(self, tex):
            res = Array.EndRow.invoke(self, tex)
            res[1].ref = self.ref
            self.ownerDocument.context.currentlabel = res[1]
            return res

    def invoke(self, tex):
        res = EqnarrayStar.invoke(self, tex)
        if self.macroMode == self.MODE_END:
            return res
        res[1].ref = self.ref
        return res


Math.eqnarray = eqnarray


class MathShift(Command):
    """
    The '$' character in TeX
    This macro detects whether this is a '$' or '$$' grouping.  If
    it is the former, a 'math' environment is invoked.  If it is
    the latter, a 'displaymath' environment is invoked.
    """
    macroName = 'active::$'
    inEnv = []

    def invoke(self, tex):
        r"""
        This gets a bit tricky because we need to keep track of both
        our beginning and ending.  We also have to take into
        account \mbox{}es.
        """
        inEnv = type(self).inEnv

        current = self.ownerDocument.createElement('math')
        for t in tex.itertokens():
            if t.catcode == Token.CC_MATHSHIFT:
                if inEnv and inEnv[-1] is not None and type(inEnv[-1]) is type(current):
                    # Don't switch to displaymath element if already inside a math element
                    tex.pushToken(t)
                else:
                    current = self.ownerDocument.createElement('displaymath')
            else:
                tex.pushToken(t)
            break

        # See if this is the end of the environment
        if inEnv and inEnv[-1] is not None and type(inEnv[-1]) is type(current):
            inEnv.pop()
            current.macroMode = Command.MODE_END
            self.ownerDocument.context.pop(current)
            return [current]

        inEnv.append(current)
        self.ownerDocument.context.push(current)

        return [current]


Primitives.MathShift = MathShift
