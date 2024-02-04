import math
import os

class EUncertShellError(Exception):
    pass

def read_parameter(tf, p_name):
    str = next(tf)
    cl = str.find(p_name)
    pl = len(p_name) + 2
    if cl == -1:
        raise ValueError(f'Read Error, expecting parameter {p_name} on line: {str}')
    str = str[pl:]
    return str.strip()

def read_double_parameter(tf, p_name):
    return float(read_parameter(tf, p_name))

def read_int_parameter(tf, p_name):
    return int(read_parameter(tf, p_name))

def read_bool_parameter(tf, p_name):
    param_value = read_parameter(tf, p_name).upper()
    return param_value == 'TRUE'

class TUserDist:
    def __init__(self):
        self.num = 0
        self.arr = []

    def load_from_file(self, file_name):
        with open(file_name, 'r') as file:
            for line in file:
                val = float(line.strip())
                self.arr.append(val)
                self.num += 1

        self.arr.sort()

    def cdf(self, x):
        error_value = -99.9
        if x < self.arr[0] or x > self.arr[self.num - 1]:
            return error_value

        index = 0
        while self.arr[index] < x:
            index += 1

        return (index / self.num) + (0.5 / self.num)

    def icdf(self, prob):
        return self.arr[int(prob * self.num)]

class TInputDist:
    def __init__(self, pe, lif, sc, nc, fn):
        self.Name = ""
        self.InputFile = fn
        self.LineInFile = lif
        self.StartChar = sc
        self.NumChars = nc
        self.DistType = "Normal"
        self.Parm = [abs(pe), abs(pe) * 0.4, 1.3 * abs(pe), 0]
        self.DisplayCDF = False
        self.PointEstimate = pe
        self.Draws = None
        self.UserFileN = ""

    @classmethod
    def ReadFromFile(cls, in_text):
        instance = cls(0,0,0,0,0)
        instance.Name = read_parameter(in_text, 'InputDistName')
        instance.InputFile = read_parameter(in_text, 'InputFile')
        if not os.path.exists(instance.InputFile):
            raise ValueError(f'File Not Found: {instance.InputFile}')

        instance.LineInFile = read_int_parameter(in_text, 'LineInFile')
        instance.StartChar = read_int_parameter(in_text, 'StartChar')
        instance.NumChars = read_int_parameter(in_text, 'NumChars')

        instance.DistType = read_parameter(in_text, 'DistType')

        instance.Parm = [0.0] * 4
        for i in range(1, 5):
            instance.Parm[i - 1] = read_double_parameter(in_text, f'Parm{i}')

        instance.DisplayCDF = read_bool_parameter(in_text, 'DisplayCDF')
        instance.PointEstimate = read_double_parameter(in_text, 'PointEstimate')

        instance.UserFileN = ''
        return instance

    def get_value(self):
        with open(self.InputFile, 'r') as file:
            for _ in range(self.LineInFile):
                file.readline()

            for _ in range(self.StartChar - 1):
                file.read(1)

            val_str = file.read(self.NumChars).strip()

        try:
            value = float(val_str)
            self.PointEstimate = value
        except ValueError:
            value = -999
            self.PointEstimate = value

        return value

    def set_value(self, val):
        with open(self.InputFile, 'r') as file:
            lines = file.readlines()

        with open(self.InputFile, 'w') as file:
            for i, line in enumerate(lines):
                if i == self.LineInFile:
                    line = line[:self.StartChar - 1] + "{:>{}}".format(val, self.NumChars) + line[self.StartChar - 1 + self.NumChars:]
                file.write(line)
                


class TOutputVar:
    def __init__(self, name, out_f, lif, nol, sc, nc, dlm, dc):
        self.Name = name
        self.OutputFile = out_f
        self.LineInFile = lif
        self.NumOnLine = nol
        self.StartChar = sc
        self.NumChars = nc
        self.Delimited = dlm
        self.DelimChar = dc

    def __init__(self, in_text):
        self.Name = read_parameter(in_text, 'OutputVarName')
        self.OutputFile = read_parameter(in_text, 'OutputFile')
        self.LineInFile = read_int_parameter(in_text, 'LineInFile')
        self.NumOnLine = read_int_parameter(in_text, 'NumOnLine')
        self.StartChar = read_int_parameter(in_text, 'StartChar')
        self.NumChars = read_int_parameter(in_text, 'NumChars')
        self.Delimited = read_bool_parameter(in_text, 'Delimited')
        delim_str = read_parameter(in_text, 'DelimChar')
        self.DelimChar = delim_str[0] if delim_str else ''

    def GetValue(self):
        with open(self.OutputFile, 'r') as file:
            for _ in range(self.LineInFile):
                file.readline()

            if self.Delimited:
                for _ in range(1, self.NumOnLine):
                    while file.read(1) != self.DelimChar:
                        pass

                val_str = ""
                while True:
                    char = file.read(1)
                    if char == self.DelimChar:
                        break
                    val_str += char
            else:
                for _ in range(self.StartChar - 1):
                    file.read(1)

                val_str = file.read(self.NumChars).strip()

        return float(val_str)
    
def read_parameter(file, p_name):
    for line in file:
        if p_name in line:
            return line.split(",",1)[1].strip()
    raise ValueError(f"Read Error, expecting parameter {p_name}")

def read_double_parameter(file, p_name):
    return float(read_parameter(file, p_name))

def read_int_parameter(file, p_name):
    return int(read_parameter(file, p_name))

def read_bool_parameter(file, p_name):
    value = read_parameter(file, p_name).upper()
    return value == 'TRUE'

def fix_float_to_str(f, l):
    formatted_str = "{:.{precision}f}".format(f, precision=l - 2)
    if "." not in formatted_str:
        formatted_str += "."
    if len(formatted_str) >= l:
        formatted_str = "{:.{precision}e}".format(f, precision=l - 5)
    if "." not in formatted_str:
        formatted_str += "."
    if len(formatted_str) >= l:
        formatted_str = "{:.{precision}e}".format(f, precision=l - 6)
    if len(formatted_str) >= l:
        raise ValueError("Error, FixFloat too Large")
    formatted_str = formatted_str.rjust(l)
    return formatted_str

def abbr_string(in_str, delim_char):
    out_str = ""
    for char in in_str:
        if char == delim_char:
            break
        out_str += char
    return out_str


class TUncertDraw:
    def __init__(self, Val, Rd, Int):
        self.Value = Val
        self.IntervalNum = Int
        self.RandomDraw = Rd