import re
from itertools import chain

from .minted import languages
from .helpers import process_list_indentation
from .errors_warnings import Warnings

# ---------------------------------------------------------------
# regex based conversion from markdown to latex;
# main scrips for the conversion process
# functions are part of classes for clarity
# ---------------------------------------------------------------


class MDSimple:
    """
    simple substitutions that are done using a dict
    simple_sub: a dict mapping to a regular expression its replacement,
                to use with re.sub. only for simple elements of the markdown
                syntax, like "*", "`"...
    """
    simple_sub = {
        # code, bold, italics
        r"(?<!\*)\*{2}(?!\*)(.+?)(?<!\*)\*{2}(?!\*)": r"\\textbf{\1}",  # bold
        r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)": r"\\textit{\1}",  # italics
        
        # images and hyperlink
        r"(?<!!)\[(.*?)\]\((.*?)\)": r"\\href{\2}{\1}",  # hyperlink
        r"!\[(.*?)\]\((.*?)\)": r"""
\\begin{figure}[h!]
    \\centering
    \\includegraphics[width=\\linewidth]{\2}
    \\caption{\1}
\\end{figure}""",  # images

        # separators
        r"-{3,}": r"\\par\\noindent\\rule{\\linewidth}{0.4pt}",  # horizontal line
        r"<br/?>": "\n\n",  # line breaks
    }

    @staticmethod
    def convert(string: str):
        """
        perform the conversion: replace markdown syntax by TeX syntax
        :param string: the string rpr of the markdown file to convert
        :return: string with the conversion performed
        """
        for k, v in MDSimple.simple_sub.items():
            string = re.sub(k, v, string, flags=re.M)
        return string


class MDHeader:
    """
    header substitutions

    contains
    --------
    book_unnumbered: a dict to convert markdown headers to latex `book` document class unnumbered sections
    book_numbered: a dict to convert markdown headers to latex `book` document class numbered sections
    article_unnumbered: a dict to convert markdown headers to latex `book` document class unnumbered sections
    article_numbered: a dict to convert markdown headers to latex `book` document class numbered sections
    """
    book_numbered = {
        r"^\s*(\\#){1}(?!\\#?) *(.*?)$": r"\\chapter{\2}\n",  # 1st level title
        r"^\s*(\\#){2}(?!\\#?) *(.*?)$": r"\\section{\2}\n",  # 2nd level title
        r"^\s*(\\#){3}(?!\\#?) *(.*?)$": r"\\subsection{\2}\n",  # 3rd level title
        r"^\s*(\\#){4}(?!\\#?) *(.*?)$": r"\\subsubsection{\2}\n",  # 4th level title
        r"^\s*(\\#){5,}(?!\\#?) *(.*?)$": r"\n\n\\textbf{\2}\n\n",  # 5th+ level title
    }
    book_unnumbered = {
        r"^\s*(\\#){1}(?!\\#?) *(.*?)$": r"\\chapter*{\2}\n\\addcontentsline{toc}{chapter}{\2}\n",
        r"^\s*(\\#){2}(?!\\#?) *(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{section}{\2}\n",
        r"^\s*(\\#){3}(?!\\#?) *(.*?)$": r"\\subsection*{\2}\n\\addcontentsline{toc}{subsection}{\2}\n",
        r"^\s*(\\#){4}(?!\\#?) *(.*?)$": r"\\subsubsection*{\2}\n\\addcontentsline{toc}{subsubsection}{\2}\n",
        r"^\s*(\\#){5,}(?!\\#?) *(.*?)$": r"\n\n\\noindent{}\\textbf{\2}\n\n",
    }
    article_numbered = {
        r"^\s*(\\#){1}(?!\\#?) *(.*?)$": r"\\section{\2}\n",  # 1st level title
        r"^\s*(\\#){2}(?!\\#?) *(.*?)$": r"\\subsection{\2}\n",  # 2nd level title
        r"^\s*(\\#){3}(?!\\#?) *(.*?)$": r"\\subsubsection{\2}\n",  # 3rd level title
        r"^\s*(\\#){4,}(?!\\#?) *(.*?)$": r"\n\n\\noindent{}\\textbf{\2}\n\n",  # 4th level title
    }
    article_unnumbered = {
        r"^\s*(\\#){1}(?!\\#?) *(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{section}{\2}\n",
        r"^\s*(\\#){2}(?!\\#?) *(.*?)$": r"\\section*{\2}\n\\addcontentsline{toc}{subsection}{\2}\n",
        r"^\s*(\\#){3}(?!\\#?) *(.*?)$": r"\\subsection*{\2}\n\\addcontentsline{toc}{subsubsection}{\2}\n",
        r"^\s*(\\#){4,}(?!\\#?) *(.*?)$": r"\n\n\\noindent{}\\textbf{\2}\n\n",
    }

    @staticmethod
    def convert(string: str, unnumbered: bool, document_class: str):
        """
        perform the conversion: replace markdown titles by numbered or unnumbered LaTeX titles
        :param string: the markdown representation of the string to convert
        :param unnumbered: flag argument indicating that the LaTeX headers should be unnumbered
        :param document_class: the class to convert the document to
        :return: processed string
        """
        if unnumbered is True:
            if document_class == "article":
                substitute = MDHeader.article_unnumbered
            else:
                substitute = MDHeader.book_unnumbered
        else:
            if document_class == "article":
                substitute = MDHeader.article_numbered
            else:
                substitute = MDHeader.book_numbered
        for k, v in substitute.items():
            string = re.sub(k, v, string, flags=re.M)
        return string


