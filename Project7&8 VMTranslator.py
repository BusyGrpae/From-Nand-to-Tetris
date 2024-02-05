# -*- coding: utf-8 -*-
"""
#VMTranslator
Translates VM commands into
the machine language of a target platform
##Usage:
% VMTtranslator input

Where input is either a single fileName.vm, or a folderName containing one or more .vm files;
##Output:
A single assembly file named input.asm

#Parser
Reads and parses a VM command

Handles the parsing of a single .vm file

* Reads a VM command, parses the command into its lexical components,
and provides convenient access to these components
* Skips white space and comments.
"""

class Parser:
  currentCmd=''

  #init:打开输入文件，去掉注释和空行,把所有VM cmd收集到一个集合里
  '''Arguments: input file/stream'''
  def __init__(self,inPath):
    self.__inPath=inPath
    commandList=[]
    with open(inPath,'r') as op:
      line=op.readline()
      while True:
        cleanLine=line.lstrip().rstrip()
        if not line:
          break
        elif line.isspace() or cleanLine.startswith('//'):
          line=op.readline()
        else:
          noComments=cleanLine.rsplit('//',1)
          commandList.append(noComments[0])
          line=op.readline()
    op.close()
    self.__commandList=commandList

  #判断集合里（commandList）里还有没处理的cmd么？
  '''Returns: boolean'''
  def hasMoreLines(self):
    commandList=self.__commandList
    if len(commandList)>0:
      boolean=True
    else:
      boolean=False
    return boolean

  #把下一个未处理的command取到currentCmd里并进一步拆分成元素
  '''应只在hasMoreLines返回True时被调用，一开始curentCmd里是空的
  将currentCmd拆成以单词为元素的集合components'''
  def advance(self):
    commandList=self.__commandList
    self.currentCmd=commandList.pop(0)
    self.__components=self.currentCmd.split()
    return

  #判断commandType
  '''Returns: C_ARITHMETIC, C_PUSH, C_POP, C_LABEL, C_GOTO, C_IF,
    C_FUNCTION, C_RETURN, C_CALL（constant）'''
  def commandType(self):
    components=self.__components
    if components[0] == 'push':
      result="C_PUSH"
    elif components[0] == 'pop':
      result="C_POP"
    elif components[0] == 'label':
      result="C_LABEL"
    elif components[0] == 'goto':
      result="C_GOTO"
    elif components[0] == 'if-goto':
      result="C_IF"
    elif components[0] == 'function':
      result="C_FUNCTION"
    elif components[0] == 'return':
      result="C_RETURN"
    elif components[0] == 'call':
      result="C_CALL"
    else:
      result="C_ARITHMETIC"
    return result

  #获取arg1（用于CodeWriter的argument）
  '''
  一般是currentCmd的第二个词，应该是字符串
  如果commandType是C_ARITHMETIC，那么是currentCmd本身/第一个词
  如果commandType是C_RETURN，不应该被调用
    Returns: string
    '''
  def arg1(self):
    components=self.__components
    if self.commandType()=='C_ARITHMETIC':
      result=components[0]
    else:
      result=components[1]
    return result

  #获取arg2（用于CodeWriter的argument）
  '''
  一般是currentCmd的最后一个元素，应该是数字
  应只在commandType是C_PUSH, C_POP, C_FUNCTION, C_CALL时被调用
    Returns: int
    '''
  def arg2(self):
    components=self.__components
    return components[2]

"""#CodeWriter
Generates the assembly code that realizes the parsed command
"""

