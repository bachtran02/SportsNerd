
# inp stands for input as input is a function already
class InputParser:
    def __init__(self, inp):
        self.checkEmpty(inp)
        self.inp = inp

    @staticmethod
    def checkEmpty(inp):
        if not inp:
            raise Exception("Input missing!")

    def parseTeamDate(self):
        li = self.inp.split()
        if li[-1].isdigit():
            date = li.pop(-1)
        else:
            return [self.inp, ""]
        team = " ".join(li)
        return [team, date]


