import numpy as np
import scipy.interpolate as spi
import os
import pandas as pd


class FunctionInterpolationApproximator(object):

    def __init__(self, racines, extrema, domaine,step = 0.05):
        if [0,0] in extrema:
            if 0 in racines:
                racines.remove(0)
        self.domaine = np.arange(domaine[0], domaine[1]+step, step)
        self.racines = racines
        self.extrema = extrema

    def racinesPentes(self):
        res = []
        s_e = sorted(self.extrema, key=lambda x: x[0])
        for r in sorted(self.racines):
            for i in range(len(self.extrema) - 1):
                if s_e[i + 1][0] > r:
                    pente = (s_e[i + 1][1] - s_e[i][1]) / (s_e[i + 1][0] - s_e[i][0])
                    left = float(r - s_e[i][0])
                    right = float(s_e[i + 1][0] - r)
                    if left == 0 or right == 0:
                        factor = 0
                    elif left > right:
                        factor = left / right
                    else:
                        factor = right / left
                    res.append(factor * pente)
                    break

        return res

    def derivesPentes(self):
        rs = list(zip(sorted(self.racines), self.racinesPentes())) + list(
            zip([e[0] for e in self.extrema], np.zeros(len(self.extrema))))
        return np.array(sorted(rs, key=lambda x: x[0]))[:, 1]

    def approximate(self):
        x_y_s = list(zip(self.racines, np.zeros(len(self.racines)))) + self.extrema
        x_y_s = np.array(sorted(x_y_s, key=lambda x: x[0]))
        xs = x_y_s[:, 0]
        ys = x_y_s[:, 1]
        dp = self.derivesPentes()
        self.spline = spi.CubicHermiteSpline(xs, ys, dp)

    @property
    def xs(self):
        return self.domaine

    @property
    def ys(self):
        return list(map(lambda x:self.spline(x),self.domaine))

    @property
    def min_x(self):
        return self.domaine[0]

    @property
    def max_x(self):
        return self.domaine[-1]

    @property
    def min_y(self):
        return min(self.ys)

    @property
    def max_y(self):
        return max(self.ys)

    def printPoints(self, separator=""):
        return separator.join(["({},{})".format(np.around(x, 3),np.around(self.spline(x), 3)) for x in self.domaine])

    def axisText(self):
        return "\\addplot[smooth,blue,samples=100] coordinates{" + self.printPoints() + "};"

    def geogebraText(self):
        pts = ",".join([str(np.around(self.spline(x), 3)) for x in self.domaine])
        return "Function[{" + str(np.around(self.domaine[0],3)) + "," + str(np.around(self.domaine[-1],3)) + "," + pts + "}]"

    def generateTikzPicture(self):
        with open("picture.tex","w") as texfile:
            texfile.write(
                """
                \\documentclass{standalone}\n
                \\usepackage{tikz}\n
                \\usepackage{pgfplots}\n
                
                \\pgfplotsset{
                    standardaxis2/.style={
                        enlarge x limits=0.15,
                        enlarge y limits=0.15,
                        %every axis x label/.style={at={(current axis.right of origin)},anchor=north west},
                        every axis y label/.style={at={(current axis.above origin)},anchor=north east},
                        axis lines=middle,
                        axis line style={-stealth,very thick},
                        xmin=-10.5,xmax=10.5,ymin=-10.5,ymax=10.5,
                        xtick distance=1,
                        ytick distance=1,
                        extra x ticks={0},
                        extra x tick style={grid=major, grid style={black},xticklabel style={inner sep=4pt,anchor=north east},xtick style={black}},
                        xticklabel style={font=\\large, anchor = north, inner sep = 4pt},
                        yticklabel style={font=\\large, anchor = east, inner sep = 4pt},
                        xlabel=$x$,
                        ylabel=$y$,
                        xlabel style={anchor = south east, inner sep = 4pt},
                        ylabel style={anchor = north west, inner sep = 4pt},
                        grid=major,
                        grid style={thin,densely dotted,black!20}
                        %tick label style = {font=\\large}
                }}
                
                \\begin{document}\n
                \\begin{tikzpicture}\n
                \\begin{axis}[
                    unit vector ratio*=1 1 1,
                    standardaxis2,
                    scale only axis,]\n
                """
                + self.axisText() +
                """
                \n
                \\end{axis}\n
                \\end{tikzpicture}\n
                \\end{document}
                
                """
            )
        os.system("pdflatex picture.tex")


if __name__ == "__main__":
    with open("input.csv") as inputFile:
        df = pd.read_csv(inputFile)
        sp = [float(p) for p in df.loc[0,"startpoint"].strip("()").split(",")]
        ep = [float(p) for p in df.loc[0,"endpoint"].strip("()").split(",")]
        domaine = [sp[0], ep[0]]
        racines = [float(p) for p in df.loc[0,"racines"].split(" ")]
        extrema = [sp] + [[float(p) for p in e.strip("()").split(",")]for e in df.loc[0,"extrema"].split(" ")] + [ep]
        f = FunctionInterpolationApproximator(racines, extrema, domaine)
        f.approximate()
        print(f.axisText())
        print(f.geogebraText())
        f.generateTikzPicture()