class CodeWriter:
  __eqCont=0
  __gtCont=0
  __ltCont=0
  __fnCont=0
  fileName=''

  #init:新建输出文件，打开文件做好写入转译Code的准备
  '''Arguments output file/stream'''
  def __init__(self,outPath):
    #新建输出文件，如果已有同名文件则覆盖
    newFile=open(outPath,'w')
    newFile.close()
    opFile=open(outPath,'a')
    self.__opFile=opFile
    return

  #Boot Code
  '''如果输入的是一个包含多个vm文件的目录，
  应在输出文件开始写入bootstrap code的assembly code
  // Bootstrap code
  SP = 256
  call Sys.init // (no arguments)'''
  def writeBoot(self):
    #boot code 翻译成assembly code
    asmCodeList=['//Boottrap Code','//SP=256']
    asmCodeList+=['@256','D=A','@SP','M=D']
    asmCodeList+=['//call Sys.init']
    self.outputCode(asmCodeList)
    asmCodeList=self.writeCall('Sys.init',0)
    return

  #Inform that the translation of a new VM file has started
  #(called by the VMtranslator)
  def setFileName(self,filePath):
    name=filePath.rsplit('/',1)[1]
    noExt=name.rsplit('.')[0]
    self.fileName=noExt
    return

  def outputCode(self,asmCodeList):
    opFile=self.__opFile
    for code in asmCodeList:
      opFile.writelines(code+"\n")
    return

  def writeArithmetic(self,command):
    #arithmetic assmebly code
    Arithmetic={"add":["@SP","AM=M-1","D=M","@SP","AM=M-1","M=D+M","@SP","M=M+1"],
          "sub":["@SP","AM=M-1","D=M","@SP","AM=M-1","M=M-D","@SP","M=M+1"],
          "neg":["@SP","AM=M-1","M=-M","@SP","M=M+1"],
          "eq":["@SP","AM=M-1","D=M","@SP","AM=M-1","D=M-D",
            '@EQ.'+str(self.__eqCont)+'$TRUE',"D;JEQ","@SP","A=M","M=0",
            '@EQ.'+str(self.__eqCont)+'$END',"0;JMP",
            '(EQ.'+str(self.__eqCont)+'$TRUE)',"@SP","A=M","M=-1",
            '(EQ.'+str(self.__eqCont)+'$END)',"@SP","M=M+1"],
          "gt":["@SP","AM=M-1","D=M","@SP","AM=M-1","D=M-D",
            '@GT.'+str(self.__gtCont)+'$TRUE',"D;JGT","@SP","A=M","M=0",
            '@GT.'+str(self.__gtCont)+'$END',"0;JMP",
            '(GT.'+str(self.__gtCont)+'$TRUE)',"@SP","A=M","M=-1",
            '(GT.'+str(self.__gtCont)+'$END)',"@SP","M=M+1"],
          "lt":["@SP","AM=M-1","D=M","@SP","AM=M-1","D=M-D",
            '@LT.'+str(self.__ltCont)+'$TRUE',"D;JLT","@SP","A=M","M=0",
            '@LT.'+str(self.__ltCont)+'$END',"0;JMP",
            '(LT.'+str(self.__ltCont)+'$TRUE)',"@SP","A=M","M=-1",
            '(LT.'+str(self.__ltCont)+'$END)',"@SP","M=M+1"],
          "and":["@SP","AM=M-1","D=M","@SP","AM=M-1","M=D&M","@SP","M=M+1"],
          "or":["@SP","AM=M-1","D=M","@SP","AM=M-1","M=D|M","@SP","M=M+1"],
          "not":["@SP","AM=M-1","M=!M","@SP","M=M+1"]}
    #eq/gt/lt计数器+1
    if command=='eq':
      self.__eqCont+=1
    elif command=='gt':
      self.__gtCont+=1
    elif command=='lt':
      self.__ltCont+=1
    #从字典查出assembly code
    asmCodeList=Arithmetic[command]
    self.outputCode(asmCodeList)
    return

  def writePushPop(self,command,segment,index):
    className=self.fileName
    #Push/Pop assmebly code
    PushPop={"C_PUSH":{"local":["@LCL","D=M",'@'+index,"A=D+A","D=M",
                  "@SP","A=M","M=D","@SP","M=M+1"],
            "argument":["@ARG","D=M",'@'+index,"A=D+A","D=M",
                  "@SP","A=M","M=D","@SP","M=M+1"],
            "this":["@THIS","D=M",'@'+index,"A=D+A","D=M",
                  "@SP","A=M","M=D","@SP","M=M+1"],
            "that":["@THAT","D=M",'@'+index,"A=D+A","D=M",
                  "@SP","A=M","M=D","@SP","M=M+1"],
            "constant":['@'+index,"D=A",
                  "@SP","A=M","M=D","@SP","M=M+1"],
            "static":['@static$'+className+'.'+index,"D=M",
                  "@SP","A=M","M=D","@SP","M=M+1"],
            "pointer":{"0":["@THIS","D=M",
                    "@SP","A=M","M=D","@SP","M=M+1"],
                  "1":["@THAT","D=M",
                    "@SP","A=M","M=D","@SP","M=M+1"],},
            "temp":["@5","D=A",'@'+index,"A=D+A","D=M",
                  "@SP","A=M","M=D","@SP","M=M+1"],},
        "C_POP":{"local":["@LCL","D=M",'@'+index,"D=D+A","@R13","M=D",
                "@SP","AM=M-1","D=M","@R13","A=M","M=D"],
            "argument":["@ARG","D=M",'@'+index,"D=D+A","@R13","M=D",
                "@SP","AM=M-1","D=M","@R13","A=M","M=D"],
            "this":["@THIS","D=M",'@'+index,"D=D+A","@R13","M=D",
                "@SP","AM=M-1","D=M","@R13","A=M","M=D"],
            "that":["@THAT","D=M",'@'+index,"D=D+A","@R13","M=D",
                "@SP","AM=M-1","D=M","@R13","A=M","M=D"],
            "static":["@SP","AM=M-1","D=M",
                '@static$'+className+'.'+index,"M=D"],
            "pointer":{"0":["@SP","AM=M-1","D=M","@THIS","M=D"],
                  "1":["@SP","AM=M-1","D=M","@THAT","M=D"]},
            "temp":["@5","D=A",'@'+index,"D=D+A","@R13","M=D",
                "@SP","AM=M-1","D=M","@R13","A=M","M=D"],},}
    #从字典查出assembly code
    if segment=="pointer":
      asmCodeList=PushPop[command][segment][index]
      self.outputCode(asmCodeList)
    else:
      asmCodeList=PushPop[command][segment]
      self.outputCode(asmCodeList)
    return

  def writeLabel(self,label):
    asmCodeList=['('+label+')']
    self.outputCode(asmCodeList)
    return

  def writeGoto(self,label):
    asmCodeList=['@'+label,'0;JMP']
    self.outputCode(asmCodeList)
    return

  def writeIf(self,label):
    asmCodeList=['@SP','AM=M-1','D=M','@'+label,'D;JNE']
    self.outputCode(asmCodeList)
    return

  def writeFunction(self,functionName,nVars):
    #Label
    self.writeLabel(functionName)
    #Initialize local segement of the callee
    i=0
    n=int(nVars)
    while i<n:
      asmCodeList=['@SP','A=M','M=0','@SP','M=M+1']
      self.outputCode(asmCodeList)
      i+=1
    return

  def writeCall(self,functionName,nArgs):
    fnCont=self.__fnCont
    #push Label to retAddr
    retLabel=functionName+'$Ret.'+str(fnCont)
    self.__fnCont+=1
    asmCodeList=['@'+retLabel,'D=A','@SP','A=M','M=D','@SP','M=M+1']
    #push LCL/saves the caller's LCL
    asmCodeList+=['@LCL','D=M','@SP','A=M','M=D','@SP','M=M+1']
    #push ARG/saves the caller's ARG
    asmCodeList+=['@ARG','D=M','@SP','A=M','M=D','@SP','M=M+1']
    #push THIS/saves the caller's THIS
    asmCodeList+=['@THIS','D=M','@SP','A=M','M=D','@SP','M=M+1']
    #push THAT/saves the caller's THAT
    asmCodeList+=['@THAT','D=M','@SP','A=M','M=D','@SP','M=M+1']
    #Reposition ARG
    asmCodeList+=['@SP','D=M','@5','D=D-A','@'+str(nArgs),'D=D-A','@ARG','M=D']
    #Reposition LCL
    asmCodeList+=['@SP','D=M','@LCL','M=D']
    self.outputCode(asmCodeList)
    #Goto execute the callee's code
    self.writeGoto(functionName)
    #(retLabel)
    self.writeLabel(retLabel)
    return

  def writeReturn(self):
    #pop *LCL to endFrame
    asmCodeList=['@LCL','D=M','@R14','M=D']
    #retAddr=*(endFrame-5)
    asmCodeList+=['@R14','D=M','@5','D=D-A','A=D','D=M','@R15','M=D']
    #pop return value to *ARG
    asmCodeList+=['@SP','AM=M-1','D=M','@ARG','A=M','M=D']
    #reposition SP to ARG+1
    asmCodeList+=['@ARG','D=M+1','@SP','M=D']
    #restores THAT
    asmCodeList+=['@LCL','AM=M-1','D=M','@THAT','M=D']
    #restores THIS
    asmCodeList+=['@LCL','AM=M-1','D=M','@THIS','M=D']
    #restores ARG
    asmCodeList+=['@LCL','AM=M-1','D=M','@ARG','M=D']
    #restores LCL
    asmCodeList+=['@LCL','A=M-1','D=M','@LCL','M=D']
    #jumps to the retAddr
    asmCodeList+=['@R15','A=M','0;JMP']
    self.outputCode(asmCodeList)
    return

  def close(self):
    opFile=self.__opFile
    opFile.close()
    return

