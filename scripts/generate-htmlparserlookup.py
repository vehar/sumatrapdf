"""
This script generates the fairly fast C code for the following function:
Given a string, see if it belongs to a known set of strings. If it does,
return a value corresponding to that string.
"""

import os
from util import group, verify_started_in_right_directory

Template_Defines = """\
#define CS1(c1)             (c1)
#define CS2(c1, c2)         (CS1(c1) | (c2 << 8))
#define CS3(c1, c2, c3)     (CS2(c1, c2) | (c3 << 16))
#define CS4(c1, c2, c3, c4) (CS3(c1, c2, c3) | (c4 << 24))

#define STR1(s) ((s)[0])
#define STR2(s) (STR1(s) | ((s)[1] << 8))
#define STR3(s) (STR2(s) | ((s)[2] << 16))
#define STR4(s) (STR3(s) | ((s)[3] << 24))

#define STR1i(s) (tolower((s)[0]))
#define STR2i(s) (STR1i(s) | (tolower((s)[1]) << 8))
#define STR3i(s) (STR2i(s) | (tolower((s)[2]) << 16))
#define STR4i(s) (STR3i(s) | (tolower((s)[3]) << 24))
"""

Template_Find_Function = """\
%s Find%s(const char *name, size_t len)
{
	uint32_t key = 0 == len ? 0 : 1 == len ? STR1i(name) :
	               2 == len ? STR2i(name) : 3 == len ? STR3i(name) : STR4i(name);
	switch (key) {
	%s
	}
	return %s;
}
"""

Template_Enumeration = """\
enum %s {
	%s
};
"""

Template_Selector = """\
bool %s(%s item)
{
	switch (item) {
	%s
		return true;
	default:
		return false;
	}
}
"""

# given e.g. "br" returns "Tag_Br"
def getEnumName(name, prefix):
	parts = name.replace("-", ":").split(":")
	parts = [p[0].upper() + p[1:].lower() for p in parts]
	return "_".join([prefix] + parts)

# given e.g. "abcd" returns "'a','b','c','d'"
def splitChars(chars):
	return "'" + "','".join(chars) + "'"

def unTab(string):
	return string.replace("\t", "    ")

# creates a lookup function that works with one switch for quickly
# finding (or failing to find) the correct value
def createFastFinder(list, type, default, caseInsensitive, funcName=None):
	list = sorted(list, key=lambda a: a[0])
	output = []
	while list:
		name, value = list.pop(0)
		if len(name) < 4:
			# no further comparison is needed for names less than 4 characters in length
			output.append('case CS%d(%s): return %s;' % (len(name), splitChars(name), value))
		else:
			# for longer names, do either another quick check (up to 8 characters)
			# or use str::EqN(I) for longer names
			output.append('case CS4(%s):' % "'%s'" % "','".join(name[:4]))
			while True:
				if len(name) == 4:
					output.append("	if (4 == len) return %s;" % value)
				elif len(name) <= 8:
					rest = name[4:]
					output.append('	if (%d == len && CS%d(%s) == STR%di(name + 4)) return %s;' %
						(len(name), len(rest), splitChars(rest), len(rest), value))
				else:
					output.append('	if (%d == len && str::EqNI(name + 4, "%s", %d)) return %s;' %
						(len(name), name[4:], len(name) - 4, value))
				# reuse the same case for names that start the same
				if not list or list[0][0][:4] != name[:4]:
					break
				name, value = list.pop(0)
			output.append('	break;')
	
	output = Template_Find_Function % (type, funcName or type, "\n	".join(output), default)
	if not caseInsensitive:
		output = output.replace("STR1i(", "STR1(").replace("STR2i(", "STR2(")
		output = output.replace("STR3i(", "STR3(").replace("STR4i(", "STR4(")
		output = output.replace("str::EqNI(", "str::EqN(")
	return unTab(output)

# creates an enumeration that can be used as a result for the lookup function
# (which would allow to "internalize" a string)
def createTypeEnum(list, type, default):
	list = sorted(list, key=lambda a: a[0])
	parts = group([item[1] for item in list] + [default], 5)
	return unTab(Template_Enumeration % (type, ",\n	".join([", ".join(part) for part in parts])))

def createFastSelector(fullList, nameList, funcName, type):
	cases = ["case %s:" % value for (name, value) in fullList if name in nameList]
	return unTab(Template_Selector % (funcName, type, "\n	".join([" ".join(part) for part in group(cases, 4)])))

########## HTML tags and attributes ##########

# This list has been generated by instrumenting HtmlFormatter.cpp
# to dump all tags we see in a mobi file and also some from EPUB and FB2 files
List_HTML_Tags = "a abbr acronym area audio b base basefont blockquote body br center code col dd div dl dt em font frame h1 h2 h3 h4 h5 h6 head hr html i img image input lh li link mbp:pagebreak meta nav object ol p pagebreak param pre s section small span strike strong style sub subtitle sup svg table td th title tr tt u ul video"
List_HTML_Attrs = "size href color filepos border valign rowspan colspan link vlink style face value bgcolor class id mediarecindex controls recindex title lang clear xmlns width align height"
List_Align_Attrs = "left right center justify"

