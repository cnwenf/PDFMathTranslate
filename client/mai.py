# -*- coding: utf-8 -*-
import re
import sys
sys.path.append("/Users/cnwenf/code/PDFMathTranslate/pdf2zh")
from pdf2zh.pdf2zh import main

if __name__ == '__main__':
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(main(["chasse.pdf"]))