"""#Main
Constructs a CodeWriter

* If the input is a .vm file:

Constructs a Parser to handle the input file;
For each VM command in the input file:
uses the Parser to parse the command,
uses the CodeWriter to generate assembly code from it
* If the input is a folder:

Handles every .vm file in the folder in the manner described above.
"""

class Main:
  def __init__(self):
    import os
    #用户输入
    path=input('输入一个vm文件或包含vm文件的文件夹的路径')
    fileType='.vm'
    fileList=[]

    #如果输入的是一个文件
    if os.path.isfile(path):
      if path.endswith(fileType): #如果是vm文件，开始翻译
        outPath=path.split('.')[0]+'.asm'
        #新建一个CodeWriter
        cdwtr=CodeWriter(outPath)
        #开始单一文件的翻译过程
        self.translateFile(path,cdwtr)
        cdwtr.close()
      else: #不是vm文件，返回错误提示
        print('输入路径下不存在可供转译的.vm文件')

    #如果输入的是含一串vmfile的目录
    elif os.path.isdir(path):
      files=os.listdir(path)
      outPath=path+'/'+path.rsplit('/',1)[1]+'.asm'
      #新建一个CodeWriter
      cdwtr=CodeWriter(outPath)
      #找出文件夹里的vm文件，写入列表
      for f in files:
        if f.endswith(fileType):
          fpath=path+'/'+f
          fileList.append(fpath)
      if len(fileList)>0: #如果文件夹里有vm文件
        #如果vm文件与文件夹同名，按输入单一文件操作
        file=path+'/'+path.rsplit('/',1)[1]+fileType
        if file in fileList:
          self.translateFile(file,cdwtr)
        #不同名，把boot code写入输出文件的开头，再逐个翻译vm文件
        else:
          cdwtr.writeBoot()
          for file in fileList:
            self.translateFile(file,cdwtr)
          cdwtr.close()
      else: #如果文件夹里不包含vm文件，返回错误提示
        print('输入路径下不存在可供转译的.vm文件')
    return

  #单个文件处理过程
  '''Constructs a Parser to handle the input file;
  For each VM command in the input file: uses the Parser to parse the command,
  uses the CodeWriter to generate assembly code from it'''
  def translateFile(self,file,cdwtr):
    #用inputFile创建一个Parser
    parser=Parser(file)
    cdwtr.setFileName(file)
    #循环：把当前cmd翻译成asm code，写入文件，再取下一个cmd
    while parser.hasMoreLines():
      #取第一个VM Command
      parser.advance()
      #把vm command作为note写在asm code前
      asmNote=['//'+parser.currentCmd]
      cdwtr.outputCode(asmNote)
      #借助CodeWriter生成对应的assmbly code
      if parser.commandType()=='C_ARITHMETIC':
        command=parser.arg1()
        cdwtr.writeArithmetic(command)
      elif parser.commandType()in ('C_PUSH','C_POP'):
        command=parser.commandType()
        segment=parser.arg1()
        index=parser.arg2()
        cdwtr.writePushPop(command,segment,index)
      elif parser.commandType()=='C_LABEL':
        label=parser.arg1()
        cdwtr.writeLabel(label)
      elif parser.commandType()=='C_GOTO':
        label=parser.arg1()
        cdwtr.writeGoto(label)
      elif parser.commandType()=='C_IF':
        label=parser.arg1()
        cdwtr.writeIf(label)
      elif parser.commandType()=='C_FUNCTION':
        functionName=parser.arg1()
        nVars=parser.arg2()
        cdwtr.writeFunction(functionName,nVars)
      elif parser.commandType()=='C_CALL':
        functionName=parser.arg1()
        nArgs=parser.arg2()
        cdwtr.writeCall(functionName,nArgs)
      elif parser.commandType()=='C_RETURN':
        cdwtr.writeReturn()
    return

#程序引导
if __name__ == "__main__":
  Main()