class MDQuote:
    """
    inline and block quote substitution

    contains
    --------
    block_quote(): replace multiline markdown quotes (">") into latex \quote{}
    inline_quote(): transform markdown quotes (`"`, `'`) into latex french or anglo saxon quotes
    """
    @staticmethod
    def block_quote(string: str):
        """
        replace a markdown quote ">" with a latex quote (\quote{}).
        works in multiline mode.

        :param string:  the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        string = re.sub(
            r"^((>.+(\n|$))+)",
            r"\\begin{quotation} \n \1 \n \\end{quotation}",
            string, flags=re.M
        ).replace(">", " ")
        return string

    @staticmethod
    def inline_quote(string: str, french_quote: bool):
        """
        convert the markdown quotes to LaTeX.
        :param string: the string representation of the markdown file
        :param french_quote: translate the quotes as french quotes (\enquote{})
                              or anglo-saxon quotes (``'')
        :return: the updated string representation of a markdown file
        """
        if french_quote is True:
            string = re.sub(r"\"(.*)\"", r"\\enquote{\1}", string)
            string = re.sub(r"'(.*)'", r'``\1"', string)
        else:
            string = re.sub(r"\"(.*)\"", r'``\1"', string)
            string = re.sub(r"'(.*)'", r"`\1'", string)
        return string


class MDList:
    """
    list substitution: replace markdown nested lists by LaTeX nested lists

    contains
    --------
    unoredered_l(): create latex `itemize` envs from md unnumbered lists
    ordered_l(): create latex `enumerate` envs from md numbered lists
    """
    @staticmethod
    def unordered_l(string: str):
        """
        translate a markdown unnumbered list into a latex `itemize` environment
        :param string:  the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        lists = re.finditer(r"((^[ \t]*?-(?!-{2,}).*?\n)+(.+\n)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "@@LISTTOKEN@@")  # add token to source
            lstext = re.sub(r"\n(?!\s*-)", " ", lstext, flags=re.M)  # group list item into one line

            lsitems = process_list_indentation(lstext)  # process the visual indentation

            # build the `\itemize{}`
            items = ""
            prev = 0  # previous indentation level
            for li in lsitems:
                # open/close the good number of envs
                if li[1] - prev > 0:  # if there are envs to open; shouldn't be > 1 env to open, but just in case
                    items += "\\begin{itemize} \n \\item " * (li[1] - prev)
                    items += li[0] + "\n"
                elif li[1] - prev < 0:  # if there are envs to close
                    items += "\\end{itemize}\n" * (prev - li[1])
                    items += "\\item " + li[0] + "\n"
                else:  # no envs to open/close
                    items += "\\item " + li[0] + "\n"
                prev = li[1]

            items += "\\end{itemize}\n" * prev  # close the remaining nested envs

            # once the list of \item and possibly nested `itemize` is built,
            # build the final itemize, add it to the markdown string and that's it !
            itemize = r"""
\begin{itemize}
@@ITEMTOKEN@@
\end{itemize}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", itemize)

        return string

    @staticmethod
    def ordered_l(string: str):
        """
        translate a markdown numbered list into a latex `enumerate` environment
        the functionning is quite the same as `unnumbered_list()`
        :param string: the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        lists = re.finditer(r"((^[ \t]*?\d+\..*?\n?)+(.+\n?)*)+", string, flags=re.MULTILINE)
        for ls in lists:
            # prepare list building
            lstext = ls[0]  # extract list text
            string = string.replace(lstext, "@@LISTTOKEN@@")  # replace source list by token
            lstext = re.sub(r"\n(?!\s*\d+\.)", " ", lstext, flags=re.M)  # group list items into single line

            lsitems = process_list_indentation(lstext)  # process the visual indentation

            # build the `\enumerate{}`
            items = ""
            prev = 0  # previous indentation level
            for li in lsitems:
                # remove numbering and whitespace
                li[0] = re.sub(r"^[ \t]*\d+\. *", "", li[0])
                
                # open/close the good number of envs
                if li[1] - prev > 0:  # if there are envs to open; shouldn't be > 1 env to open, but just in case
                    items += "\\begin{enumerate} \n \\item " * (li[1] - prev)
                    items += li[0] + "\n"
                elif li[1] - prev < 0:  # if there are envs to close
                    items += "\\end{enumerate}\n" * (prev - li[1])
                    items += "\\item " + li[0] + "\n"
                else:  # no envs to open/close
                    items += "\\item " + li[0] + "\n"
                prev = li[1]

            items += "\\end{enumerate}\n" * prev  # close the remaining nested envs

            # once the list of \item and possibly nested `enumerate` is built,
            # build the final enumerate, add it to the markdown string and that's it !
            enumerate = r"""
            \begin{enumerate}
            @@ITEMTOKEN@@
            \end{enumerate}""".replace("@@ITEMTOKEN@@", items)
            string = string.replace("@@LISTTOKEN@@", enumerate)

        return string

class MDCode:
    """
    block and inline code substitution

    contains
    --------
    block_code(): create a latex minted or lstlisting env from a md block of code
    inline_code(): create a latex mintinline env from inline md code
    """
    @staticmethod
    def inline_code(string: str, language: str):
        """
        translate inline code in markdown-formatted text into a mintinline environment. Optionally specify a language for minted to use for syntax highlighting.

        :param string: the string representation of the markdown file
        :param language: a string specifying the language to use for syntax highlighting, see https://pygments.org/docs/lexers/
        :return: the updated string representation
        """
        
        matches = re.finditer(r"`([^`^\n]+)`", string)
        for m in matches:
            code = m[0]
            inline_snippet = r"\mintinline{" + language + r"}{" + m[1] + r"}"
            string = string.replace(code, inline_snippet)
        
        return string

    @staticmethod
    def block_code(string: str, language):
        """
        translate a markdown block of code into a minted environment.
        
        the function tries to match a md block code "```...```". if the
        block of code is matched, the code body is inserted into a minted environment.

        the function also tries to extract the following from the first line of the code block:
        - a code language specification, which is checked for support
          by minted/pygments (defaulting to "text" if not supported).
        - a title, which is converted to a caption if present.
        - hl_lines, which is converted to a minted option if present.

        :param string: the string representation of the markdown file
        :return: the updated string representation of a markdown file
        """
        matches = re.finditer(r"```((.|\n)*?)```", string, flags=re.M)
        for m in matches:
            code = m[0]  # isolate the block of code
            string = string.replace(code, "@@MINTEDTOKEN@@")  # to reinject code to string later

            # extract info string
            info_string = re.search(r"```([^\n]*)$", code, flags=re.M)[0].replace("```", "").strip()  # ugly but works
            
            env = r"""
\begin{listing}[H]
\begin{minted}{@@LANGTOKEN@@}
@@CODETOKEN@@
\end{minted}
@@CAPTIONTOKEN@@
\end{listing}"""  # env to add the code to; ugly indentation to avoid messing up the .tex file

            # extract code body
            code_body = re.sub(r"```.*?\n((.|\n)+?)```", r"\1", code, flags=re.M)  
            # add code body to the latex env
            env = env.replace("@@CODETOKEN@@", code_body)
            
            # assume language is the first word in the info string
            # cf. https://spec.commonmark.org/0.31.2/#fenced-code-blocks
            lang_info = re.search(r'^([0-9A-Za-z_-]+) *', info_string)
            if lang_info:
                lang = lang_info[1]
            # if the used language is supported by minted, create a minted inside
            # a listing environment to hold the code
                if not lang in languages:
                    Warnings("lang_not_supported", lang)
                    lang = "text"
            else:
                lang = "text"
            # add code language specification to the latex env
            env = env.replace("@@LANGTOKEN@@", lang)
            
            # titles specified like title="A nice code block" in the info string
            # will be converted to captions
            title_info = re.search(r'title="([^"]+)"', info_string)
            if title_info:
                env = env.replace("@@CAPTIONTOKEN@@", r'\caption{' + title_info[1] + r'}')
            else:  # remove captiontoken line
                env = env.replace("@@CAPTIONTOKEN@@\n","")

            # highlight lines specified like hl_lines="1 11 4-6" in the info string
            hl_lines_info = re.search(r'hl_lines="([^"]+)"', info_string)
            if hl_lines_info:
                lines = ", ".join(hl_lines_info[1].split(" ")) # add commas to hl_lines
                env = env.replace(r"begin{minted}", r"begin{minted}[highlightlines={" + lines + r"}]")

            # reinject latex code to string
            string = string.replace("@@MINTEDTOKEN@@", env)

        return string


class MDReference:
    r"""
    substitutions for references inside a markdown document.
    currently only for footnote substitutions

    contains
    --------
    footnote(): replace markdown footnotes (`[\^\d+]`) into latex `\footnote{}`
    """
    @staticmethod
    def footnote(string: str):
        r"""
        translate a markdown footnode `[^\d+]` to a latex footnote (`\footnote{}`)

        the structure of a markdown footnote:
        - This is the body of the text [^1] <-- body of the text
                                       ^^^^ <-- pointer to the footnote
        - [^1]: this is the footnote  <-- footnote
          ^^^^  <------------------------ pointer to the footnote mark
        in turn, what we need to do is remove the pointers, match the body of the
        footnote and add it to a `\footnote{}`

        :param string: the string representation of a markdown file
        """
        footnotes = re.finditer(r"\[\\\^\d+\](?![ \t]*:)", string, flags=re.M)
        for match in footnotes:
            try:
                pointer = match[0]  # extract the footnote pointer (the pointer to the actual footnote)
                key = re.search(r"\d+", pointer)[0]  # extract the footnote n°
                fnote = re.search(
                    fr"(\[\\\^%s\]:)(.+\n?)*" % key,
                    string, flags=re.M
                )  # match the proper footnote (with the good key)
                texnote = re.sub(r"\s+", " ", fnote[0].replace(fnote[1], ""))  # remove the pointer + normalize space

                if not re.search("^\s*$", texnote):  # if the note isn't empty; else, delete it
                    texnote = r"\footnote{" + texnote + "}"
                    string = string.replace(fnote[0], "")  # delete the markdown footnote
                    string = string.replace(pointer, texnote)  # add the \footnote to string
                else:
                    # delete the footnote body and pointers
                    string = string.replace(pointer, "")
                    string = string.replace(fnote[0], "")

            except TypeError:
                # a footnote pointer may point to nothing; conversely, a footnote
                # may to have a ref in the body. in that case, pass now and delete every loose
                # footnote part right after
                pass
        # delete all loose footnote strings
        string = re.sub(r"\[\\\^\d+\](?![ \t]*:)", "", string, flags=re.M)
        string = re.sub(r"(\[\\\^\d+\]:)(.+\n?)*", "", string, flags=re.M)

        return string


class MDCleaner:
    """
    clean the input markdown and output LaTeX.

    contains
    --------
    prepare_markdown(): replace markdown document by escaping special tex characters and
                        removing code substrings from the rest of the pipeline
    clean_tex(): clean the tex created and reinsert code substrings at the end of the pipeline
    """
    @staticmethod
    def prepare_markdown(string: str):
        """
        prepare markdown for the transformation:
        - strip empty lines (matching the expression `^[ \t]*\n`) by removing inline spaces.
          used at the beginning of the process, it will greatly simplify the following matches and replacement.
        - escape latex special characters. this is also useful because of our use of
          `_` in `@@*TOKEN*@@` strings used for replacements.

        this function is used after `block_code()` and `inline_code()` to avoid replacing
        special characters that should be interpreted verbatim by LaTeX.
        to escape all `minted`, `lstlisting`, and `mintinline` code we use a dict that stores all
        these substrings of code.

        :param string: the string representation of a markdown file
        :return: the updated string representation of a markdown file
        """
        string = re.sub(r"^[ \t]*\n", r"\n\n", string, flags=re.M)
        string = string.replace("@@", "USERRESERVEDTOKEN")  # @@ is our special token, so we need to escape it
        #                                                     in case it is present in the user file

        # escape all code blocks so that their content isn't escaped.
        # for that, store all code blocks in a dict, replace them in `string`
        # with a special token. this token uses `+` because they aren't LaTeX
        # special characters
        block_codematch = re.finditer(r"\\begin\{(listing|lstlisting)}(.|\n)*?\\end\{(listing|lstlisting)}", string, flags=re.M)
        inline_codematch = re.finditer(r"\\mintinline{.*}{.*}", string, flags=re.M)
        n = 0
        codedict = {}
        for match in chain(block_codematch, inline_codematch):
            code = match[0]  # extract text
            string = string.replace(code, f"@@CODETOKEN{n}@@")
            codedict[f"@@CODETOKEN{n}@@"] = code
            n += 1        

        string = string.replace("{==", "") # begin highlight (removed)
        string = string.replace("==}", "") # end highlight (removed)
        string = string.replace(r"{", r"\{")
        string = string.replace(r"}", r"\}")
        # string = re.sub("(?<![^\]]\[)\^", r"\^", string, flags=re.M)
        string = re.sub(r"\\(?![\{\}])", r"\\textbackslash{}", string, flags=re.M)
        string = string.replace(r">", r"\textgreater{}")
        string = string.replace(r"#", r"\#")
        string = string.replace("$", r"\$")
        string = string.replace("%", r"\%")
        string = string.replace(r"$", r"\&")
        string = string.replace(r"~", r"\~")
        string = string.replace("_", r"\_")
        string = string.replace("&", r"\&")
        string = re.sub("\^", r"\\^", string, flags=re.M)
        # print(string)

        return string, codedict

    @staticmethod
    def clean_tex(string: str, codedict: dict):
        """
        clean spaces around latex commands + uneccessary spaces created during
        transformation
        :param string: the string representation of the markdown file
        :param codedict: the dictionnary containing escaped code blocks
        :return: the updated string representation of a markdown file
        """
        # rebuild the string by reinjecting the code blocks
        for k, v in codedict.items():
            string = string.replace(k, v)

        # clean spaces
        # string = re.sub(r"((?<!^ ) )+", " ", string, flags=re.M)  # replace multiple spaces with a single space, but not if they are at the beginning of a line
        # string = re.sub(r"{\s+", r"{", string, flags=re.M)  # remove whitespace after opening curly brace
        # string = re.sub(r"\s+}", r"}", string, flags=re.M)  # remove whitespace before closing curly brace
        string = re.sub(r"\n{2,}", r"\n\n", string, flags=re.M)  # reduce 2+ consecutive newlines to 2
        string = re.sub(r"(\\begin\{.*?)\n{2,}", r"\1\n", string, flags=re.M)  # replace multiple consecutive newlines after \begin with just one
        string = re.sub(r"\n{2,}( *\\end\{)", r"\n\1", string, flags=re.M) # replace multiple consecutive newlines before \end with just one

        string = string.replace("USERRESERVEDTOKEN", "@@")

        return string


class MDFrontmatter:
    """
    remove Markdown file frontmatter written in YAML format
    """
    
    @staticmethod
    def convert(string: str):
        """
        perform the conversion: delete markdown frontmatter
        :param string: the string rpr of the markdown file to convert
        :return: string with the conversion performed
        """
        
        flags = re.MULTILINE | re.DOTALL
        string = re.sub(r"^---.*---", "", string, flags=flags)

        return string
