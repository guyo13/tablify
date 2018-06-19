from sys import version as PY_VER

if PY_VER[0] == "2":
    STR_TYPES = (str, unicode)
else:
    STR_TYPES = (str,)

ITERABLES = (list, tuple, set)
HEADER_TYPES = ITERABLES + STR_TYPES
LINE_TYPES = HEADER_TYPES
HEADER_PROPS = ("width", "text_dir", "row_delimiter", "left_delimiter", "right_delimiter", "auto_resize", "truncate")
 
class Formatter(object):
    def __init__(self, width=10,
                 text_dir="ltr",
                 row_delim="-",
                 column_delim_left="| ",
                 column_delim_right=" ",
                 auto_resize=False,
                 truncate=True
                ):
        self.width = int(width)
        self.text_dir = text_dir
        self.row_delim = row_delim
        self.column_delim_left = column_delim_left
        self.column_delim_right = column_delim_right
        self.auto_resize = auto_resize
        self.truncate = truncate
        self.__props = {
                        "width": self.width,
                        "text_dir": self.text_dir,
                        "row_delimiter": self.row_delim,
                        "left_delimiter": self.column_delim_left,
                        "right_delimiter": self.column_delim_right,
                        "auto_resize": self.auto_resize,
                        "truncate": self.truncate,
                       }
    
    def get(self, prop):
        return self.__props.get(prop)
        
DEFAULT_FORMATTER = Formatter()

class Table(object):
    def __init__(self, header=None, formatter=DEFAULT_FORMATTER):
        self.formatter = formatter
        self.__row_template = None
        self.__row_spacer = None
        self.header = header
        self.__lines = []
        self.generator = None

    @property
    def header(self):
        return self._header
    @header.setter
    def header(self, header):
        """Expects an interable that contains the column names - for example: ("product", "price", "stock",) or ["color", "shape", "material"] - , or
           an iterable that contains dict elements that contains formatting - for example: ({"key": "product", "width": 5}, {"key": "price", "width": 7},) , or
           a comma delimited string that describes the column names - for example: 'product,price,stock' 
        """
        arr = []
        if header == None:
            self._header = arr
            return
        htype = type(header)
        if htype not in HEADER_TYPES:
            raise ValueError("Header type must be either one of: {}".format(HEADER_TYPES))
        if htype not in ITERABLES:
            header = header.split(",")
        for i, elem in enumerate(header):
            if not isinstance(elem, dict):
                try:
                    t = str(elem)
                except:
                    raise ValueError("Can't convert element in position {} of type {}".format(i, type(elem)))
                else:
                    arr.append({"key": t,
                                "width": self.formatter.width})
            else:
                key = elem.get("key")
                width = elem.get("width") or self.formatter.width
                text_dir = elem.get("text_dir")
                row_delimiter = elem.get("row_delimiter")
                left_delimiter = elem.get("left_delimiter")
                right_delimiter = elem.get("right_delimiter")
                auto_resize = elem.get("auto_resize")
                truncate = elem.get("truncate")
                obj = {
                       "key":key,
                       "width": width,
                       "text_dir": text_dir,
                       "row_delimiter": row_delimiter,
                       "left_delimiter": left_delimiter,
                       "right_delimiter": right_delimiter,
                       "auto_resize": auto_resize,
                       "truncate": truncate
                      }
                for k in list(obj.keys()):
                    if obj[k] == None:
                        obj.pop(k, None)
                arr.append(obj)
        self._header = arr
        self.gen_row_template_string()
        self.gen_row_spacer()

    def writeline(self, line):
        if line == None:
            return
        ltype = type(line)
        if ltype not in LINE_TYPES:
            raise ValueError("Line type must be either one of: {}".format(LINE_TYPES))
        if ltype in ITERABLES:
            line = ','.join(str(col) for col in line)
            #line = ','.join(line) # Does not allow lines that come as list/tuple and contain integers for example
        self.__lines.append(line)
        split = line.split(',')
        for i,col in enumerate(split):
            if self._get_header_prop(i, "auto_resize") != True:
                continue
            l = len(col)
            width = self._get_header_prop(i, "width")
            if l > width:
                self._set_header_prop(i, 'width', l)
                
    
    def getlines(self):
        return self.__lines
 
    def gen_row_template_string(self, add_newline=True):
        addnl = ""
        if add_newline:
            addnl = "\n"
        template = addnl
        for elem in self.header:
            text_dir = elem.get("text_dir") or self.formatter.text_dir
            text_dir_str = ":<" if text_dir=="ltr" else ":>"
            text_dir_str += str(elem.get("width") or self.formatter.width)
            left = elem.get("left_delimiter") or self.formatter.column_delim_left
            right = elem.get("right_delimiter") or self.formatter.column_delim_right
            item = left + "{" + text_dir_str + "}" + right
            template += item
        template += addnl
        self.__row_template = template
        return template
            
    def gen_row_spacer(self):
        line = ""
        for elem in self.header:
            width =  elem.get("width")
            left = elem.get("left_delimiter") or self.formatter.column_delim_left
            right = elem.get("right_delimiter") or self.formatter.column_delim_right
            length = width + len(left) + len(right)
            symbol = elem.get("row_delimiter") or self.formatter.row_delim
            item = symbol * length
            line += item
        self.__row_spacer = line
        return line
    
    def stringify(self):
        if self.__row_template == None:
            self.gen_row_template_string()
        if self.__row_spacer == None:
            self.gen_row_spacer()
        output = self.__row_spacer
        header = [e["key"] for e in self.header]
        output += self.__row_template.format(*header)
        for i, line in enumerate(self.__lines):
            output += self.__row_spacer
            l = line.split(',')
            for j, col in enumerate(l):
                props = self._get_multiple_header_prop(j, ("auto_resize", "truncate", "width"))
                if props.get("auto_resize") is not True and props.get("truncate") is True:
                    l[j] = self._truncate(l[j], props['width'])
                elif props.get("auto_resize") is True and len(l[j]) > props['width']:
                    self._set_header_prop(j, "width", len(l[j]))
            if len(l) < len(self.header):
                l += [""] * (len(self.header) - len(l))
            output += self.__row_template.format(*l)
        return output

    def _get_header_prop(self, index, prop):
        if index > len(self._header) or index < 0:
            raise IndexError("Invalid index for get header props")
        prop = self._header[index].get(prop, self.formatter.get(prop))
        return prop
            
    def _set_header_prop(self, index, prop, value):
        if index > len(self._header) or index < 0:
            raise IndexError("Invalid index for set header props")
        if prop not in HEADER_PROPS:
            raise ValueError("Invalid header property '{}'.".format(prop))
        self._header[index][prop] = value
    
    def _get_multiple_header_prop(self, index, props):
        if index > len(self._header) or index < 0:
            raise IndexError("Invalid index for get header props")
        res = {}
        h = self._header[index]
        for p in props:
            val = h.get(p, self.formatter.get(p))
            if val is not None:
                res[p] = val
        return res
    
    def _truncate(self, word, length):
        if len(word) > length:
            word = word[0:length]
        return word

