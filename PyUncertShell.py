import sys
import os
import shutil
import math
import UncertDefn
import CalcDist
import subprocess
import random 
import datetime

VersionStr = "1.02 beta"

class EUncertShellError(Exception):
    pass

class TUncertMain:
    def __init__(self):
        self.NumDists = 0
        self.NumOutputs = 0
        self.DistArray = []
        self.OutArray = []
        self.Seed = 20
        self.Iterations = 20
        self.UseSeed = True
        self.ModelPath = ''
        self.ModelParameter = ''
        self.ShellPath = ''
        self.OutPath = ''
        self.Changed = False
        self.UResults = [[] for _ in range(5)]
        self.DetRes, self.MinRes, self.MaxRes, self.StdRes, self.MeanRes = range(5)
        self.UserInterrupt = None
        self.IterationsDone = 0

    def NewShell(self):
        self.NumDists = 0
        self.NumOutputs = 0
        self.Seed = 20
        self.Iterations = 20
        self.UseSeed = True
        self.ModelPath = ''
        self.ShellPath = ''

    def SaveShell(self):
        with open(self.ShellPath, 'w') as out_text:
            out_text.write(f"Version, {VersionStr}\n")
            out_text.write(f"Seed, {self.Seed}\n")
            out_text.write(f"Iterations, {self.Iterations}\n")
            out_text.write(f"UseSeed, {int(self.UseSeed)}\n")
            out_text.write(f"ModelPath, {self.ModelPath}\n")
            out_text.write(f"ModelParameter, {self.ModelPath}\n")
            out_text.write(f"NumDists, {self.NumDists}\n")

            for dist in self.DistArray:
                dist.WriteText(out_text)

            out_text.write(f"NumOutputs, {self.NumOutputs}\n")

            for output_var in self.OutArray:
                output_var.WriteText(out_text)

    def str_to_bool(self, s):
        s = s.lower()
        if s == "true":
            return True
        elif s == "false":
            return False
        else:
            raise ValueError("Input is not 'True' or 'False'")

    def LoadShell(self):
        if os.path.splitext(self.ShellPath)[1].upper() != '.USH':
            with open(self.ShellPath, 'r') as in_text:
                version_str = in_text.readline().strip().split(', ')[1]
                self.Seed = int(in_text.readline().strip().split(', ')[1])
                self.Iterations = int(in_text.readline().strip().split(', ')[1])
                self.UseSeed = self.str_to_bool(in_text.readline().strip().split(', ')[1])
                self.ModelPath = in_text.readline().strip().split(', ')[1]
                self.ModelParameter = in_text.readline().strip().split(', ')[1]
                self.NumDists = int(in_text.readline().strip().split(', ')[1])

                for _ in range(self.NumDists):
                    dist = UncertDefn.TInputDist.ReadFromFile(in_text)
                    self.DistArray.append(dist)

                self.NumOutputs = int(in_text.readline().strip().split(', ')[1])

                for _ in range(self.NumOutputs):
                    output_var = UncertDefn.TOutputVar(in_text)
                    self.OutArray.append(output_var)
        else:
            with open(self.ShellPath, 'rb') as file_stream:
                version_check = file_stream.read(10).decode('utf-8').strip()
                version_str = VersionStr
                self.Seed = int.from_bytes(file_stream.read(4), byteorder='little')
                self.Iterations = int.from_bytes(file_stream.read(4), byteorder='little')
                self.UseSeed = bool(int.from_bytes(file_stream.read(4), byteorder='little'))
                self.ModelPath = file_stream.read(256).decode('utf-8').strip()

                if self.ModelPath != '' and not os.path.exists(self.ModelPath):
                    raise FileNotFoundError(f"File Not Found: {self.ModelPath}")

                self.NumDists = int.from_bytes(file_stream.read(4), byteorder='little')

                for _ in range(self.NumDists):
                    dist = UncertDefn.TInputDist.Load(file_stream)
                    self.DistArray.append(dist)

                self.NumOutputs = int.from_bytes(file_stream.read(4), byteorder='little')

                for _ in range(self.NumOutputs):
                    output_var = UncertDefn.TOutputVar.Load(file_stream)
                    self.OutArray.append(output_var)

    def ExecuteModel(self):
        result = subprocess.run(self.ModelPath + " " +self.ModelParameter, shell=True, check=True)
        return (result.returncode == 0);

    def Accumulate_Uncertainty_Results(self):

        if self.IterationsDone == 0:
            for Loop in range(self.NumOutputs):
                self.AllData.write(self.OutArray[Loop].Name.replace(',', '')+', ')  #write to alldata.txt
            self.AllData.write("\n")
            self.InitArrays()
        else:
            for Loop in range(self.NumOutputs):
                for Res in range(self.MinRes, self.MeanRes + 1):
                    OVal = self.OutArray[Loop].GetValue()
                    UVal = self.UResults[Res][Loop]
                    if Res == self.MinRes: self.AllData.write(f"{OVal:.2f}, ")  #write to alldata.txt
                    if Res == self.MeanRes:
                        self.UResults[Res][Loop]=OVal+UVal  #Sum for now
                    if Res == self.MinRes:
                        if OVal<UVal: self.UResults[Res][Loop]=OVal
                    if Res == self.MaxRes:
                        if OVal>UVal: self.UResults[Res][Loop]=OVal
                    if Res == self.StdRes:
                        self.UResults[Res][Loop] += OVal ** 2
                        
            self.AllData.write("\n")
            
        self.IterationsDone += 1

        # Update Text output
        it_str = f'Iteration {self.IterationsDone} Completed.'
        self.TextOut.write(it_str+"\n")
        self.TextOut.write('---------------------------------------------------------'+"\n")

    def InitTextResults(self):

        res_out_file = os.path.splitext(self.OutPath)[0] + '_summary.txt'
        text_out_file = os.path.splitext(self.OutPath)[0] + '_uncertlog.txt'
        all_data_file = os.path.splitext(self.OutPath)[0] + '_alldata.txt'

        while '\\' in res_out_file:
            res_out_file = res_out_file.replace('\\', '')

        while '\\' in text_out_file:
            text_out_file = text_out_file.replace('\\', '')

        self.AllData = open(all_data_file, 'w')
        self.ResOut = open(res_out_file, 'w')
        self.TextOut = open(text_out_file, 'w')
        self.TextOut.write('---------------------------------------------------------\n')
        self.TextOut.write('\n')
        self.TextOut.write(f'        Uncertainty Run for Model "{os.path.basename(self.ModelPath)}"\n')
        self.TextOut.write('\n')
        self.TextOut.write('---------------------------------------------------------\n')
        DateHolder = f'Run Starts at {datetime.datetime.now():%m-%d-%y %I:%M%p}'
        self.TextOut.write(f'        {DateHolder}\n')
        self.TextOut.write('---------------------------------------------------------\n')
        self.TextOut.write('\n')
        self.TextOut.write('        ** DISTRIBUTIONS SUMMARY **\n')
        self.TextOut.write('\n')

    def SummarizeDist(self):
        parm_info = {
            'Normal': ['Mean', 'Std. Deviation', '', ''],
            'Triangular': ['Most Likely', 'Minimum', 'Maximum', ''],
            'LogNormal': ['Mean', 'Std. Deviation', '', ''],
            'Uniform': ['Minimum', 'Maximum', '', '']
        }

        parm_values = [f'{parm:.4f}' for parm in self.Dist.Parm]

        self.TextOut.write(f'{self.Dist.Name}:   Point Estimate: {self.Dist.PointEstimate:.4f}\n')
        self.TextOut.write(f'  {self.Dist.DistType} : ')

        for i in range(4):
            if parm_info[self.Dist.DistType][i] != '':
                self.TextOut.write(f'{parm_info[self.Dist.DistType][i]}={parm_values[i]}; ')

        self.TextOut.write('\n\n')

    def InitArrays(self):
                
        for loop in range(self.NumOutputs):
            for res in range(self.MinRes, self.MeanRes + 1):
                OVal = self.OutArray[loop].GetValue();
                if res == self.MinRes: self.AllData.write(f"{OVal:.2f}, ")
                if (loop==0): self.UResults[res] = [0.0] * self.NumOutputs
                if res == self.StdRes: self.UResults[res][loop] = OVal * OVal
                else: self.UResults[res][loop] = OVal 
        self.AllData.write("\n")


    def PostProcessResults(self):

        for i in range(self.NumOutputs):
            Sum = self.UResults[self.MeanRes][i]
            SumSquare = self.UResults[self.StdRes][i]
            n = self.IterationsDone

            if n > 0:
                self.UResults[self.MeanRes][i] = Sum / n

            # Calculate standard deviation using the "nonbiased" or "n-1" method
            if n > 1:
                InSqrt = ((n * SumSquare) - (Sum * Sum)) / (n * (n - 1))
            else:
                InSqrt = 0

            if InSqrt > 0:
                self.UResults[self.StdRes][i] = math.sqrt(InSqrt)
            else:
                self.UResults[self.StdRes][i] = 0

    def WriteResultsToTxt(self):

        if self.IterationsDone > 0:
            self.PostProcessResults()

        self.ResOut.write('Variable Name, Min, Mean, Max, Std. Dev.\n')

        for i in range(self.NumOutputs):
            self.ResOut.write(f'{self.OutArray[i].Name}, {self.UResults[self.MinRes][i]:.4f}, {self.UResults[self.MeanRes][i]:.4f}, '
                         f'{self.UResults[self.MaxRes][i]:.4f}, {self.UResults[self.StdRes][i]:.4f}\n')
        
    class EUncertShellError(Exception):
        def __init__(self, message):
            self.message = message

    def CopyFile(src, dst, replace=False):
        if os.path.exists(dst):
            if replace:
                os.remove(dst)
            else:
                return
        shutil.copy(src, dst)

    def SetSeed(self, seed):
        if seed == -1:
            random.seed()
        else:
            random.seed(seed)

    def RandomInt(top):
        return random.randint(1, top)

    def ICDF(self, prob):
        res = None

        if self.Dist.DistType == 'Normal':
            res = CalcDist.icdfNormal(prob, self.Dist.Parm[0], self.Dist.Parm[1])
        elif self.Dist.DistType == 'Triangular':
            res = CalcDist.icdfTriangular(prob, self.Dist.Parm[2], self.Dist.Parm[3], self.Dist.Parm[1])
        elif self.Dist.DistType == 'LogNormal':
            res = CalcDist.icdfLogNormal(prob, math.exp(self.Dist.Parm[0]), math.exp(self.Dist.Parm[1]))
        elif self.Dist.DistType == 'Uniform':
            res = CalcDist.icdfUniform(prob, self.Dist.Parm[0], self.Dist.Parm[1])
        elif self.Dist.DistType == 'USER':
            res = CalcDist.UserDist.ICDF(prob)

        if res is None:
            raise Exception('Distribution Error! ICDF Called with Invalid Parameters.')

        return res

    def CDF(self, x_val):
        res = None

        if self.Dist.DistType == 'Triangular':
            res = CalcDist.cdfTriangular(x_val, self.Dist.Parm[2], self.Dist.Parm[3], self.Dist.Parm[1])
        elif self.Dist.DistType == 'Normal':
            res = CalcDist.cdfNormal(x_val, self.Dist.Parm[0], self.Dist.Parm[1])
        elif self.Dist.DistType == 'LogNormal':
            res = CalcDist.cdfLogNormal(x_val, math.exp(self.Dist.Parm[0]), math.exp(self.Dist.Parm[1]))
        elif self.Dist.DistType == 'Uniform':
            res = CalcDist.cdfUniform(x_val, self.Dist.Parm[0], self.Dist.Parm[1])
        elif self.CalcDist.DistType == 'USER':
            res = self.UserDist.CDF(x_val)

        if res is None:
            raise Exception('Distribution Error! CDF Called with Invalid Parameters.')

        return res

    def CalculateDraw(self, interval):
        prob_low = 0.0
        prob_high = 1.0

        if self.Dist.DistType in ['Normal', 'LogNormal']:
            prob_low = self.CDF(0)

        width = (prob_high - prob_low) / self.Iterations
        where = (width * interval) + prob_low
        rand_prob = where - width * random.uniform(0, 1)

        return self.ICDF(rand_prob)

    def FillVariableDraws(self, indx):
        self.Dist.Draws = []

        for iteration_loop in range(1, self.Iterations + 1):
            if indx > 27:
                random_draw = iteration_loop / self.Iterations
            else:
                random_draw = random.uniform(0, 1)

            draw = UncertDefn.TUncertDraw(random_draw, 0, iteration_loop)
            self.Dist.Draws.append(draw)

        user_dist = None
        if self.Dist.DistType == 'USER':
            user_dist = UncertDefn.TUserDist.LoadFromFile(self.Dist.UserFileN)

        for iteration_loop in range(1, self.Iterations + 1):
            low_value = 99
            low_val_index = 0

            for find_slot_loop in range(self.Iterations):
                if self.Dist.Draws[find_slot_loop].RandomDraw <= low_value:
                    low_val_index = find_slot_loop
                    low_value = self.Dist.Draws[find_slot_loop].RandomDraw

            new_draw = self.Dist.Draws[low_val_index]
            new_draw.RandomDraw = 99
            new_draw.IntervalNum = iteration_loop
            new_draw.Value = self.CalculateDraw(iteration_loop)

        if user_dist:
            user_dist.Free()


    def LatinHypercubeRun(self):
        
        Loop = Loop2 = Prog = 0
        OVal = 0.0
        ItStr = ""
        IsBacked = False
        N1 = [''] * 301
        N2 = [''] * 301

        # Initialization
        self.IterationsDone = 0
        self.UserInterrupt = False

        # try:
        # Initialize text results
        self.InitTextResults()

        # Set seed if required
        if self.UseSeed:
            self.SetSeed(self.Seed)
        else:
            self.SetSeed(-1)

        print('Deterministic Run...')

        # Execute model
        if not self.ExecuteModel():
            print('Model Execution Error.')
            exit()     

        # Initialize UResults
        self.UResults[self.DetRes] = [0.0] * self.NumOutputs

        for Loop in range(self.NumOutputs):
            OVal = self.OutArray[Loop].GetValue()
            self.UResults[self.DetRes][Loop] = OVal

        self.FileBacked = []

        # Copy input files to backup
        for Loop in range(self.NumDists):
            IsBacked = False

            for Loop2 in range(len(self.FileBacked) if self.FileBacked else 0):
                if self.FileBacked[Loop2] == self.DistArray[Loop].InputFile:
                    IsBacked = True

            if not IsBacked:
                N1 = self.DistArray[Loop].InputFile
                N2 = os.path.splitext(self.DistArray[Loop].InputFile)[0] + '.backup'
                shutil.copyfile(N1, N2)
                self.FileBacked.append(self.DistArray[Loop].InputFile)

        # Fill VariableDraws and save point estimates
        for Loop in range(self.NumDists):
            self.Dist = self.DistArray[Loop]
            self.FillVariableDraws(Loop)
            self.SummarizeDist()

        print('---------------------------------------------------------')

        for NSLoop in range(1, self.Iterations + 1):
            # Update Progress Dialog
            ItStr = f'Iteration {NSLoop} of {self.Iterations}'
            print(ItStr)
            self.TextOut.write(ItStr+"\n")
            self.TextOut.write("\n")

            # Load the Latin Hypercube values into the simulation
            for DLoop in range(self.NumDists):
                self.Dist = self.DistArray[DLoop]
                DrawValue = self.Dist.Draws[NSLoop - 1].Value
                self.Dist.set_value(DrawValue)
                self.TextOut.write(f'{self.Dist.Name} {DrawValue:.5f}'+"\n")

            self.UserInterrupt = False
            # Execute the model for each iteration
            if not self.ExecuteModel():  
                self.UserInterrupt = True
                DateHolder = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
                self.TextOut.write(f'Execute Model Error at {DateHolder}')
                print('Model Execution Error.')
                break

            print(f'Completed Uncertainty Run- {NSLoop} of {self.Iterations}')

            if self.UserInterrupt:
                DateHolder = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
                print(f'Run Terminated at {DateHolder}')
                break
            else:
                self.Accumulate_Uncertainty_Results()
                    
            if not self.UserInterrupt:
                DateHolder = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S')
                self.TextOut.write(f'Run Successfully Completed At {DateHolder}'+"\n")
                self.TextOut.write('---------------------------------------------------------'+"\n")

        # except Exception as e:
        #     ErrorString = str(e)
        #     self.TextOut.write('Run-Time Error During Uncertainty Iteration'+"\n"+e+'n"' )
        #     print ('Run-Time Error During Uncertainty Iteration');
        #     DateHolder = datetime.datetime.now().strftime('%m-%d-%Y %H:%M:%S'+"\n")

        #     try:
        #         self.TextOut.write(f'Run Terminated at {DateHolder}'+"\n")
        #         self.TextOut.write(f'    Due to {ErrorString}'+"\n")
        #     except:
        #         self.TextOut.write('No Data Written'+"\n")

        self.TextOut.close();

        try:
            if self.IterationsDone > 0:
                self.WriteResultsToTxt()

        except Exception as e:
            self.ResOut.close()
            ErrorString = str(e)

        self.ResOut.close()
        self.AllData.close()

        # Restore Input File(s) from Backup(s)
        for Loop in range(len(self.FileBacked) if self.FileBacked else 0):
            N1 = self.DistArray[Loop].InputFile
            N2 = os.path.splitext(self.DistArray[Loop].InputFile)[0] + '.backup'
            shutil.copyfile(N2, N1)
        

#try:
if len(sys.argv) < 2:
    print('You must enter the uncertshell input text file as a parameter')
else:
    UM = TUncertMain()
    UM.ShellPath = sys.argv[1]
    UM.OutPath = sys.argv[1]
    UM.LoadShell()
    UM.LatinHypercubeRun()
    print('Run Completed')

#except Exception as e:
    #print(f'{e.__class__.__name__}: {e}')