# these tags must all also appear in List_HTML_Tags (else they're ignored)
List_Self_Closing_Tags = "area base basefont br col frame hr img input link mbp:pagebreak meta pagebreak param"
List_Inline_Tags = "a abbr acronym audio b code em font i s small span strike strong sub sup tt u video"

########## HTML and XML entities ##########

Template_Entities_Comment = """\
// map of entity names to their Unicode runes, cf.
// http://en.wikipedia.org/wiki/List_of_XML_and_HTML_character_entity_references
"""

from htmlentitydefs import entitydefs
entitydefs['apos'] = "'" # only XML entity that isn't an HTML entity as well
List_HTML_Entities = []
for name, value in entitydefs.items():
	List_HTML_Entities.append((name, value[2:-1] or str(ord(value))))

########## CSS colors ##########

# array of name/value for css colors, value is what goes inside MKRGB()
# based on https://developer.mozilla.org/en/CSS/color_value
# TODO: add more colors
List_CSS_Colors = [
	("black",        "  0,  0,  0"),
	("white",        "255,255,255"),
	("gray",         "128,128,128"),
	("red",          "255,  0,  0"),
	("green",        "  0,128,  0"),
	("blue",         "  0,  0,255"),
	("yellow",       "255,255,  0"),
];
# fallback is the transparent color MKRGBA(0,0,0,0)

########## main ##########

Template_Lookup_Header = """\
/* Copyright 2012 the SumatraPDF project authors (see AUTHORS file).
   License: Simplified BSD (see COPYING.BSD) */

// This file is auto-generated by generate-htmlparserlookup.py

#ifndef HtmlParserLookup_h
#define HtmlParserLookup_h

%(enum_htmltag)s
%(enum_alignattr)s
HtmlTag         FindHtmlTag(const char *name, size_t len);
bool            IsTagSelfClosing(HtmlTag item);
bool            IsInlineTag(HtmlTag item);
AlignAttr       FindAlignAttr(const char *name, size_t len);
uint32_t        FindHtmlEntityRune(const char *name, size_t len);

#endif
"""

Template_Lookup_Code = """\
/* Copyright 2012 the SumatraPDF project authors (see AUTHORS file).
   License: Simplified BSD (see COPYING.BSD) */

// This file is auto-generated by generate-htmlparserlookup.py

#include "BaseUtil.h"
#include "HtmlParserLookup.h"

%(code_defines)s
%(code_htmltag)s
%(code_selfclosing)s
%(code_inlinetag)s
%(code_alignattr)s
%(code_htmlentity)s
"""

def main():
	tags = [(name, getEnumName(name, "Tag")) for name in List_HTML_Tags.split()]
	attrs = [(name, getEnumName(name, "Attr")) for name in List_HTML_Attrs.split()]
	aligns = [(name, getEnumName(name, "Align")) for name in List_Align_Attrs.split()]
	cssColors = [(name, "MKRGB(%s)" % value) for (name, value) in List_CSS_Colors]
	
	enum_htmltag = createTypeEnum(tags, "HtmlTag", "Tag_NotFound")
	enum_htmlattr = createTypeEnum(attrs, "HtmlAttr", "Attr_NotFound")
	enum_alignattr = createTypeEnum(aligns, "AlignAttr", "Align_NotFound")
	
	code_defines = Template_Defines
	code_htmltag = createFastFinder(tags, "HtmlTag", "Tag_NotFound", True)
	code_htmlattr = createFastFinder(attrs, "HtmlAttr", "Attr_NotFound", True)
	code_selfclosing = createFastSelector(tags, List_Self_Closing_Tags.split(), "IsTagSelfClosing", "HtmlTag")
	code_inlinetag = createFastSelector(tags, List_Inline_Tags.split(), "IsInlineTag", "HtmlTag")
	code_alignattr = createFastFinder(aligns, "AlignAttr", "Align_NotFound", True)
	code_htmlentity = Template_Entities_Comment + "\n" + createFastFinder(List_HTML_Entities, "uint32_t", "-1", False, "HtmlEntityRune")
	code_csscolor = createFastFinder(cssColors, "ARGB", "MKRGBA(0,0,0,0)", True, "CssColor")
	
	content = Template_Lookup_Header % locals()
	open("src/utils/HtmlParserLookup.h", "wb").write(content.replace("\n", "\r\n"))
	content = Template_Lookup_Code[:-1] % locals()
	open("src/utils/HtmlParserLookup.cpp", "wb").write(content.replace("\n", "\r\n"))

if __name__ == "__main__":
	if os.path.exists("generate-htmlparserlookup.py"):
		os.chdir("..")
	verify_started_in_right_directory()
	main()