#! /usr/bin/python
#@author Joe Gibson

import re
import sys
import getopt
import operator

'''
Converts assembly instructions to maching code for a microcontroller implemented in VHDL on a Xilinx Artix-7 FPGA
Python Version: 2.7.6
'''

#|Instruction 	| Encoding          |
#|--------------|:-----------------:|
#|LOAD M,R 	 	|000000pr, mmmmmmmm |
#|STOR R,M 	 	|000001pr, mmmmmmmm |
#|ADD R 		|1000000r           |
#|SUB R 		|1001000r           |
#|LSL R 		|1010000r           |
#|LSR R 		|1011000r           |
#|XOR R 		|1100000r           |
#|COM R 		|1101000r           |
#|NEG R 		|1110000r           |
#|CLR R 		|1111000r           |
#|OUT R,P 	 	|000100ir           |
#|IN P,R 	 	|000101ir           |
#|BCDO R      	|1111100r           |
#|DEB P,R       |000110ir           |
#|BNZ M       	|000010p0, mmmmmmmm |
#|CALL M        |010000p0, mmmmmmmm |
#|RET R, K      |0110000r, kkkkkkkk |

class Assembler:
    def __init__(self, ifp, cfp):
        self.instruction_map = {
            'LOAD'  : ('000000pr', ['P', 'R', 'M']),
            'STOR'  : ('000001pr', ['P', 'R', 'M']),
            'ADD'   : ('1000000r', ['R']),
            'SUB'   : ('1001000r', ['R']),
            'LSL'   : ('1010000r', ['R']),
            'LSR'   : ('1011000r', ['R']),
            'XOR'   : ('1100000r', ['R']),
            'COM'   : ('1101000r', ['R']),
            'NEG'   : ('1110000r', ['R']),
            'CLR'   : ('1111000r', ['R']),
            'OUT'   : ('000100ir', ['I', 'R']),
            'IN'    : ('000101ir', ['I', 'R']),
            'BCDO'  : ('1111100r', ['R']),
            'BNZ'   : ('000010p0', ['P', 'M']),
            'CALL'  : ('010000p0', ['P', 'M']),
            'RET'   : ('0110000r', ['R', 'K'])
        }

        self.instructionFilepath = ifp
        self.coeFilepath = cfp
        self.coe = []
        self.data = []
        self.instruction = []
        self.sections = []

        #Initialize the COE list with the correct headers
        self.coe.append('memory_initialization_radix = 2;')
        self.coe.append('memory_initialization_vector =')

    ###Data section
    # ...
    # DATA
    #   [10] = 0x05 <-- Sets memory location 10 to the value 0x05
    #   ...
    # END DATA
    #
    def ParseData(self):
        #Open file
        self.instructionFile = open(self.instructionFilepath, 'r')

        #Data section flag
        dataSectionFlag = False

        #Parse data section
        for line in self.instructionFile:
            #Strip leading/trailing whitespace
            line.strip()

            #Check for beginning/end of data section
            if line == 'DATA':
                dataSectionFlag = True
            elif line == 'END DATA':
                dataSectionFlag = False

            #Parse data section tokens
            if dataSectionFlag == True:
                tokens = line.split('=')

                #Strip whitespace from tokens
                for token in tokens:
                    token.strip()

                #Format: [<MEM LOCATION>] = <VALUE>
                location = tokens[0].translate(None, '[]')
                value = int(tokens[1], 16)
                self.data.append((location, value))

        #Close file
        self.instructionFile.close()

    ###Section section
    # ...
    # SECTIONS
    #   <NAME> = 100 <-- Begin section '<NAME>' at location '100'
    #   ...
    # END SECTIONS
    # ...
    def ParseSections(self):
        #Open file
        self.instructionFile = open(self.instructionFilepath, 'r')

        #Section flag
        sectionFlag = False

        #Parse data section
        for line in self.instructionFile:
            #Strip leading/trailing whitespace
            line.strip()

            #Check for beginning/end of data section
            if line == 'SECTIONS':
                sectionFlag = True
            elif line == 'END SECTIONS':
                sectionFlag = False

            #Parse data section tokens
            if sectionFlag == True:
                tokens = line.split('=')

                #Strip whitespace from tokens
                for token in tokens:
                    token.strip()

                #Format: [<MEM LOCATION>] = <VALUE>
                section = tokens[0]
                startAddress = int(tokens[1], 10)
                self.sections.append((section, startAddress))

        #Close file
        self.instructionFile.close()

    ###Instruction section:
    # ...
    # <SECTION_NAME>:
    #   <INSTR 1>
    #   ...
    # <SECTION_NAME>:
    #   <INSTR N>
    #   ...
    # ...
    def ParseInstructions(self):
        #Open file
        self.instructionFile = open(self.instructionFilepath, 'r')

        #Section flag
        beginSectionFlag = False

        #Sort the sections by their starting address
        self.sections.sort(key=lambda x: x[1])

        #Keep track of the line count to be able to ensure sections begin at the right line
        lineCount = 0

        #Parse instructions
        for line in self.instructionFile:
            #Strip leading/trailing whitespace and remove colons
            line.strip()
            line.translate(None, ':')

            #Check for beginning/end of instruction section
            for s[0] in self.sections:
                if line == s[0]:
                    beginSectionFlag = True
                    startAddress = s[1]
                    break
                else:
                    beginSectionFlag = False

            #Create NULL instructions until the expected section is to begin
            if beginSectionFlag == True:
                while lineCount < startAddress:
                    self.coe.append('11110000')

            #Write instructions
            else:
                values = line.split(' ')
                instruction = values[0]
                parameters = values[1:]

                #Add legitimate instructions to COE
                if instruction in self.instruction_map.keys():
                    self.coe.append(self.instruction_map[instruction])

        #Close file
        self.instructionFile.close()

    def WriteCOE(self):
        #Write the coe list to the coe file
        self.coeFile = open(self.coeFilepath, 'w')

        for line in self.coe:
            self.coeFile.write(line + '\n')

        self.coeFile.close()


def main(argc, argv):
    if argc < 2:
        print '@usage: ./ArtixAssember <instruction file> <coe file>'
        return

    instructionFile = argv[0]
    coeFile = argv[1]

    print 'Instruction file: ' + instructionFile
    print 'COE file: ' + coeFile

    assembler = Assembler(instructionFile, coeFile)

    assembler.ParseData()
    assembler.ParseSections()
    assembler.ParseInstructions()
    assembler.WriteCOE()

if __name__ == '__main__':
	main(len(sys.argv[1:]), sys.argv[1:])
